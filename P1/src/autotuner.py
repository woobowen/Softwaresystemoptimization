#!/usr/bin/env python3
"""A small, serial C-program autotuner with append-only experiment records."""

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import time
import uuid


BLOCKS = (8, 16, 24, 64, 128)
OPTS = ("O0", "O1", "O2", "O3")
COMMON_FLAGS = ("-std=c11", "-Wall", "-Wextra")


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def fingerprint(value):
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             allow_nan=False).encode())


@dataclass(frozen=True)
class Config:
    s: int
    opt: str

    @property
    def key(self):
        return f"s{self.s}-{self.opt}"


class ConfigSpace:
    def __init__(self, blocks=BLOCKS, opts=OPTS):
        self.blocks, self.opts = tuple(blocks), tuple(opts)
        if not self.blocks or any(type(s) is not int or s <= 0 for s in self.blocks):
            raise ValueError("blocks must be positive integers")
        if not self.opts or any(opt not in OPTS for opt in self.opts):
            raise ValueError("opts must be drawn from O0, O1, O2, O3")
        if len(set(self.blocks)) != len(self.blocks) or len(set(self.opts)) != len(self.opts):
            raise ValueError("duplicate configuration values")
        self.configs = tuple(Config(s, opt) for s in self.blocks for opt in self.opts)

    def check(self, config):
        if config not in self.configs:
            raise ValueError(f"configuration outside space: {config}")

    def neighbors(self, config):
        self.check(config)
        s_index, opt_index = self.blocks.index(config.s), self.opts.index(config.opt)
        nearby_blocks = self.blocks[max(0, s_index - 1):s_index + 2]
        nearby_opts = self.opts[max(0, opt_index - 1):opt_index + 2]
        return [c for c in self.configs if c != config and
                ((c.opt == config.opt and c.s in nearby_blocks) or
                 (c.s == config.s and c.opt in nearby_opts))]


def process(command, timeout, on_start=None):
    """Record a real subprocess; terminate its whole group on timeout/interrupt."""
    result = dict(command=list(map(str, command)), started_at=now(), spawned=False,
                  stdout="", stderr="", returncode=None, status="ok", error=None)
    start = time.monotonic()
    child = None
    try:
        child = subprocess.Popen(result["command"], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True, encoding="utf-8",
                                 errors="replace", start_new_session=True)
        result["spawned"] = True
        result["pid"] = child.pid
        if on_start:
            on_start({k: result[k] for k in ("command", "started_at", "pid", "spawned")})
        result["stdout"], result["stderr"] = child.communicate(timeout=timeout)
        if child.returncode:
            result.update(status="nonzero", error=f"exit status {child.returncode}")
    except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
        result.update(status="timeout" if isinstance(exc, subprocess.TimeoutExpired)
                      else "interrupted", error=str(exc) or "KeyboardInterrupt")
        if child:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            result["stdout"], result["stderr"] = child.communicate()
    except OSError as exc:
        if child:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.communicate()
            raise
        result.update(status="os_error", error=str(exc))
    finally:
        if child:
            result["returncode"] = child.returncode
        result.update(ended_at=now(), process_wall_s=time.monotonic() - start)
    return result


