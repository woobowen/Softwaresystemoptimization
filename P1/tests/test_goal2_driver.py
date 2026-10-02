"""Small real searches and corrupted-journal counterexamples; no formal samples."""

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

P1=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P1/"scripts"))
import experiment_v2 as ex
import clock_diagnostics as cd


class Goal2DriverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (P1/".cache").mkdir(exist_ok=True)
        cls.temporary=tempfile.TemporaryDirectory(prefix="goal2-fixtures-",dir=P1/".cache")
        cls.directory=Path(cls.temporary.name)
        source=cls.directory/"small.c"
        source.write_text((P1/"src/matrix_multiplication.c").read_text().replace("#define n 4096","#define n 128"))
        target=ex.at.TargetProgram(source,cache_dir=cls.directory/"build",compile_timeout=60.0)
        cls.protocol=dict(framework=dict(path="src/autotuner.py",sha256=ex.sha256(P1/"src/autotuner.py")),
            target=dict(path=str(source.relative_to(P1)),sha256=ex.sha256(source),n=128,
                compiler="gcc",compiler_identity=target.metadata()["compiler"],common_flags=list(ex.at.COMMON_FLAGS)),
            space=dict(blocks=list(ex.at.BLOCKS),opts=list(ex.at.OPTS)),
            measurement=dict(compile_timeout_s=60,timeout_s=1200,cpu_affinity=sorted(os.sched_getaffinity(0)),
                cache_dir=str((cls.directory/"build").relative_to(P1))))
        cls.protocol_path=cls.directory/"protocol.json"
        cls.protocol_path.write_text(json.dumps(cls.protocol))
        cls.protocol.update(protocol_sha256=ex.sha256(cls.protocol_path),measurement_root=str(P1))
        cls.rows={}
        for name in ("random","recheck"):
            job=dict(id=name,action="search",role="fixture",algorithm=name,budget=8,repeats=1,seed=7)
            command=ex.command(job,cls.directory,cls.protocol,cls.protocol_path)
            result=subprocess.run(command,capture_output=True,text=True,timeout=60)
            if result.returncode:
                raise RuntimeError(result.stderr)
            cls.rows[name]=ex.read_records(cls.directory/(name+".jsonl"))

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def trace(self,name="random"):
        rows=copy.deepcopy(self.rows[name])
        return rows,rows[0]["metadata"],dict(id=name,action="search",role="fixture",algorithm=name,budget=8,repeats=1,seed=7)

    def test_real_small_base_and_recheck_traces(self):
        for name in self.rows:
            rows,metadata,job=self.trace(name)
            ex.validate_trace(rows,metadata,job)
            self.assertEqual(ex.validate_task(job,self.directory,self.protocol),"complete")
        self.assertEqual(self.rows["recheck"][-1]["process_runs"],8)
        self.assertEqual(self.rows["recheck"][-1]["distinct_configs"],6)

    def test_summary_best_cannot_be_backfilled_from_confirmation(self):
        rows,metadata,job=self.trace()
        rows[-1]["best"]["score"]=0.000001
        with self.assertRaises(ValueError): ex.validate_trace(rows,metadata,job)

    def test_wrong_trial_score_and_proposal_fail(self):
        for field in ("score","config"):
            rows,metadata,job=self.trace()
            trial=next(r for r in rows if r["type"]=="trial")
            trial[field]=0.000001 if field=="score" else dict(s=128,opt="O3")
            with self.assertRaises(ValueError): ex.validate_trace(rows,metadata,job)

    def test_duplicate_measurement_and_run_identity_fail(self):
        rows,metadata,job=self.trace()
        index=next(i for i,r in enumerate(rows) if r["type"]=="measurement")
        rows.insert(index,copy.deepcopy(rows[index]))
        with self.assertRaises(ValueError): ex.validate_trace(rows,metadata,job)
        rows,metadata,job=self.trace(); rows[index]["run_id"]="other"
        with self.assertRaises(ValueError): ex.validate_trace(rows,metadata,job)

    def test_raw_output_checksum_and_clock_units_fail(self):
        for change in (dict(stdout="nan\nchecksum=1\n"),dict(checksum=1),dict(clock_unit="us"),
                dict(process_wall_clock="RAW"),dict(kernel_clock="CLOCK_MONOTONIC_RAW"),
                dict(kernel_unit="ms"),dict(clock_read_order=["CLOCK_REALTIME"]),dict(boundary_read_order={})):
            rows,metadata,job=self.trace()
            next(r for r in rows if r["type"]=="measurement").update(change)
            with self.assertRaises(ValueError): ex.validate_trace(rows,metadata,job)

    def test_clock_boundaries_reject_extra_domain_and_noninteger_units(self):
        for boundary in ("clock_start_ns","clock_end_ns"):
            for change in ("extra","float"):
                rows,metadata,job=self.trace()
                row=next(r for r in rows if r["type"]=="measurement")
                if change=="extra": row[boundary]["CPU_TIME"]=1
                else: row[boundary]["CLOCK_MONOTONIC"]=float(row[boundary]["CLOCK_MONOTONIC"])
                with self.assertRaises(ValueError): ex.validate_trace(rows,metadata,job)

    def test_clock_deltas_and_same_domain_guard_fail(self):
        rows,metadata,job=self.trace()
        row=next(r for r in rows if r["type"]=="measurement")
        row["clock_deltas_s"]["CLOCK_MONOTONIC_RAW"]*=1.2
        with self.assertRaises(ValueError): ex.validate_trace(rows,metadata,job)
        rows,metadata,job=self.trace()
        row=next(r for r in rows if r["type"]=="measurement")
        row["process_wall_s"]=row["kernel_s"]-0.01
        with self.assertRaises(ValueError): ex.validate_trace(rows,metadata,job)

    def test_recheck_eligibility_and_fresh_recovery_cannot_change(self):
        for field,value in (("fresh_score",0.000001),("return_eligible",False),("config_samples",[0.000001])):
            rows,metadata,job=self.trace("recheck")
            row=next(r for r in rows if r["type"]=="trial" and r["phase"]=="recheck")
            row[field]=value
            with self.assertRaises(ValueError): ex.validate_trace(rows,metadata,job)

    def test_summary_counts_and_budget_are_recomputed(self):
        rows,metadata,job=self.trace()
        rows[-1]["process_runs"]-=1
        with self.assertRaises(ValueError): ex.validate_trace(rows,metadata,job)
        rows,metadata,job=self.trace(); metadata["budget"]=7
        with self.assertRaises(ValueError): ex.validate_trace(rows,metadata,job)

    def test_metadata_rehash_does_not_bypass_frozen_job(self):
        rows,metadata,job=self.trace()
        path=self.directory/"tampered.jsonl"
        metadata["seed"]=9; rows[0]["fingerprint"]=ex.at.fingerprint(metadata)
        path.write_text("".join(json.dumps(r)+"\n" for r in rows))
        job["id"]="tampered"
        with self.assertRaises(ValueError): ex.validate_task(job,self.directory,self.protocol)

    def test_historical_root_comes_from_frozen_manifest(self):
        rows,metadata,job=self.trace()
        oldroot=Path("/tmp/goal2-frozen-checkout")
        expected=ex.common_metadata(self.protocol,job,oldroot)
        self.assertEqual(expected["target"]["source"],str(oldroot/self.protocol["target"]["path"]))
        self.assertEqual(expected["framework_sha256"],metadata["framework_sha256"])

    def test_resource_ledger_cannot_forget_unknown_or_duplicate_attempt(self):
        path=self.directory/"resource-fixture.jsonl"
        ex.append(path,"task_start",attempt_id="1",task="x")
        with self.assertRaises(ValueError): ex.usage(path)
        ex.append(path,"task_end",attempt_id="1",task="x",n4096_calls=1,resource_s=2.0)
        self.assertEqual(ex.usage(path),(1,2.0))
        ex.append(path,"task_end",attempt_id="1",task="x",n4096_calls=1,resource_s=2.0)
        with self.assertRaises(ValueError): ex.usage(path)

    def test_owned_lock_rejects_a_second_runner(self):
        path=self.directory/"lock-fixture"
        with ex.performance_lock(path):
            with self.assertRaises(ValueError):
                with ex.performance_lock(path): pass

    def test_clock_probe_has_fixed_statement_order_and_identical_kernel(self):
        text=(P1/"src/matrix_multiplication.c").read_text()
        result=cd.diagnostic_source(text)
        self.assertEqual(cd.kernel(text),cd.kernel(result))
        for boundary in ("start","end"):
            positions=[result.index(f"{boundary}_ns[{i}]=") for i in range(4)]
            self.assertEqual(positions,sorted(positions))
        self.assertIn("clock_nanosleep(CLOCK_BOOTTIME",cd.PROBE)
        self.assertIn("struct timex tx={0}",cd.PROBE)

    def test_resource_clocks_do_not_cross_compare_kernel_or_go_backwards(self):
        begin=dict(monotonic=10,raw=10,realtime=10)
        self.assertEqual(ex.elapsed(begin,dict(monotonic=20,raw=25,realtime=20))["raw"],15e-9)
        with self.assertRaises(ValueError): ex.elapsed(begin,dict(monotonic=9,raw=25,realtime=20))

    def test_hard_exit_recovery_preserves_unknown_actual_cost(self):
        path=self.directory/"recovery-fixture.jsonl"
        inspection=self.directory/"inspection-fixture.txt"
        inspection.write_text("synthetic no-process fixture, not an experiment\n")
        start=ex.clocks()
        ex.append(path,"task_start",attempt_id="lost",task="fixture",role="fixture",journal=None,
            clock_start_ns=start,call_upper=1,prior_measurement_starts=0,
            boot_id=Path("/proc/sys/kernel/random/boot_id").read_text().strip())
        evidence=self.directory/"recovery-evidence.json"
        evidence.write_text(json.dumps(dict(attempt_id="lost",verified_no_live_processes=True,
            inspection=str(inspection.relative_to(P1)))))
        row=ex.recover_resource(evidence,path)
        self.assertIsNone(row["driver_wall_s"])
        self.assertEqual(row["n4096_calls"],1)
        self.assertGreaterEqual(row["resource_s"],0)
        self.assertEqual(ex.usage(path)[0],1)

    def test_direct_task_existing_output_is_preserved(self):
        directory=self.directory/"protected-output"
        directory.mkdir(exist_ok=True)
        path=directory/"fixture.stdout.txt"; path.write_text("existing fixture\n")
        ledger=self.directory/"protected-output-ledger.jsonl"
        with self.assertRaises(ValueError):
            ex.controlled([sys.executable,"-c","print(123)"],directory,"fixture","fixture",ledger=ledger)
        self.assertEqual(path.read_text(),"existing fixture\n")
        self.assertFalse(ledger.exists())

    def test_clock_guard_uses_only_same_boot_matrix_intervals(self):
        rows=[]
        for name,boot,calls in (("probe","current",0),("old","other",1),("matrix","current",1)):
            rows.append(dict(type="task_start",attempt_id=name,boot_id=boot))
            rows.append(dict(type="task_end",attempt_id=name,n4096_calls=calls,driver_wall_s=40,returncode=0,reason=None,
                clock_elapsed_s=dict(raw=44,monotonic=40,realtime=40)))
        self.assertEqual(ex.matrix_clock_baselines(rows,"current"),[1.1])

    def test_hard_exit_driver_cleans_its_recorded_separate_child(self):
        directory=self.directory/"hard-exit-fixture"
        directory.mkdir(exist_ok=True)
        journal=directory/"child.jsonl"
        code="""import json,os,subprocess,sys
command=[sys.executable,'-c','import time;time.sleep(30)']
child=subprocess.Popen(command,start_new_session=True)
with open(sys.argv[1],'w') as out:
 out.write(json.dumps(dict(type='measurement_start',pid=child.pid,command=command,spawned=True))+'\\n')
 out.flush();os.fsync(out.fileno())
os._exit(7)
"""
        ledger=directory/"resource-fixture.jsonl"
        with self.assertRaises(ValueError):
            ex.controlled([sys.executable,"-c",code,str(journal)],directory,"crash","fixture",
                call_upper=1,journal=journal,ledger=ledger,time_limit=3)
        pid=ex.read_records(journal)[0]["pid"]
        stat=Path(f"/proc/{pid}/stat")
        self.assertTrue(not stat.exists() or stat.read_text().split(")",1)[1].split()[0]=="Z")
        self.assertEqual(ex.usage(ledger)[0],1)


if __name__=="__main__": unittest.main()
