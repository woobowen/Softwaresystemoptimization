#!/usr/bin/env python3
"""Capture a real local xterm using a private X authority and no TCP listener."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import signal
import shutil
import struct
import subprocess
import tempfile
import time

from experiment_v2 import P1, append, clocks, elapsed, performance_lock, stop


def authority(path, display):
    # Xauthority counted strings: family, address, display, mechanism, cookie.
    fields=(b"",str(display).encode(),b"MIT-MAGIC-COOKIE-1",secrets.token_bytes(16))
    data=struct.pack(">H",65535)+b"".join(struct.pack(">H",len(x))+x for x in fields)
    descriptor=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(descriptor,"wb") as out:
        out.write(data)


def tcp_listeners(display):
    result=subprocess.run(["ss","-ltnH"],capture_output=True,text=True,check=True,timeout=5)
    return [line for line in result.stdout.splitlines() if re.search(rf":{6000+display}\s",line)]


def unix_listeners(display):
    result=subprocess.run(["ss","-lxH"],capture_output=True,text=True,check=True,timeout=5)
    return [line for line in result.stdout.splitlines()
        if re.search(rf"@?/tmp/\.X11-unix/X{display}(?:\s|$)",line)]


def active(pid):
    if pid is None:
        return False
    try:
        return Path(f"/proc/{pid}/stat").read_text().split(")",1)[1].split()[0]!="Z"
    except FileNotFoundError:
        return False


def clean_shell(pidfile, wrapper, terminal):
    if not pidfile.exists():
        return None
    pid=int(pidfile.read_text().strip())
    try:
        command=[x.decode() for x in Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0") if x]
        if not command:  # Already exited or zombie.
            return pid
        group=os.getpgid(pid)
        if Path(command[0]).name!="bash" or command[1]!=str(wrapper) or group not in (pid,terminal.pid):
            raise ValueError("recorded terminal shell identity changed; refuse unrelated process cleanup")
        os.killpg(group,signal.SIGTERM)
        for _ in range(100):
            try:
                state=Path(f"/proc/{pid}/stat").read_text().split(")",1)[1].split()[0]
            except FileNotFoundError:
                break
            if state=="Z":
                break
            time.sleep(.05)
        else:
            os.killpg(group,signal.SIGKILL)
            for _ in range(20):
                if not active(pid):
                    break
                time.sleep(.05)
            else:
                raise ValueError("owned shell remained active after SIGKILL")
        return pid
    except (FileNotFoundError,ProcessLookupError):
        return pid


def capture(script, output, evidence, title, timeout=1200):
    script=Path(script).resolve(strict=True)
    output=Path(output).resolve()
    output.relative_to(P1)
    if output.exists():
        raise ValueError("capture output exists; inspect it before deliberately replacing a final image")
    xterm=shutil.which("xterm")
    if xterm is None:
        local=P1/".cache/screenshot-tools/root/usr/bin/xterm"
        xterm=str(local) if local.is_file() else None
    if xterm is None or not all(shutil.which(x) for x in ("Xvfb","xdpyinfo","ffmpeg","ss")):
        raise ValueError("required local screenshot tools are missing")
    output.parent.mkdir(parents=True,exist_ok=True)
    begin=clocks()
    processes=[]
    failure=None
    record=dict(command_file_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),
        command_text=script.read_text(),image=str(output.relative_to(P1)),
        actual_terminal=True,transport="local Unix socket",authorization="private MIT-MAGIC-COOKIE-1",
        cookie_recorded=False,clock_start_ns=begin,started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()))
    with performance_lock(), tempfile.TemporaryDirectory(prefix="screenshot-",dir=P1/".cache") as temporary:
        directory=Path(temporary)
        os.chmod(directory,0o700)
        display=next((d for d in secrets.SystemRandom().sample(range(200,600),400)
            if not Path(f"/tmp/.X11-unix/X{d}").exists() and not Path(f"/tmp/.X{d}-lock").exists()
            and not tcp_listeners(d) and not unix_listeners(d)),None)
        if display is None:
            raise ValueError("no unused local display found")
        record["display"]=display
        auth=directory/"authority"
        authority(auth,display)
        environment=dict(os.environ,DISPLAY=f":{display}",XAUTHORITY=str(auth))
        server_command=["Xvfb",f":{display}","-screen","0","1500x940x24","-nolisten","tcp","-auth",str(auth),"-pn"]
        record["server_command"]=server_command
        pidfile=directory/"shell.pid"
        wrapper=directory/"terminal.sh"
        wrapper.write_text('''set -eu
printf '%s\\n' "$$" > "$3"
if bash "$1"; then code=0; else code=$?; fi
printf '\\n(exit status %s)\\n' "$code"
printf %s "$code" > "$2"
exit "$code"
''')
        terminal=None
        try:
            with (directory/"server.log").open("w") as log:
                server=subprocess.Popen(server_command,stdout=log,stderr=log,start_new_session=True)
                processes.append(server)
                for _ in range(100):
                    probe=subprocess.run(["xdpyinfo"],env=environment,capture_output=True,text=True,timeout=5)
                    if probe.returncode==0:
                        break
                    if server.poll() is not None:
                        raise ValueError("Xvfb failed: "+(directory/"server.log").read_text())
                    time.sleep(.1)
                else:
                    raise ValueError("private display did not become ready")
                if tcp_listeners(display):
                    raise ValueError("owned display unexpectedly opened TCP")
                record["unix_listeners_during"]=unix_listeners(display)
                if not record["unix_listeners_during"]:
                    raise ValueError("ready display has no identifiable local Unix listener")
                empty=directory/"empty-authority"
                empty.touch(mode=0o600)
                unauthenticated=subprocess.run(["xdpyinfo"],env=dict(environment,XAUTHORITY=str(empty)),
                    capture_output=True,text=True,timeout=5)
                record["empty_authority_returncode"]=unauthenticated.returncode
                if unauthenticated.returncode==0:
                    raise ValueError("private display accepted an empty authority")
                done=directory/"done"
                terminal_command=[xterm,"-hold","-fa","DejaVu Sans Mono","-fs","12",
                    "-geometry","140x42+10+10","-bg","#111827","-fg","#e5e7eb",
                    "-title",title,"-e","bash",str(wrapper),str(script),str(done),str(pidfile)]
                record["terminal_command"]=terminal_command
                with (directory/"terminal.log").open("w") as terminal_log:
                    terminal=subprocess.Popen(terminal_command,env=environment,cwd=P1,
                        stdout=terminal_log,stderr=terminal_log,start_new_session=True)
                    processes.append(terminal)
                    deadline=time.monotonic()+timeout
                    while not done.exists():
                        if terminal.poll() is not None or time.monotonic()>deadline:
                            raise ValueError("terminal command did not finish: "+(directory/"terminal.log").read_text())
                        time.sleep(.1)
                    record["command_returncode"]=int(done.read_text())
                    if record["command_returncode"]!=0:
                        raise ValueError("real screenshot command failed")
                    # Allow the final terminal redraw, separately recorded from target work.
                    time.sleep(.3)
                    recorder=["ffmpeg","-hide_banner","-loglevel","error","-f","x11grab",
                        "-video_size","1500x940","-i",f":{display}","-frames:v","1",
                        "-threads","1",str(output)]
                    subprocess.run(recorder,env=environment,capture_output=True,text=True,check=True,timeout=30)
                    record["capture_command"]=recorder
                    record["image_sha256"]=hashlib.sha256(output.read_bytes()).hexdigest()
        except BaseException as error:
            record["error"]=type(error).__name__+": "+str(error)
            failure=error
        finally:
            cleanup_errors=[]
            if terminal is not None:
                try:
                    record["shell_pid"]=clean_shell(pidfile,wrapper,terminal)
                except BaseException as error:
                    cleanup_errors.append("shell: "+str(error))
            for process in reversed(processes):
                try:
                    stop(process)
                except BaseException as error:
                    cleanup_errors.append("process: "+str(error))
            record["owned_pids"]=[p.pid for p in processes]
            record["shell_stopped"]=not active(record.get("shell_pid"))
            record["owned_processes_stopped"]=all(p.poll() is not None for p in processes) and record["shell_stopped"]
            record["cleanup_errors"]=cleanup_errors
    # TemporaryDirectory has now actually removed the private authorization file.
    record["authorization_removed_on_exit"]=not auth.exists() and not directory.exists()
    record["display_socket_removed"]=not Path(f"/tmp/.X11-unix/X{display}").exists()
    record["display_lock_removed"]=not Path(f"/tmp/.X{display}-lock").exists()
    try:
        record["tcp_listeners_after"]=tcp_listeners(display)
        record["unix_listeners_after"]=unix_listeners(display)
    except Exception as error:
        record["tcp_listeners_after"]=None
        record["unix_listeners_after"]=None
        record["cleanup_errors"].append("listeners unknown: "+str(error))
    record["clock_end_ns"]=clocks()
    try:
        record["elapsed_s"]=elapsed(begin,record["clock_end_ns"])
    except ValueError as error:
        record["elapsed_s"]=None
        record["cleanup_errors"].append(str(error))
    append(evidence,"capture",**record)
    if failure is not None:
        raise failure
    if record["cleanup_errors"] or record["tcp_listeners_after"] or record["unix_listeners_after"] or not all(record[x] for x in
            ("owned_processes_stopped","authorization_removed_on_exit","display_socket_removed","display_lock_removed")):
        raise ValueError("owned screenshot cleanup did not complete; inspect capture evidence")
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command-file",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--title",default="P1 terminal")
    parser.add_argument("--evidence",type=Path,default=P1/"evidence/commands/screenshots_goal2.jsonl")
    args=parser.parse_args()
    result=capture(args.command_file,args.output,args.evidence,args.title)
    print(json.dumps(dict(image=result["image"],sha256=result["image_sha256"],
        stopped=result["owned_processes_stopped"],tcp_listeners=result["tcp_listeners_after"])))


if __name__=="__main__":
    def interrupt(signum,frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,interrupt)
    main()
