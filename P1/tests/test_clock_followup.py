"""Synthetic clock fixtures only; never performance results."""

import copy
from contextlib import redirect_stdout
import io
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

P1=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P1/"scripts"))
import experiment_v2 as ex
import clock_followup as cf


class ClockFollowupTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix="clock-fixtures-",dir=P1/".cache")
        self.directory=Path(self.temporary.name)
        self.job=dict(id="fixture",action="run")
        self.protocol=dict(state="approved",purpose="one_finite_clock_relation_followup",
            measurement=dict(formal_admission=False),diagnostic_jobs=[self.job]+[dict(id=str(i)) for i in range(11)])
        self.timex=lambda:dict(readonly=True,offset_raw=0,frequency_scaled_ppm=0,tick_us=10000)
        self.previous=dict(driver=[1.0],formal_target_process=[1.0],diagnostic_kernel=[1.0])

    def tearDown(self):
        self.temporary.cleanup()

    def observer(self):
        return cf.Observer(copy.deepcopy(self.protocol),copy.deepcopy(self.job),["fixture-command"],
            self.directory/"clock.jsonl",self.timex,self.previous)

    def test_scope_rejects_formal_other_job_command_calls_and_existing_trace(self):
        observer=self.observer()
        observer.validate("fixture",["fixture-command"],1,self.directory/"formal.jsonl")
        for task,command,count,journal in (("wrong",["fixture-command"],1,"x"),
            ("fixture",["wrong"],1,"x"),("fixture",["fixture-command"],8,"x"),
            ("fixture",["fixture-command"],1,None)):
            with self.assertRaises(ValueError): observer.validate(task,command,count,journal)
        observer.protocol["measurement"]["formal_admission"]=True
        with self.assertRaises(ValueError): observer.validate("fixture",["fixture-command"],1,"x")
        observer.protocol["measurement"]["formal_admission"]=False
        observer.trace.write_text("synthetic existing trace\n")
        with self.assertRaises(ValueError): observer.validate("fixture",["fixture-command"],1,"x")

    def test_short_prefix_conflict_does_not_become_complete_conflict(self):
        observer=self.observer()
        observer.sample("start",dict(monotonic=0,raw=0,realtime=0),[1])
        observer.sample("interval",dict(monotonic=10_000_000_000,raw=9_700_000_000,realtime=10_000_000_000),[1])
        rows=[dict(type="measurement",status="ok",spawned=True,clock_deltas_s={
            "CLOCK_MONOTONIC":50,"CLOCK_MONOTONIC_RAW":50,"CLOCK_REALTIME":50}),dict(type="summary")]
        result=observer.finish(dict(monotonic=50_000_000_000,raw=50_000_000_000,realtime=50_000_000_000),rows,None,0,[1])
        self.assertTrue(result["prefix_clock_conflict"])
        self.assertFalse(result["complete_clock_conflict"])
        self.assertEqual([r["source"] for r in result["clock_complete_checks"]],["driver","formal_target_process"])
        samples=ex.read_records(observer.trace)
        self.assertEqual(samples[1]["local_ratio"],.97)
        self.assertTrue(all(type(x) is int for row in samples if row["type"]=="clock_sample" for x in row["clock_ns"].values()))

    def test_complete_target_conflict_is_visible_even_with_summary(self):
        observer=self.observer(); observer.sample("start",dict(monotonic=0,raw=0,realtime=0),[1])
        rows=[dict(type="measurement",status="ok",spawned=True,clock_deltas_s={
            "CLOCK_MONOTONIC":50,"CLOCK_MONOTONIC_RAW":52,"CLOCK_REALTIME":50}),dict(type="summary")]
        result=observer.finish(dict(monotonic=50_000_000_000,raw=50_000_000_000,realtime=50_000_000_000),rows,None,0,[1])
        self.assertTrue(result["complete_clock_conflict"])
        self.assertTrue(result["clock_conflict"])

    def test_nonpositive_nan_and_two_percent_boundary(self):
        # Binary floating rounding is governed by the same strict >.02 expression everywhere.
        self.assertEqual(cf.ratio_check("fixture",dict(monotonic=100,raw=102,realtime=100),[1])["conflict"],abs(1.02-1)>.02)
        for value in (0,-1,math.nan,math.inf):
            with self.assertRaises(ValueError): cf.ratio_check("fixture",dict(monotonic=100,raw=value,realtime=100),[1])

    def test_clock_backwards_and_incomplete_summary_hard_fail(self):
        observer=self.observer(); observer.sample("start",dict(monotonic=10,raw=10,realtime=10),[])
        with self.assertRaises(ValueError): observer.sample("interval",dict(monotonic=9,raw=20,realtime=20),[])
        with self.assertRaises(ValueError): observer.finish(dict(monotonic=20,raw=20,realtime=20),[],None,0,[])

    def test_failed_interrupted_unknown_and_other_boot_excluded_from_baseline(self):
        boot=Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        rows=[]
        for key,code,reason,known,current in (("valid",0,None,True,boot),
                ("failed",1,None,True,boot),("interrupted",130,"interrupted",True,boot),
                ("unknown",0,None,False,boot),("other",0,None,True,"other")):
            rows.append(dict(type="task_start",attempt_id=key,boot_id=current,role="fixture",journal=None))
            rows.append(dict(type="task_end",attempt_id=key,returncode=code,reason=reason,n4096_calls_known=known,
                n4096_calls=1,driver_wall_s=40,clock_elapsed_s=dict(monotonic=40,raw=40,realtime=40)))
        path=self.directory/"ledger.jsonl"; path.write_text("".join(json.dumps(r)+"\n" for r in rows))
        self.assertEqual(ex.matrix_clock_baselines(rows,boot),[1])
        self.assertEqual(cf.complete_sources(path)["driver"],[1])

    def test_matrix_raw_ns_recomputed_and_cpu_not_wall_reference(self):
        path=self.directory/"matrix.stdout.txt"
        row=dict(clock_order=["MONOTONIC","RAW","REALTIME","PROCESS_CPU"],
            start_ns=[0]*4,end_ns=[50_000_000_000,50_500_000_000,50_000_000_000,49_000_000_000],
            elapsed_s=[50,50.5,50,49])
        path.write_text("50.000000\nchecksum=17180040496.458935\n"+json.dumps(row)+"\n")
        self.assertEqual(cf.matrix_interval(path),dict(monotonic=50,raw=50.5,realtime=50))
        row["elapsed_s"][1]=math.nan
        path.write_text("50.000000\nchecksum=17180040496.458935\n"+json.dumps(row)+"\n")
        with self.assertRaises(ValueError): cf.matrix_interval(path)
        row["elapsed_s"]=[]
        path.write_text("50.000000\nchecksum=17180040496.458935\n"+json.dumps(row)+"\n")
        with self.assertRaises(ValueError): cf.matrix_interval(path)

    def test_observer_cannot_disable_task_timeout_or_known_cost_record(self):
        ledger=self.directory/"timeout-ledger.jsonl"
        command=[sys.executable,"-c","import time; time.sleep(3)"]
        class FixtureObserver:
            def validate(self,*args): pass
            def sample(self,*args): pass
            def finish(self,*args): return dict(clock_diagnostic_only=True)
        with self.assertRaises(ValueError):
            ex.controlled(command,self.directory,"timeout","fixture",ledger=ledger,
                time_limit=.1,diagnostic_observer=FixtureObserver())
        end=ex.read_records(ledger)[-1]
        self.assertEqual(end["reason"],"resource_or_task_timeout")
        self.assertEqual(end["n4096_calls"],0)
        self.assertGreater(end["resource_s"],.1)
        self.assertEqual(ex.usage(ledger)[0],0)

    def test_query_is_readonly_and_cap_is_checked_before_spawn(self):
        self.assertIn("struct timex value = {0}",cf.QUERY)
        with mock.patch.object(ex,"usage",return_value=(520,0)):
            with self.assertRaises(ValueError):
                ex.controlled(["never-spawn"],self.directory,"cap","fixture",call_upper=1)

    def test_query_identity_cannot_authorize_another_source_or_clock_change(self):
        for identity in (dict(readonly_modes=1),dict(readonly_modes=0,source_sha256="another source")):
            with self.assertRaises(ValueError): cf.query_reader(self.directory,identity)

    def test_cli_check_supplies_runtime_protocol_path_to_real_freeze_check(self):
        prototype=ex.load_json(P1/"evidence/protocol_clock_followup.json")
        prototype["approval"]["followup_executor_sha256"]=ex.sha256(cf.__file__)
        path=self.directory/"protocol-fixture.json"
        path.write_text(json.dumps(prototype))
        runtime=dict(prototype,protocol_sha256=ex.sha256(path),protocol_path=str(path.relative_to(P1)),measurement_root=str(P1))
        (self.directory/"plan.json").write_text(json.dumps(ex.plan(runtime,"diagnostic")))
        original_lock=ex.performance_lock
        output=io.StringIO()
        with mock.patch.object(sys,"argv",[cf.__file__,"check","--protocol",str(path),"--directory",str(self.directory)]), \
                mock.patch.object(ex,"performance_lock",side_effect=lambda:original_lock(self.directory/"fixture-lock")), \
                mock.patch.object(cf.cd,"check_identity"),mock.patch.object(cf,"query_reader",return_value=self.timex), \
                redirect_stdout(output):
            # Only the cache availability checks are isolated; the parser and freeze_check are real.
            cf.main()
        row=json.loads(output.getvalue())
        self.assertEqual(row["state"],"checked")
        self.assertEqual(row["jobs"],12)
        self.assertEqual(row["n4096_calls"],0)
        self.assertEqual(row["protocol_sha256"],ex.sha256(path))

    def test_multi_attempt_baselines_select_only_that_attempts_processes(self):
        boot=Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        journal=self.directory/"recovery.jsonl"
        data=[]
        for number,(tid,ratio) in enumerate((("first",1.0),("second",1.01),("future",1.3)),1):
            fields=dict(run_id="same-run",trial_id=tid,repeat=0,pid=100+number)
            data.extend([dict(type="measurement_start",**fields),dict(type="measurement",**fields,
                status="ok",spawned=True,clock_deltas_s=dict(CLOCK_MONOTONIC=50,CLOCK_MONOTONIC_RAW=50*ratio))])
        journal.write_text("".join(json.dumps(r)+"\n" for r in data))
        rows=[]
        for attempt,offset in (("a",0),("b",1)):
            rows.extend([dict(type="task_start",attempt_id=attempt,boot_id=boot,role="fixture",
                journal=str(journal.relative_to(P1)),prior_measurement_starts=offset),
                dict(type="task_end",attempt_id=attempt,returncode=0,reason=None,n4096_calls_known=True,
                    n4096_calls=1,driver_wall_s=50,clock_elapsed_s=dict(monotonic=50,raw=50,realtime=50))])
        path=self.directory/"attempt-ledger.jsonl"; path.write_text("".join(json.dumps(r)+"\n" for r in rows))
        self.assertEqual(cf.complete_sources(path)["formal_target_process"],[1.0,1.01])

    def test_completed_resume_checks_command_cost_reason_and_raw_trace(self):
        observer=self.observer(); before=dict(monotonic=0,raw=0,realtime=0)
        observer.previous=dict(driver=[],formal_target_process=[],diagnostic_kernel=[])
        after=dict(monotonic=50_000_000_000,raw=50_000_000_000,realtime=50_000_000_000)
        observer.sample("start",before,[])
        values=dict(CLOCK_MONOTONIC=50,CLOCK_MONOTONIC_RAW=50,CLOCK_REALTIME=50)
        fields=observer.finish(after,[dict(type="measurement",status="ok",spawned=True,
            clock_deltas_s=values),dict(type="summary")],None,0,[])
        observer.trace.rename(self.directory/"fixture.clocks.jsonl")
        fields["clock_trace"]=str((self.directory/"fixture.clocks.jsonl").relative_to(P1))
        (self.directory/"fixture.jsonl").write_text(json.dumps(dict(type="measurement",status="ok",spawned=True,
            clock_deltas_s=values))+"\n")
        start=dict(type="task_start",attempt_id="fixture",command=["fixture-command"],
            role="fixture",call_upper=1,prior_measurement_starts=0,
            journal=str((self.directory/"fixture.jsonl").relative_to(P1)),clock_start_ns=before,
            boot_id=Path("/proc/sys/kernel/random/boot_id").read_text().strip())
        end=dict(type="task_end",attempt_id="fixture",task="fixture",returncode=0,reason=None,
            n4096_calls=1,n4096_calls_known=True,driver_wall_s=50,resource_s=50,resource_wall_s=50,
            clock_elapsed_s=dict(monotonic=50,raw=50,realtime=50),clock_end_ns=after,**fields)
        job=dict(id="fixture",action="run",role="fixture")
        with mock.patch.object(ex,"read_records",side_effect=lambda p:[start] if p==ex.LEDGER else
                [json.loads(line) for line in Path(p).read_text().splitlines()]), \
                mock.patch.object(ex,"command",return_value=["fixture-command","--resume"]), \
                mock.patch.object(ex,"validate_task",return_value="complete"):
            cf.completed_job(job,self.directory,self.protocol,Path("fixture-protocol"),end)
            for field,value in (("reason","resource_or_task_timeout"),("resource_s",0),("resource_wall_s",0),("returncode",1)):
                changed=dict(end,**{field:value})
                with self.assertRaises(ValueError): cf.completed_job(job,self.directory,self.protocol,Path("fixture-protocol"),changed)
            start["command"]=["tampered"]
            with self.assertRaises(ValueError): cf.completed_job(job,self.directory,self.protocol,Path("fixture-protocol"),end)
            start["command"]=["fixture-command"]
            rows=[json.loads(line) for line in (self.directory/"fixture.clocks.jsonl").read_text().splitlines()]
            pristine=copy.deepcopy(rows)
            for field,value in (("phase","fake"),("adjtimex",dict(readonly=True,frequency_scaled_ppm=987))):
                mutated=copy.deepcopy(pristine); mutated[0][field]=value
                (self.directory/"fixture.clocks.jsonl").write_text("".join(json.dumps(r)+"\n" for r in mutated))
                with self.assertRaises(ValueError): cf.completed_job(job,self.directory,self.protocol,Path("fixture-protocol"),end)
            (self.directory/"fixture.clocks.jsonl").write_text("".join(json.dumps(r)+"\n" for r in pristine))
            tampered=copy.deepcopy(end)
            tampered["clock_complete_checks"][0]["ratio"]=1.3
            rows[-1]["clock_complete_checks"]=tampered["clock_complete_checks"]
            (self.directory/"fixture.clocks.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
            tampered["clock_trace_sha256"]=ex.sha256(self.directory/"fixture.clocks.jsonl")
            with self.assertRaises(ValueError): cf.completed_job(job,self.directory,self.protocol,Path("fixture-protocol"),tampered)
            rows[0]["clock_ns"]["raw"]=1
            (self.directory/"fixture.clocks.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
            with self.assertRaises(ValueError): cf.completed_job(job,self.directory,self.protocol,Path("fixture-protocol"),end)


if __name__=="__main__": unittest.main()