class TargetProgram:
    def __init__(self, source, compiler="gcc", flags=COMMON_FLAGS, cache_dir=None,
                 compile_timeout=60):
        self.source = Path(source).resolve(strict=True)
        self.source_sha256 = digest(self.source.read_bytes())
        path = shutil.which(str(compiler))
        if not path:
            raise ValueError(f"compiler not found: {compiler}")
        self.compiler = str(Path(path).resolve())
        self.flags = tuple(flags)
        if not math.isfinite(compile_timeout) or compile_timeout <= 0:
            raise ValueError("compile timeout must be positive and finite")
        self.compile_timeout = compile_timeout
        probe = process([self.compiler, "--version"], compile_timeout)
        if probe["status"] != "ok":
            raise ValueError(f"compiler version probe failed: {probe['status']}")
        self.compiler_info = dict(path=self.compiler, version=probe["stdout"].strip(),
                                  sha256=digest(Path(self.compiler).read_bytes()), probe=probe)
        self.cache_dir = Path(cache_dir or Path(__file__).resolve().parents[1] / ".cache" / "build").resolve()
        source_text = self.source.read_text()
        self.require_checksum = bool(re.search(r'printf\s*\(\s*"checksum=', source_text))
        match = re.search(r"^\s*#\s*define\s+n\s+(\d+)\b", source_text, re.M)
        self.n = int(match[1]) if match else None

    def metadata(self):
        # Probe timing is provenance, not part of a reproducibility fingerprint.
        return dict(source=str(self.source), source_sha256=self.source_sha256, n=self.n,
                    compiler={k: v for k, v in self.compiler_info.items() if k != "probe"},
                    flags=list(self.flags), compile_timeout=self.compile_timeout,
                    require_checksum=self.require_checksum)

    def build(self, opt, emit=None):
        if opt not in OPTS:
            raise ValueError("invalid optimization level")
        if digest(self.source.read_bytes()) != self.source_sha256:
            raise ValueError("target source changed during experiment")
        flags = [*self.flags, "-" + opt]
        identity = dict(self.metadata(), flags=flags)
        key = fingerprint(identity)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        binary, manifest = self.cache_dir / key, self.cache_dir / (key + ".json")
        result = dict(build_key=key, opt=opt, binary=str(binary), flags=flags,
                      source_sha256=self.source_sha256, compiler=identity["compiler"])
        cached = None
        if manifest.is_file() and binary.is_file():
            try:
                saved = json.loads(manifest.read_text())
                if saved["identity"] == identity and saved["binary_sha256"] == digest(binary.read_bytes()):
                    cached = saved["result"]
            except (ValueError, KeyError, OSError):
                pass
        if cached is not None:
            result.update(cached, cached=True, compile_wall_s=0)
            if emit:
                emit("build", result)
            return result
        fd, temporary = tempfile.mkstemp(prefix="compile-", dir=self.cache_dir)
        os.close(fd)
        command = [self.compiler, *flags, str(self.source), "-o", temporary]
        try:
            compile_result = process(command, self.compile_timeout,
                                     lambda record: emit("build_start", dict(result, **record)) if emit else None)
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise
        result.update(cached=False, compile=compile_result, status=compile_result["status"],
                      compile_wall_s=compile_result["process_wall_s"], binary_sha256=None)
        try:
            if result["status"] == "ok":
                os.replace(temporary, binary)
                result["binary_sha256"] = digest(binary.read_bytes())
                data = dict(identity=identity, binary_sha256=result["binary_sha256"], result=result)
                temporary_manifest = self.cache_dir / (key + ".tmp")
                temporary_manifest.write_text(json.dumps(data, allow_nan=False))
                os.replace(temporary_manifest, manifest)
        finally:
            Path(temporary).unlink(missing_ok=True)
        if emit:
            emit("build", result)
        return result

    @staticmethod
    def parse(stdout):
        lines = stdout.splitlines()
        if not lines:
            raise ValueError("missing elapsed-time output")
        try:
            value = float(lines[0].strip())
        except ValueError as exc:
            raise ValueError("first output line is not a float") from exc
        if not math.isfinite(value) or value <= 0:
            raise ValueError("elapsed time must be positive and finite")
        TargetProgram.checksum(stdout)
        return value

    @staticmethod
    def checksum(stdout):
        lines = [line.strip() for line in stdout.splitlines()[1:]
                 if line.strip().startswith("checksum")]
        if not lines:
            return None
        if len(lines) != 1 or not lines[0].startswith("checksum="):
            raise ValueError("invalid or duplicate checksum output")
        try:
            value = float(lines[0].split("=", 1)[1])
        except ValueError as exc:
            raise ValueError("invalid checksum output") from exc
        if not math.isfinite(value):
            raise ValueError("checksum must be finite")
        return value

    def measure(self, build, config, timeout, on_start=None):
        binary = Path(build["binary"])
        if digest(binary.read_bytes()) != build["binary_sha256"]:
            raise ValueError("cached binary changed before measurement")
        result = process([str(binary), str(config.s)], timeout, on_start)
        result.update(kernel_s=None, checksum=None, build_key=build["build_key"],
                      binary_sha256=build["binary_sha256"])
        if result["status"] == "ok":
            try:
                result["kernel_s"] = self.parse(result["stdout"])
                result["checksum"] = self.checksum(result["stdout"])
                if self.require_checksum and result["checksum"] is None:
                    raise ValueError("missing checksum output for this target")
            except ValueError as exc:
                result.update(status="parse_error", error=str(exc), kernel_s=None)
        return result


