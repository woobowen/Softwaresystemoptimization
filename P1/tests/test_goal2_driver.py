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
            measurement=dict(compile_timeout_s=60,timeout_s=1200,score_clock=target.kernel_clock,cpu_affinity=sorted(os.sched_getaffinity(0)),
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
                dict(process_wall_clock="RAW"),dict(kernel_clock="unknown"),
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
        ex.append(path,"task_start",attempt_id="1",task="x",clock_start_ns=dict(monotonic=0,raw=0,realtime=0))
        with self.assertRaises(ValueError): ex.usage(path)
        ex.append(path,"task_end",attempt_id="1",task="x",n4096_calls=1,resource_s=2.0,resource_wall_s=2.0,
            driver_wall_s=2.0,clock_elapsed_s=dict(monotonic=2.0,raw=2.0,realtime=2.0),
            clock_end_ns=dict(monotonic=2000000000,raw=2000000000,realtime=2000000000))
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

    def clock_row(self,q=1.0,trial=0):
        row=copy.deepcopy(next(r for r in self.rows["random"] if r["type"]=="measurement"))
        row.update(trial_id=trial,pid=1000+trial,process_wall_s=40.0,
            clock_start_ns=dict(CLOCK_MONOTONIC=1,CLOCK_MONOTONIC_RAW=2,CLOCK_REALTIME=3),
            clock_end_ns=dict(CLOCK_MONOTONIC=40000000001,CLOCK_MONOTONIC_RAW=2+round(40e9*q),CLOCK_REALTIME=40000000003),
            clock_deltas_s=dict(CLOCK_MONOTONIC=40.0,CLOCK_MONOTONIC_RAW=40*q,CLOCK_REALTIME=40.0))
        start=dict(type="measurement_start",run_id=row["run_id"],trial_id=trial,repeat=row["repeat"],pid=row["pid"])
        return start,row

    def test_complete_clock_check_rejects_nan_zero_and_wrong_unit(self):
        for value in (0,float("nan"),float("inf")):
            with self.assertRaises(ValueError):
                ex.complete_clock_check("driver","fixture",dict(monotonic=40,raw=value,realtime=40),[])
        _,row=self.clock_row(); row["clock_unit"]="us"
        with self.assertRaises(ValueError): ex.process_clock_span(row)

    def raw_history(self, previous, journals=()):
        marker=self.directory/"legacy-binding-fixture.json"
        marker.write_text('{"synthetic": true}\n')
        metadata=self.rows["random"][0]["metadata"]
        target=metadata["target"]
        identity=dict(framework_sha256=metadata["framework_sha256"],
            source_sha256=target["source_sha256"],n=target["n"],kernel_clock=target["kernel_clock"],
            compiler=target["compiler"],flags=target["flags"],runtime_affinity=metadata["runtime_affinity"])
        entries=[]
        for path in journals:
            header=ex.read_records(path)[0]
            entries.append(dict(path=str(path.relative_to(P1)),sha256=ex.sha256(path),
                metadata_fingerprint=header["fingerprint"]))
        path=self.directory/"raw-history-fixture.json"
        path.write_text(json.dumps(dict(schema=1,use="clock_baselines_only",
            ledger_prefix=dict(rows=len(previous),fingerprint=ex.at.fingerprint(previous)),
            legacy_journals=entries,legacy_numeric_binding=dict(path=str(marker.relative_to(P1)),sha256=ex.sha256(marker)),
            legacy_diagnostic_identity_files=[],new_target_identities=[identity])))
        return dict(path=str(path.relative_to(P1)),sha256=ex.sha256(path))

    def test_raw_guard_keeps_physical_first_and_ignores_failed_previous(self):
        path=self.directory/"raw-history-journal-fixture.jsonl"
        start,row=self.clock_row()
        path.write_text(''.join(json.dumps(r)+'\n' for r in [self.rows['random'][0],start,row]))
        previous=[]
        for name,q,failed in (("first",1.0,False),("failed",1.5,True),("previous",1.005,False)):
            previous.append(dict(type="task_start",attempt_id=name,task=name,boot_id="same",
                journal=str(path.relative_to(P1)),prior_measurement_starts=0,
                clock_start_ns=dict(monotonic=0,raw=0,realtime=0)))
            spans=dict(monotonic=40.0,raw=round(40e9*q)/1e9,realtime=40.0)
            previous.append(dict(type="task_end",attempt_id=name,task=name,n4096_calls=1,n4096_calls_known=True,
                returncode=0,reason="clock conflict" if failed else None,clock_conflict=failed,
                driver_wall_s=40.0,clock_elapsed_s=spans,resource_s=max(spans.values()),resource_wall_s=max(spans.values()),
                clock_end_ns={k:round(v*1e9) for k,v in spans.items()}))
        binding=self.raw_history(previous,[path])
        guard=ex.CompleteClockGuard(previous,"same",path,0,mode=ex.RAW_GUARD,history=binding)
        self.assertEqual([r["identity"] for r in guard.driver_baselines],["first","previous"])
        new_start,new=self.clock_row(1.09,1)
        new["clock_end_ns"]["CLOCK_REALTIME"]=3+round(40e9*1.09)
        new["clock_deltas_s"]["CLOCK_REALTIME"]=43.6
        result=guard.finish([self.rows['random'][0],new_start,new],"new",dict(monotonic=40,raw=43.6,realtime=43.6),1)
        self.assertFalse(result["clock_conflict"])
        self.assertEqual(result['clock_guard']['schema'],2)
        self.assertEqual(result['clock_guard']['history'],binding)
        self.assertEqual(result['clock_guard']['driver_check']['q'],1)
        refs=result['clock_guard']['driver_check']['baselines']
        self.assertEqual([r['identity'] for r in refs],["first","previous"])

    def test_raw_guard_does_not_lose_realtime_conflict(self):
        path=self.directory/"raw-rt-fixture.jsonl"
        binding=self.raw_history([])
        guard=ex.CompleteClockGuard([],"same",path,0,mode=ex.RAW_GUARD,history=binding)
        start,row=self.clock_row();start2,row2=self.clock_row(1.03,1)
        result=guard.finish([self.rows['random'][0],start,row,start2,row2],"fixture",dict(monotonic=80,raw=80,realtime=80),2)
        self.assertTrue(result['clock_conflict'])
        self.assertTrue(result['clock_guard']['process_checks'][1]['conflict'])
        self.assertFalse(result['clock_guard']['driver_check']['conflict'])

    def test_raw_clock_history_rejects_changed_prefix_raw_and_identity(self):
        path=self.directory/"raw-scope-fixture.jsonl"
        path.write_text(json.dumps(self.rows['random'][0])+'\n')
        prefix=[dict(type="synthetic",n=1)]
        binding=self.raw_history(prefix,[path])
        with self.assertRaises(ValueError): ex.load_clock_history(binding,[dict(type="synthetic",n=2)])
        path.write_text(path.read_text()+"{}\n")
        with self.assertRaises(ValueError): ex.load_clock_history(binding,prefix)
        binding=self.raw_history([])
        history=ex.load_clock_history(binding,[])
        changed=copy.deepcopy(self.rows['random'][0])
        changed['metadata']['target']['source_sha256']='different-source'
        changed['fingerprint']=ex.at.fingerprint(changed['metadata'])
        with self.assertRaises(ValueError): ex.check_clock_header([changed],history)
        with self.assertRaises(ValueError): ex.CompleteClockGuard([],"same",path,0,mode="unreviewed",history=binding)

    def test_raw_history_cannot_accept_new_unguarded_direct_matrix(self):
        binding=self.raw_history([])
        previous=[dict(type='task_start',attempt_id='direct',task='direct',boot_id='same',journal=None,
            clock_start_ns=dict(monotonic=0,raw=0,realtime=0)),
            dict(type='task_end',attempt_id='direct',task='direct',returncode=0,reason=None,n4096_calls=1,
            n4096_calls_known=True,clock_conflict=False,driver_wall_s=40,
            clock_elapsed_s=dict(monotonic=40,raw=40,realtime=40),resource_s=40,resource_wall_s=40,
            clock_end_ns=dict(monotonic=40000000000,raw=40000000000,realtime=40000000000))]
        with self.assertRaisesRegex(ValueError,'completed RAW guard'):
            ex.CompleteClockGuard(previous,'same',self.directory/'direct-fixture.jsonl',0,mode=ex.RAW_GUARD,history=binding)

    def test_new_raw_baseline_requires_a_literal_known_count(self):
        binding=self.raw_history([])
        previous=[dict(type='task_start',attempt_id='unknown',task='unknown',boot_id='same',journal=None),
            dict(type='task_end',attempt_id='unknown',task='unknown',returncode=0,reason=None,n4096_calls=1)]
        for value in (None,False,1,'true'):
            with self.subTest(value=value):
                if value is None:
                    previous[-1].pop('n4096_calls_known',None)
                else:
                    previous[-1]['n4096_calls_known']=value
                with self.assertRaisesRegex(ValueError,'explicit known call count'):
                    ex.CompleteClockGuard(previous,'same',self.directory/'unknown.jsonl',0,mode=ex.RAW_GUARD,history=binding)

    def test_same_domain_raw_upper_bound_survives_shorter_monotonic(self):
        rows,metadata,job=self.trace()
        clock=metadata['target']['kernel_clock']
        self.assertEqual(clock,'CLOCK_MONOTONIC_RAW')
        row=next(r for r in rows if r['type']=='measurement')
        row['clock_end_ns']['CLOCK_MONOTONIC']=row['clock_start_ns']['CLOCK_MONOTONIC']+1
        row['clock_deltas_s']['CLOCK_MONOTONIC']=1e-9
        row['process_wall_s']=1e-9
        ex.validate_trace(rows,metadata,job)
        delta=row['clock_deltas_s']['CLOCK_MONOTONIC_RAW']
        row['kernel_s']=float(f"{delta+.006:.9f}")
        row['stdout']=f"{row['kernel_s']:.9f}\nchecksum={row['checksum']:.17g}\n"
        with self.assertRaisesRegex(ValueError,'same-domain'): ex.validate_trace(rows,metadata,job)

    def test_complete_processes_are_checked_individually_before_driver_average(self):
        path=self.directory/"guard-journal-fixture.jsonl"
        guard=ex.CompleteClockGuard([],"fixture-boot",path,0)
        start1,row1=self.clock_row(); start2,row2=self.clock_row(1.03,1)
        result=guard.finish([start1,row1,start2,row2],"fixture",dict(monotonic=80,raw=80,realtime=80),2)
        self.assertTrue(result["clock_conflict"])
        self.assertTrue(result["clock_guard"]["process_checks"][1]["conflict"])
        self.assertFalse(result["clock_guard"]["driver_check"]["conflict"])

    def test_failed_attempt_cannot_be_a_formal_clock_baseline(self):
        path=self.directory/"baseline-fixture.jsonl"
        start,row=self.clock_row(1.2)
        path.write_text(json.dumps(start)+'\n'+json.dumps(row)+'\n')
        previous=[dict(type="task_start",attempt_id="failed",boot_id="same",journal=str(path.relative_to(P1)),prior_measurement_starts=0),
            dict(type="task_end",attempt_id="failed",n4096_calls=1,n4096_calls_known=True,returncode=1,reason="failed",
                 driver_wall_s=40,clock_elapsed_s=dict(monotonic=40,raw=48,realtime=40))]
        guard=ex.CompleteClockGuard(previous,"same",path,0)
        self.assertEqual(guard.process_baselines,[])
        self.assertEqual(guard.driver_baselines,[])

    def test_unfinished_call_and_missing_fields_are_not_healthy(self):
        path=self.directory/"unfinished-clock-fixture.jsonl"
        start,row=self.clock_row()
        for rows in ([start],[start,{k:v for k,v in row.items() if k!="clock_end_ns"}]):
            guard=ex.CompleteClockGuard([],"boot",path,0)
            result=guard.finish(rows,"fixture",dict(monotonic=40,raw=40,realtime=40),1)
            self.assertFalse(result["clock_guard"]["complete"])
            self.assertIsNotNone(result["clock_guard"]["error"])

    def test_partial_live_json_is_not_a_finished_clock_sample(self):
        path=self.directory/"live-clock-fixture.jsonl"
        start,row=self.clock_row()
        path.write_text(json.dumps(start)+'\n'+json.dumps(row)[:30])
        guard=ex.CompleteClockGuard([],"boot",path,0)
        self.assertTrue(guard.poll("fixture"))
        self.assertEqual(guard.checks,[])
        path.write_text(json.dumps(start)+'\n'+json.dumps(row)+'\n')
        self.assertTrue(guard.poll("fixture"))
        self.assertEqual(len(guard.checks),1)

    def test_real_small_guard_records_all_calls_and_complete_driver(self):
        job=dict(id="guarded-small",action="search",role="fixture",algorithm="random",budget=8,repeats=1,seed=7)
        path=self.directory/(job["id"]+".jsonl")
        ledger=self.directory/"guarded-small-ledger.jsonl"
        record=ex.controlled(ex.command(job,self.directory,self.protocol,self.protocol_path),self.directory,
            job["id"],job["role"],call_upper=8,journal=path,ledger=ledger,complete_clock_guard=True,time_limit=60)
        self.assertEqual(record["n4096_calls"],8)  # This private fixture ledger counts small processes only.
        self.assertFalse(record["clock_conflict"])
        self.assertTrue(record["clock_guard"]["complete"])
        self.assertEqual(len(record["clock_guard"]["process_checks"]),8)
        self.assertEqual(record["clock_guard"]["driver_check"]["identity"],record["attempt_id"])
        rows=ex.read_records(path); resources=ex.read_records(ledger)
        self.assertTrue(ex.validate_complete_clock_record(record,resources,rows,path))
        for field in ("process_checks","driver_check","threshold_fraction","boot_id"):
            changed=copy.deepcopy(record); changed["clock_guard"].pop(field)
            altered=copy.deepcopy(resources); altered[-1]=changed
            with self.assertRaises(ValueError): ex.validate_complete_clock_record(changed,altered,rows,path)
        changed=copy.deepcopy(record);changed["clock_guard"]["process_checks"][0]["q"]+=.1
        altered=copy.deepcopy(resources);altered[-1]=changed
        with self.assertRaises(ValueError): ex.validate_complete_clock_record(changed,altered,rows,path)

    def test_formal_summary_cannot_hide_a_clock_conflict_or_missing_attempt(self):
        protocol=copy.deepcopy(self.protocol)
        protocol["measurement"]["clock_health"]={"guard":"completed_per_target_process_and_driver_first_and_previous_same_boot"}
        job=dict(id="random",action="search",role="fixture",algorithm="random",budget=8,repeats=1,seed=7)
        with self.assertRaises(ValueError): ex.validate_task(job,self.directory,protocol)
        directory=self.directory/"summary-clock-fixture"; directory.mkdir(exist_ok=True)
        (directory/"random.jsonl").write_text((self.directory/"random.jsonl").read_text())
        record=dict(type="task_end",task="random",n4096_calls=8,returncode=0,reason=None,clock_conflict=True,
            clock_guard=dict(schema=1,mode="complete_target_and_driver",complete=True,error=None))
        (directory/"driver.jsonl").write_text(json.dumps(record)+'\n')
        with self.assertRaises(ValueError): ex.validate_task(job,directory,protocol)

    def test_saved_raw_seconds_and_resource_charge_cannot_be_tampered(self):
        start=dict(type="task_start",task="fixture",attempt_id="fixture",clock_start_ns=dict(monotonic=0,raw=0,realtime=0))
        end=dict(type="task_end",task="fixture",attempt_id="fixture",n4096_calls=1,resource_s=40,resource_wall_s=40,
            driver_wall_s=40,clock_elapsed_s=dict(monotonic=40,raw=40,realtime=40),
            clock_end_ns=dict(monotonic=40000000000,raw=40000000000,realtime=40000000000))
        path=self.directory/"boundary-cost-fixture.jsonl"
        for field in ("saved_raw","resource"):
            altered=copy.deepcopy(end)
            if field=="saved_raw": altered["clock_elapsed_s"]["raw"]=39
            else: altered["resource_s"]=1
            path.write_text(json.dumps(start)+'\n'+json.dumps(altered)+'\n')
            with self.assertRaises(ValueError): ex.usage(path)

    def test_completed_baseline_requires_unique_complete_target_rows(self):
        start,row=self.clock_row()
        for rows in ([start],[start,row,row],[start,start,row]):
            with self.assertRaises(ValueError): ex.attempt_measurements(rows,0,1,complete=True)

    def test_resource_calls_cannot_be_reduced_below_physical_starts(self):
        journal=self.directory/"physical-starts-fixture.jsonl"
        a,_=self.clock_row(trial=0); b,_=self.clock_row(trial=1)
        journal.write_text(json.dumps(a)+'\n'+json.dumps(b)+'\n')
        start=dict(type="task_start",task="fixture",attempt_id="fixture",journal=str(journal.relative_to(P1)),
            clock_start_ns=dict(monotonic=0,raw=0,realtime=0))
        end=dict(type="task_end",task="fixture",attempt_id="fixture",n4096_calls=1,resource_s=40,resource_wall_s=40,
            driver_wall_s=40,clock_elapsed_s=dict(monotonic=40,raw=40,realtime=40),
            clock_end_ns=dict(monotonic=40000000000,raw=40000000000,realtime=40000000000))
        path=self.directory/"physical-count-ledger.jsonl"
        path.write_text(json.dumps(start)+'\n'+json.dumps(end)+'\n')
        with self.assertRaises(ValueError): ex.usage(path)

    def test_formal_plan_identity_fields_cannot_be_changed(self):
        protocol=ex.load_json(P1/"evidence/protocol_v2.json")
        protocol['target']['sha256']=ex.sha256(P1/'src/matrix_multiplication.c')
        protocol['framework']['sha256']=ex.sha256(P1/'src/autotuner.py')
        protocol['measurement'].update(score_clock='CLOCK_MONOTONIC_RAW',cost_clock='CLOCK_MONOTONIC_RAW')
        protocol['measurement']['clock_health'].update(guard_mode=ex.RAW_GUARD,guard_schema=2,
            raw_realtime_ratio_change_fraction=.02)
        source=self.directory/'current-plan-fixture.json'
        source.write_text(json.dumps(protocol))
        protocol.update(protocol_sha256=ex.sha256(source),protocol_path=str(source.relative_to(P1)),measurement_root=str(P1))
        manifest=ex.plan(protocol,"reference")
        ex.freeze_check(protocol,manifest,source)
        for key in ("schema","protocol","target_sha256","framework_sha256"):
            altered=copy.deepcopy(manifest)
            altered[key]=0 if key=="schema" else "wrong-identity"
            with self.assertRaises(ValueError): ex.freeze_check(protocol,altered,source)
        protocol['measurement'].update(score_clock='CLOCK_MONOTONIC',cost_clock='CLOCK_MONOTONIC')
        protocol['measurement']['clock_health'].update(guard_mode='complete_target_and_driver',guard_schema=1,
            raw_monotonic_ratio_change_fraction=.02)
        source.write_text(json.dumps(protocol))
        protocol['protocol_sha256']=ex.sha256(source)
        with self.assertRaisesRegex(ValueError,'target timer boundaries'):
            ex.freeze_check(protocol,ex.plan(protocol,'reference'),source)


if __name__=="__main__": unittest.main()