class SearchStrategy:
    """Propose configurations using only this search's observed feedback."""
    def __init__(self, name, space, seed=0):
        if name not in ("grid", "random", "greedy"):
            raise ValueError("unknown search algorithm")
        self.name, self.space, self.scores = name, space, {}
        self.order = list(space.configs)
        rng = random.Random(seed)
        if name == "random":
            rng.shuffle(self.order)
        self.current = rng.choice(space.configs) if name == "greedy" else None

    def suggest(self):
        if self.name != "greedy":
            return next((c for c in self.order if c not in self.scores), None)
        if self.current not in self.scores:
            return self.current
        while True:
            neighbors = self.space.neighbors(self.current)
            pending = [c for c in neighbors if c not in self.scores]
            if pending:
                return pending[0]
            score = lambda c: self.scores[c] if self.scores[c] is not None else math.inf
            winner = min([self.current, *neighbors], key=score)
            if score(winner) >= score(self.current):
                return None
            self.current = winner

    def observe(self, config, score):
        if config != self.suggest():
            raise ValueError("feedback does not match next proposed configuration")
        if score is not None and (not math.isfinite(score) or score <= 0):
            raise ValueError("invalid feedback score")
        self.scores[config] = score


class Journal:
    def __init__(self, path, metadata, resume=False, probe=None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.records = []
        expected = fingerprint(metadata)
        fragment = None
        if resume:
            data = self.path.read_bytes()
            offset = 0
            for line in data.splitlines(keepends=True):
                try:
                    self.records.append(json.loads(line))
                except ValueError:
                    if offset + len(line) != len(data) or line.endswith(b"\n"):
                        raise ValueError("corrupt journal record")
                    fragment = line.decode("utf-8", errors="replace")
                    break
                offset += len(line)
            if not self.records or self.records[0].get("fingerprint") != expected:
                raise ValueError("resume fingerprint mismatch")
            self.run_id = self.records[0]["run_id"]
            self.file = self.path.open("r+", encoding="utf-8")
            self.file.seek(offset)
            if fragment is not None:
                self.file.truncate()
            elif data and not data.endswith(b"\n"):
                self.file.write("\n")
        else:
            self.file = self.path.open("x", encoding="utf-8")
            self.run_id = uuid.uuid4().hex
            self.append("header", metadata=metadata, fingerprint=expected, compiler_probe=probe)
        if fragment is not None:
            self.append("journal_recovery", discarded_fragment=fragment)

    def append(self, kind, **fields):
        record = dict(type=kind, run_id=self.run_id, at=now(), **fields)
        line = json.dumps(record, ensure_ascii=False, allow_nan=False)
        self.file.write(line + "\n")
        self.file.flush()
        os.fsync(self.file.fileno())
        self.records.append(record)
        return record

    def close(self):
        self.file.close()


def unfinished_builds(records):
    return [start for i, start in enumerate(records) if start["type"] == "build_start" and
            not any(r["type"] == "build" and not r["cached"] and
                    r.get("build_key") == start.get("build_key") and
                    r["compile"].get("pid") == start.get("pid") for r in records[i + 1:])]


class Evaluator:
    def __init__(self, target, space, journal, repeats=1, timeout=1800):
        if type(repeats) is not int or repeats < 1:
            raise ValueError("repeats must be a positive integer")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be positive and finite")
        self.target, self.space, self.journal = target, space, journal
        self.repeats, self.timeout = repeats, timeout
        self.session_started = None

    def evaluate(self, config, trial_id):
        self.space.check(config)
        records = [r for r in self.journal.records if r.get("trial_id") == trial_id]
        completed = next((r for r in records if r["type"] == "trial"), None)
        if completed:
            if completed["config"] != asdict(config):
                raise ValueError("completed trial configuration mismatch")
            return completed
        trial_started = time.monotonic()
        if not records:
            self.journal.append("trial_start", trial_id=trial_id, config=asdict(config), started_at=now())
        elif records[0]["config"] != asdict(config):
            raise ValueError("resume trial configuration mismatch")
        emit = lambda kind, data: self.journal.append(kind, trial_id=trial_id, config=asdict(config), **data)
        measurements = [r for r in records if r["type"] == "measurement"]
        for start in (r for r in records if r["type"] == "measurement_start"):
            if not any(r["repeat"] == start["repeat"] for r in measurements):
                self.ensure_stopped(start)
                recovered = emit("measurement", dict(repeat=start["repeat"], status="interrupted",
                    command=start["command"], started_at=start["started_at"], ended_at=None,
                    process_wall_s=None, spawned=True, stdout="", stderr="", returncode=None,
                    error="process completion was not recorded", kernel_s=None))
                measurements.append(recovered)
        interrupted_build = bool(unfinished_builds(records))
        if interrupted_build:
            for pending in unfinished_builds(records):
                self.ensure_stopped(pending)
        build = next((r for r in reversed(records) if r["type"] == "build"), None)
        if not interrupted_build and not any(r["status"] != "ok" for r in measurements) and \
                (build is None or build["status"] == "ok"):
            build = self.target.build(config.opt, emit)
            if build["status"] == "interrupted":
                raise KeyboardInterrupt
            if build["status"] == "ok":
                for repeat in range(len(measurements), self.repeats):
                    result = self.target.measure(build, config, self.timeout,
                        lambda data: emit("measurement_start", dict(repeat=repeat, **data)))
                    measurements.append(emit("measurement", dict(repeat=repeat, **result)))
                    if result["status"] == "interrupted":
                        raise KeyboardInterrupt
                    if result["status"] != "ok":
                        break
        samples = [r["kernel_s"] for r in measurements if r["status"] == "ok"]
        valid = not interrupted_build and build is not None and build["status"] == "ok" and \
            len(measurements) == self.repeats and len(samples) == self.repeats
        score = statistics.median(samples) if valid else None
        previous = [r for r in self.journal.records if r["type"] == "trial" and r["score"] is not None]
        candidates = [dict(config=r["config"], score=r["score"]) for r in previous]
        if valid:
            candidates.append(dict(config=asdict(config), score=score))
        best = min(candidates, key=lambda r: r["score"]) if candidates else None
        wall = time.monotonic() - trial_started
        prior_wall = sum((r.get("compile_wall_s") or 0) for r in records if r["type"] == "build") + sum(
            (r.get("process_wall_s") or 0) for r in records if r["type"] == "measurement")
        cost = dict(started_at=records[0]["at"] if records else next(
            r["started_at"] for r in self.journal.records if r["type"] == "trial_start" and r["trial_id"] == trial_id),
            ended_at=now(), trial_wall_s=None if records else wall,
            trial_wall_recorded_s=prior_wall + wall, resumed=bool(records))
        if self.session_started is not None:
            elapsed = sum(r["wall_s"] for r in self.journal.records if r["type"] == "session_end") + \
                time.monotonic() - self.session_started
            unknown = sum(r["type"] == "session_start" for r in self.journal.records) - sum(
                r["type"] == "session_end" for r in self.journal.records) > 1
            cost.update(tuning_elapsed_s=None if unknown else elapsed, tuning_elapsed_recorded_s=elapsed)
        return emit("trial", dict(score=score, samples=samples, status="ok" if valid else "failed",
                                  best_so_far=best, **cost))

    @staticmethod
    def ensure_stopped(start):
        pid = start.get("pid")
        if pid is not None:
            try:
                os.killpg(pid, 0)
            except ProcessLookupError:
                return
            raise ValueError(f"unrecorded process group {pid} is still present; "
                             "wait for it to finish before resuming (PID is not killed automatically)")


def search(strategy, evaluator, budget, session_started=None):
    if type(budget) is not int or budget < 0:
        raise ValueError("budget must be a nonnegative integer")
    journal = evaluator.journal
    final = next((r for r in journal.records if r["type"] == "summary"), None)
    if final:
        return final
    trials = [r for r in journal.records if r["type"] == "trial"]
    for trial in trials:
        strategy.observe(Config(**trial["config"]), trial["score"])
    session_started = session_started or dict(monotonic=time.monotonic(), at=now())
    start = session_started["monotonic"]
    evaluator.session_started = start
    journal.append("session_start", started_at=session_started["at"])
    try:
        for trial_id in range(len(trials), budget):
            config = strategy.suggest()
            if config is None:
                break
            trial = evaluator.evaluate(config, trial_id)
            strategy.observe(config, trial["score"])
    finally:
        journal.append("session_end", ended_at=now(), wall_s=time.monotonic() - start)
    trials = [r for r in journal.records if r["type"] == "trial"]
    measurements = [r for r in journal.records if r["type"] == "measurement"]
    builds = [r for r in journal.records if r["type"] == "build"]
    compile_processes = sum(r["type"] == "build_start" for r in journal.records)
    incomplete_builds = len(unfinished_builds(journal.records))
    incomplete_sessions = sum(r["type"] == "session_start" for r in journal.records) - sum(
        r["type"] == "session_end" for r in journal.records)
    compile_wall = sum(r["compile_wall_s"] for r in builds)
    tuning_wall = sum(r["wall_s"] for r in journal.records if r["type"] == "session_end")
    return journal.append("summary", best=trials[-1]["best_so_far"] if trials else None,
        proposals=len([r for r in journal.records if r["type"] == "trial_start"]),
        attempted_trials=len(trials), completed_configs=sum(r["status"] == "ok" for r in trials),
        distinct_configs=len({Config(**r["config"]).key for r in trials}),
        process_runs=sum(r.get("spawned", False) for r in measurements),
        failed_trials=sum(r["status"] != "ok" for r in trials),
        failed_runs=sum(r["status"] != "ok" for r in measurements),
        interrupted_runs=sum(r["status"] == "interrupted" for r in measurements),
        compile_processes=compile_processes, incomplete_builds=incomplete_builds,
        failed_builds=sum(r["status"] != "ok" for r in builds),
        compile_wall_s=None if incomplete_builds else compile_wall,
        compile_wall_recorded_s=compile_wall,
        cached_builds=sum(r["cached"] for r in builds),
        incomplete_sessions=incomplete_sessions, tuning_wall_s=None if incomplete_sessions else tuning_wall,
        tuning_wall_recorded_s=tuning_wall)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("list", "build", "run", "search"))
    parser.add_argument("--target", type=Path, default=Path(__file__).with_name("matrix_multiplication.c"))
    parser.add_argument("--blocks", default=",".join(map(str, BLOCKS)))
    parser.add_argument("--opts", default=",".join(OPTS))
    parser.add_argument("--compiler", default="gcc")
    parser.add_argument("--cflag", action="append", default=[])
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--compile-timeout", type=float, default=60)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--protocol", type=Path)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--s", type=int)
    parser.add_argument("--opt", choices=OPTS)
    parser.add_argument("--algorithm", choices=("grid", "random", "greedy"), default="grid")
    parser.add_argument("--budget", type=int, default=20)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=1800)
    args = parser.parse_args(argv)
    journal = None
    session_started = dict(monotonic=time.monotonic(), at=now())
    def interrupt(signum, frame):
        raise KeyboardInterrupt
    previous_handler = signal.signal(signal.SIGTERM, interrupt)
    try:
        space = ConfigSpace(tuple(int(s) for s in args.blocks.split(",")), args.opts.split(","))
        if args.budget < 0 or args.repeats < 1 or not math.isfinite(args.timeout) or args.timeout <= 0:
            raise ValueError("budget >= 0, repeats >= 1, and finite timeout > 0 required")
        if args.resume and args.output is None:
            raise ValueError("--resume requires --output")
        if args.action == "list":
            print(json.dumps([asdict(c) for c in space.configs]))
            return 0
        if args.action == "run":
            if args.s is None or args.opt is None:
                raise ValueError("run requires --s and --opt")
            space.check(Config(args.s, args.opt))
            space = ConfigSpace((args.s,), (args.opt,))
        target = TargetProgram(args.target, args.compiler, (*COMMON_FLAGS, *args.cflag),
                               args.cache_dir, args.compile_timeout)
        metadata = dict(schema=1, framework_sha256=digest(Path(__file__).read_bytes()),
            target=target.metadata(), blocks=list(space.blocks), opts=list(space.opts),
            action=args.action, algorithm=args.algorithm if args.action == "search" else "grid",
            seed=args.seed, budget=args.budget if args.action == "search" else 1,
            repeats=args.repeats, timeout=args.timeout,
            protocol_sha256=digest(args.protocol.read_bytes()) if args.protocol else None,
            cache_dir=str(target.cache_dir))
        output = args.output or Path(__file__).resolve().parents[1] / "results" / (args.action + "-" + uuid.uuid4().hex + ".jsonl")
        journal = Journal(output, metadata, args.resume, target.compiler_info["probe"])
        if args.action == "build":
            for pending in unfinished_builds(journal.records):
                Evaluator.ensure_stopped(pending)
            existing = [r for r in journal.records if r["type"] == "build"]
            done = {r["opt"] for r in existing}
            for opt in space.opts:
                if opt not in done:
                    built = target.build(opt, lambda kind, data: journal.append(kind, **data))
                    if built["status"] == "interrupted":
                        raise KeyboardInterrupt
            result = dict(output=str(output), builds=[r for r in journal.records if r["type"] == "build"])
            cost = sum(r["compile_wall_s"] for r in result["builds"])
            incomplete = len(unfinished_builds(journal.records))
            result.update(incomplete_builds=incomplete, compile_wall_s=None if incomplete else cost,
                          compile_wall_recorded_s=cost)
            code = int(any(r["status"] != "ok" for r in result["builds"]))
        else:
            strategy = SearchStrategy(metadata["algorithm"], space, args.seed)
            result = search(strategy, Evaluator(target, space, journal, args.repeats, args.timeout),
                            metadata["budget"], session_started)
            result = dict(result, output=str(output))
            code = int(result["failed_trials"] > 0)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return code
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    except KeyboardInterrupt:
        print("interrupted; completed records saved", file=sys.stderr)
        return 130
    finally:
        if journal:
            journal.close()
        signal.signal(signal.SIGTERM, previous_handler)


if __name__ == "__main__":
    raise SystemExit(main())
