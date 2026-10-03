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
import resource
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
ALGORITHMS = ("grid", "random", "greedy", "stratified", "patience", "recheck")
RUN_MODES = ("correctness", "diagnostic", "benchmark")
PRIMARY_CLOCK = "CLOCK_MONOTONIC_RAW"


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def fingerprint(value):
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             allow_nan=False).encode())


def clock_readings_ns():
    """Read these time domains in the same fixed order at each boundary."""
    return {name: time.clock_gettime_ns(getattr(time, name)) for name in
            ("CLOCK_MONOTONIC", "CLOCK_MONOTONIC_RAW", "CLOCK_REALTIME")}


def raw_time_ns():
    return time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)


def build_identity(metadata, opt):
    """Runtime settings do not change a compiler's output."""
    if opt not in OPTS:
        raise ValueError("invalid optimization level")
    return dict(source=metadata["source"], source_sha256=metadata["source_sha256"],
                compiler=metadata["compiler"], flags=[*metadata["flags"], "-" + opt])


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
    clocks_start = clock_readings_ns()
    cpu_start = resource.getrusage(resource.RUSAGE_CHILDREN)
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
        cpu_end = resource.getrusage(resource.RUSAGE_CHILDREN)
        clocks_end = clock_readings_ns()
        deltas = {name: (clocks_end[name] - value) / 1e9 for name, value in clocks_start.items()}
        result.update(ended_at=now(), process_wall_s=deltas["CLOCK_MONOTONIC"],
            process_wall_clock="CLOCK_MONOTONIC", clock_unit="ns",
            process_raw_s=deltas[PRIMARY_CLOCK], process_raw_clock=PRIMARY_CLOCK,
            timing_status="ok" if deltas[PRIMARY_CLOCK] > 0 else "invalid",
            timing_error=None if deltas[PRIMARY_CLOCK] > 0 else "primary process clock did not advance",
            auxiliary_clock_anomalies=[name for name in ("CLOCK_MONOTONIC", "CLOCK_REALTIME")
                                       if deltas[name] <= 0],
            clock_read_order=list(clocks_start), clock_start_ns=clocks_start,
            clock_end_ns=clocks_end, clock_deltas_s=deltas,
            boundary_read_order=dict(start=[*clocks_start, "RUSAGE_CHILDREN"],
                                     end=["RUSAGE_CHILDREN", *clocks_end]),
            child_cpu_start_s=dict(user=cpu_start.ru_utime, system=cpu_start.ru_stime),
            child_cpu_end_s=dict(user=cpu_end.ru_utime, system=cpu_end.ru_stime),
            child_user_cpu_s=cpu_end.ru_utime - cpu_start.ru_utime,
            child_system_cpu_s=cpu_end.ru_stime - cpu_start.ru_stime)
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
        self.compile_timeout = float(compile_timeout)
        probe = process([self.compiler, "--version"], compile_timeout)
        if probe["status"] != "ok":
            raise ValueError(f"compiler version probe failed: {probe['status']}")
        self.compiler_info = dict(path=self.compiler, version=probe["stdout"].strip(),
                                  sha256=digest(Path(self.compiler).read_bytes()), probe=probe)
        self.cache_dir = Path(cache_dir or Path(__file__).resolve().parents[1] / ".cache" / "build").resolve()
        source_text = self.source.read_text()
        self.require_checksum = bool(re.search(r'printf\s*\(\s*"checksum=', source_text))
        self.require_kernel_boundaries = bool(re.search(r'printf\s*\(\s*"kernel_start_ns=', source_text))
        code = re.sub(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
                      " ", source_text, flags=re.S)
        clocks = set(re.findall(r"\bclock_gettime\s*\(\s*(CLOCK_[A-Z_]+)\s*,", code))
        self.kernel_clock = next(iter(clocks)) if len(clocks) == 1 and clocks <= {
            "CLOCK_MONOTONIC", "CLOCK_MONOTONIC_RAW"} else "unknown"
        match = re.search(r"^\s*#\s*define\s+n\s+(\d+)\b", source_text, re.M)
        self.n = int(match[1]) if match else None

    def metadata(self):
        # Probe timing is provenance, not part of a reproducibility fingerprint.
        return dict(source=str(self.source), source_sha256=self.source_sha256, n=self.n,
                    compiler={k: v for k, v in self.compiler_info.items() if k != "probe"},
                    flags=list(self.flags), compile_timeout=self.compile_timeout,
                    require_checksum=self.require_checksum, kernel_clock=self.kernel_clock,
                    require_kernel_boundaries=self.require_kernel_boundaries)

    def build(self, opt, emit=None):
        if opt not in OPTS:
            raise ValueError("invalid optimization level")
        if digest(self.source.read_bytes()) != self.source_sha256:
            raise ValueError("target source changed during experiment")
        flags = [*self.flags, "-" + opt]
        identity = build_identity(self.metadata(), opt)
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
            result.update(cached, cached=True, compile_wall_s=0, compile_raw_s=0)
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
                      compile_wall_s=compile_result["process_wall_s"],
                      compile_raw_s=compile_result.get("process_raw_s")
                          if compile_result.get("timing_status") == "ok" else None,
                      binary_sha256=None)
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
    def elapsed(stdout):
        lines = stdout.splitlines()
        if not lines:
            raise ValueError("missing elapsed-time output")
        try:
            value = float(lines[0].strip())
        except ValueError as exc:
            raise ValueError("first output line is not a float") from exc
        if not math.isfinite(value):
            raise ValueError("elapsed time must be finite")
        return value

    @staticmethod
    def parse(stdout):
        value = TargetProgram.elapsed(stdout)
        if value <= 0:
            raise ValueError("elapsed time must be positive")
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

    @staticmethod
    def kernel_boundaries(stdout):
        names = ("kernel_start_ns", "kernel_end_ns")
        lines = [line.strip() for line in stdout.splitlines()[1:]
                 if line.strip().startswith(names)]
        if not lines:
            return None
        values = {}
        for line in lines:
            match = re.fullmatch(r"(kernel_start_ns|kernel_end_ns)=(-?[0-9]+)", line)
            if not match or match[1] in values:
                raise ValueError("invalid or duplicate kernel nanosecond boundary")
            values[match[1]] = int(match[2])
        if set(values) != set(names):
            raise ValueError("missing kernel nanosecond boundary")
        return values

    def measure(self, build, config, timeout, on_start=None, *, mode="benchmark"):
        if mode not in RUN_MODES:
            raise ValueError("unknown run mode")
        binary = Path(build["binary"])
        if digest(binary.read_bytes()) != build["binary_sha256"]:
            raise ValueError("cached binary changed before measurement")
        result = process([str(binary), str(config.s)], timeout, on_start)
        result.update(kernel_s=None, kernel_clock=self.kernel_clock, kernel_unit="s",
                      checksum=None, build_key=build["build_key"],
                      binary_sha256=build["binary_sha256"], mode=mode,
                      output_status="not_checked", score_eligible=False,
                      kernel_start_ns=None, kernel_end_ns=None,
                      timing_source_established=self.kernel_clock != "unknown")
        if result["status"] == "ok":
            try:
                result["kernel_s"] = self.elapsed(result["stdout"])
                result["checksum"] = self.checksum(result["stdout"])
                boundaries = self.kernel_boundaries(result["stdout"])
                if self.require_checksum and result["checksum"] is None:
                    raise ValueError("missing checksum output for this target")
                if getattr(self, "require_kernel_boundaries", False) and boundaries is None:
                    raise ValueError("missing kernel nanosecond boundaries for this target")
                if boundaries is not None:
                    result.update(boundaries)
                result["output_status"] = "ok"
                if result["kernel_s"] <= 0:
                    result.update(timing_status="invalid", timing_error="kernel clock did not advance")
            except ValueError as exc:
                result.update(status="parse_error", error=str(exc), kernel_s=None,
                              output_status="error")
            if result["status"] == "ok" and self.kernel_clock != "unknown":
                wall = result.get("clock_deltas_s", {}).get(self.kernel_clock)
                if type(wall) not in (int, float) or not math.isfinite(wall) or wall <= 0:
                    result.update(timing_status="invalid", timing_error="missing or invalid same-domain process interval")
                elif result["kernel_s"] > wall + .005:
                    result.update(timing_status="invalid", timing_error="kernel elapsed exceeds same-domain process time + 0.005 s")
            if result["status"] == "ok" and boundaries is not None:
                start, end = boundaries["kernel_start_ns"], boundaries["kernel_end_ns"]
                if start < 0 or end <= start:
                    result.update(timing_status="invalid", timing_error="kernel nanosecond boundaries did not advance")
                elif abs(result["kernel_s"] - (end - start) / 1e9) > .0000005 + 1e-12:
                    result.update(timing_status="invalid", timing_error="kernel seconds differ from integer nanosecond boundaries")
                if self.kernel_clock != "unknown":
                    begin = result.get("clock_start_ns", {}).get(self.kernel_clock)
                    finish = result.get("clock_end_ns", {}).get(self.kernel_clock)
                    if type(begin) is not int or type(finish) is not int or not begin <= start < end <= finish:
                        result.update(timing_status="invalid", timing_error="kernel boundaries are outside same-domain process boundaries")
            if result["status"] == "ok":
                result.setdefault("timing_status", "ok")
                result.setdefault("timing_error", None)
                if result["timing_status"] == "invalid" and mode == "benchmark":
                    result.update(status="clock_error", error=result["timing_error"])
                result["score_eligible"] = mode == "benchmark" and result["timing_status"] == "ok"
        return result


class SearchStrategy:
    """Propose configurations using only this search's observed feedback."""
    def __init__(self, name, space, seed=0, min_trials=5, patience=3,
                 min_relative_improvement=0.0, *, budget=None, start=None):
        if name not in ALGORITHMS:
            raise ValueError("unknown search algorithm")
        if type(min_trials) is not int or min_trials < 1 or type(patience) is not int or patience < 1:
            raise ValueError("min_trials and patience must be positive integers")
        if not math.isfinite(min_relative_improvement) or not 0 <= min_relative_improvement < 1:
            raise ValueError("min_relative_improvement must be finite and in [0, 1)")
        if start is not None:
            if name != "greedy":
                raise ValueError("an explicit start is only supported by greedy")
            space.check(start)
        if name == "recheck" and (type(budget) is not int or budget < 4):
            raise ValueError("recheck requires a call budget of at least 4")
        self.name, self.space, self.scores = name, space, {}
        self.min_trials, self.patience = min_trials, patience
        self.min_relative_improvement = min_relative_improvement
        self.stale, self.best_score = 0, None
        self.order = list(space.configs)
        rng = random.Random(seed)
        if name in ("random", "patience", "recheck"):
            rng.shuffle(self.order)
        elif name == "stratified":
            blocks = {opt: list(space.blocks) for opt in space.opts}
            for values in blocks.values():
                rng.shuffle(values)
            self.order = []
            for i in range(len(space.blocks)):
                opts = list(space.opts)
                rng.shuffle(opts)
                self.order.extend(Config(blocks[opt][i], opt) for opt in opts)
        self.current = (start if start is not None else rng.choice(space.configs)) if name == "greedy" else None
        if name == "recheck":
            self.budget = budget
            self.explore_count = min(len(space.configs), budget - 2)
            self.first_scores, self.config_samples = {}, {}
            self.finalists, self.rechecked = None, set()

    def suggest(self):
        if self.name == "recheck":
            if len(self.first_scores) < self.explore_count:
                return next(c for c in self.order if c not in self.first_scores)
            return next((c for c in self.finalists if c not in self.rechecked), None)
        if self.name == "patience" and len(self.scores) >= self.min_trials and self.stale >= self.patience:
            return None
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
        if self.name == "recheck":
            samples = self.config_samples.setdefault(config, [])
            if config in self.first_scores:
                self.rechecked.add(config)
                if score is not None:
                    samples.append(score)
                self.scores[config] = statistics.median(samples) if score is not None else None
            else:
                self.first_scores[config] = score
                if score is not None:
                    samples.append(score)
                self.scores[config] = score
                if len(self.first_scores) == self.explore_count:
                    valid = [c for c in self.order if self.first_scores.get(c) is not None]
                    self.finalists = sorted(valid, key=lambda c: self.first_scores[c])[:2]
            return
        self.scores[config] = score
        if self.name == "patience":
            significant = score is not None and (self.best_score is None or
                (self.best_score - score) / self.best_score > self.min_relative_improvement)
            self.stale = 0 if significant else self.stale + 1
            if score is not None and (self.best_score is None or score < self.best_score):
                self.best_score = score

    def best(self, require_review=False):
        """S3's updated online scores can rise when a candidate is remeasured."""
        if self.name != "recheck":
            raise ValueError("aggregate best is only used by recheck")
        candidates = [c for c in self.order if self.scores.get(c) is not None and
                      (not (require_review or self.rechecked) or c in self.rechecked)]
        if not candidates:
            return None
        winner = min(candidates, key=lambda c: self.scores[c])
        return dict(config=asdict(winner), score=self.scores[winner])


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
    def __init__(self, target, space, journal, repeats=1, timeout=1800, *, mode="benchmark"):
        if type(repeats) is not int or repeats < 1:
            raise ValueError("repeats must be a positive integer")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be positive and finite")
        if mode not in RUN_MODES:
            raise ValueError("unknown run mode")
        self.target, self.space, self.journal = target, space, journal
        self.repeats, self.timeout, self.mode = repeats, timeout, mode
        self.session_started = None
        self.session_raw_started_ns = None

    def evaluate(self, config, trial_id, strategy=None):
        self.space.check(config)
        if strategy is not None:
            if strategy.name != "recheck" or self.repeats != 1 or self.mode != "benchmark":
                raise ValueError("aggregate scoring requires recheck with one process per trial")
            if config != strategy.suggest():
                raise ValueError("evaluation does not match next proposed configuration")
        records = [r for r in self.journal.records if r.get("trial_id") == trial_id]
        completed = next((r for r in records if r["type"] == "trial"), None)
        if completed:
            if completed["config"] != asdict(config):
                raise ValueError("completed trial configuration mismatch")
            return completed
        trial_started = time.monotonic()
        trial_raw_started_ns = raw_time_ns()
        if not records:
            self.journal.append("trial_start", trial_id=trial_id, config=asdict(config), started_at=now(),
                                raw_start_ns=trial_raw_started_ns)
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
                    start_callback = lambda data: emit("measurement_start", dict(repeat=repeat, **data))
                    if self.mode == "benchmark":
                        result = self.target.measure(build, config, self.timeout, start_callback)
                    else:
                        result = self.target.measure(build, config, self.timeout, start_callback, mode=self.mode)
                    measurements.append(emit("measurement", dict(repeat=repeat, **result)))
                    if result["status"] == "interrupted":
                        raise KeyboardInterrupt
                    if result["status"] != "ok":
                        break
        samples = [r["kernel_s"] for r in measurements if r["status"] == "ok"]
        valid = not interrupted_build and build is not None and build["status"] == "ok" and \
            len(measurements) == self.repeats and len(samples) == self.repeats
        score_eligible = valid and self.mode == "benchmark" and all(
            r.get("score_eligible", True) for r in measurements)
        score = statistics.median(samples) if score_eligible else None
        scoring = {}
        if strategy is not None:
            phase = "recheck" if config in strategy.first_scores else "explore"
            fresh_score = score
            strategy.observe(config, fresh_score)
            score = strategy.scores[config]
            best = strategy.best()
            scoring = dict(phase=phase, fresh_score=fresh_score,
                config_samples=list(strategy.config_samples[config]),
                return_eligible=config in strategy.rechecked and score is not None,
                finalists=[asdict(c) for c in strategy.finalists] if strategy.finalists is not None else None)
        else:
            previous = [r for r in self.journal.records if r["type"] == "trial" and r["score"] is not None]
            candidates = [dict(config=r["config"], score=r["score"]) for r in previous]
            if score_eligible:
                candidates.append(dict(config=asdict(config), score=score))
            best = min(candidates, key=lambda r: r["score"]) if candidates else None
        wall = time.monotonic() - trial_started
        trial_raw_ended_ns = raw_time_ns()
        raw_elapsed = (trial_raw_ended_ns - trial_raw_started_ns) / 1e9
        prior_wall = sum((r.get("compile_wall_s") or 0) for r in records if r["type"] == "build") + sum(
            (r.get("process_wall_s") or 0) for r in records if r["type"] == "measurement")
        prior_raw = sum(r.get("compile_raw_s") or 0 for r in records if r["type"] == "build") + sum(
            r.get("process_raw_s") or 0 for r in records if r["type"] == "measurement")
        cost = dict(started_at=records[0]["at"] if records else next(
            r["started_at"] for r in self.journal.records if r["type"] == "trial_start" and r["trial_id"] == trial_id),
            ended_at=now(), trial_wall_s=None if records else wall,
            trial_wall_recorded_s=prior_wall + wall, resumed=bool(records),
            raw_start_ns=trial_raw_started_ns, raw_end_ns=trial_raw_ended_ns,
            trial_raw_s=raw_elapsed if not records and raw_elapsed > 0 else None,
            trial_raw_recorded_s=prior_raw + raw_elapsed,
            primary_clock=PRIMARY_CLOCK)
        if self.session_started is not None:
            elapsed = sum(r["wall_s"] for r in self.journal.records if r["type"] == "session_end") + \
                time.monotonic() - self.session_started
            unknown = sum(r["type"] == "session_start" for r in self.journal.records) - sum(
                r["type"] == "session_end" for r in self.journal.records) > 1
            cost.update(tuning_elapsed_s=None if unknown else elapsed, tuning_elapsed_recorded_s=elapsed)
        if self.session_raw_started_ns is not None:
            completed_sessions = [r for r in self.journal.records if r["type"] == "session_end"]
            raw_elapsed = (trial_raw_ended_ns - self.session_raw_started_ns) / 1e9
            known_raw = sum(r["raw_s"] for r in completed_sessions if r.get("raw_s") is not None)
            unknown_raw = any(r.get("raw_s") is None for r in completed_sessions) or unknown or raw_elapsed <= 0
            cost.update(tuning_raw_elapsed_s=None if unknown_raw else known_raw + raw_elapsed,
                        tuning_raw_elapsed_recorded_s=known_raw + raw_elapsed)
        return emit("trial", dict(score=score, samples=samples, status="ok" if valid else "failed",
                                  mode=self.mode, score_eligible=score_eligible,
                                  best_so_far=best, **scoring, **cost))

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
    if strategy.name == "recheck" and (budget != strategy.budget or evaluator.repeats != 1):
        raise ValueError("recheck needs its declared call budget and repeats=1")
    journal = evaluator.journal
    final = next((r for r in journal.records if r["type"] == "summary"), None)
    if final:
        return final
    trials = [r for r in journal.records if r["type"] == "trial"]
    for trial in trials:
        strategy.observe(Config(**trial["config"]), trial["fresh_score"] if strategy.name == "recheck"
                         else trial["score"])
    session_started = session_started or dict(monotonic=time.monotonic(), raw_ns=raw_time_ns(), at=now())
    start = session_started["monotonic"]
    raw_start = session_started["raw_ns"] if "raw_ns" in session_started else raw_time_ns()
    evaluator.session_started = start
    evaluator.session_raw_started_ns = raw_start
    journal.append("session_start", started_at=session_started["at"], raw_start_ns=raw_start,
                   primary_clock=PRIMARY_CLOCK)
    try:
        for trial_id in range(len(trials), budget):
            config = strategy.suggest()
            if config is None:
                break
            if strategy.name == "recheck":
                evaluator.evaluate(config, trial_id, strategy)
            else:
                trial = evaluator.evaluate(config, trial_id)
                strategy.observe(config, trial["score"])
    finally:
        raw_end = raw_time_ns()
        journal.append("session_end", ended_at=now(), wall_s=time.monotonic() - start,
                       raw_start_ns=raw_start, raw_end_ns=raw_end,
                       raw_s=(raw_end - raw_start) / 1e9 if raw_end > raw_start else None,
                       primary_clock=PRIMARY_CLOCK)
    trials = [r for r in journal.records if r["type"] == "trial"]
    measurements = [r for r in journal.records if r["type"] == "measurement"]
    builds = [r for r in journal.records if r["type"] == "build"]
    compile_processes = sum(r["type"] == "build_start" for r in journal.records)
    incomplete_builds = len(unfinished_builds(journal.records))
    incomplete_sessions = sum(r["type"] == "session_start" for r in journal.records) - sum(
        r["type"] == "session_end" for r in journal.records)
    compile_wall = sum(r["compile_wall_s"] for r in builds)
    compile_raw = sum(r["compile_raw_s"] for r in builds if r.get("compile_raw_s") is not None)
    missing_compile_raw = incomplete_builds or any(r.get("compile_raw_s") is None for r in builds)
    tuning_wall = sum(r["wall_s"] for r in journal.records if r["type"] == "session_end")
    sessions = [r for r in journal.records if r["type"] == "session_end"]
    tuning_raw = sum(r["raw_s"] for r in sessions if r.get("raw_s") is not None)
    missing_tuning_raw = incomplete_sessions or any(r.get("raw_s") is None for r in sessions)
    stop_reason = "budget" if len(trials) >= budget else (
        "patience" if strategy.name == "patience" and len(strategy.scores) >= strategy.min_trials and
        strategy.stale >= strategy.patience else
        "local_optimum" if strategy.name == "greedy" else
        "candidate_exhausted" if strategy.name == "recheck" else "space_exhausted")
    scoring = {}
    if strategy.name == "recheck":
        scoring = dict(exploration_trials=sum(r["phase"] == "explore" for r in trials),
            recheck_trials=sum(r["phase"] == "recheck" for r in trials),
            eligible_configs=sum(c in strategy.rechecked and score is not None for c, score in strategy.scores.items()),
            finalists=[asdict(c) for c in strategy.finalists] if strategy.finalists is not None else None)
    return journal.append("summary", best=strategy.best(require_review=True) if strategy.name == "recheck" else
        trials[-1]["best_so_far"] if trials else None,
        stop_reason=stop_reason,
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
        tuning_wall_recorded_s=tuning_wall,
        compile_raw_s=None if missing_compile_raw else compile_raw,
        compile_raw_recorded_s=compile_raw, tuning_raw_s=None if missing_tuning_raw else tuning_raw,
        tuning_raw_recorded_s=tuning_raw, primary_clock=PRIMARY_CLOCK, mode=evaluator.mode, **scoring)


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
    parser.add_argument("--algorithm", choices=ALGORITHMS, default="grid")
    parser.add_argument("--min-trials", type=int, default=5)
    parser.add_argument("--patience", type=int, default=3)
    parser.add_argument("--min-relative-improvement", type=float, default=0.0,
                        help="relative reduction required to reset patience, e.g. 0.02 for 2%%")
    parser.add_argument("--budget", type=int, default=20)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--start-s", type=int, help="explicit Greedy start for the separate diagnostic panel")
    parser.add_argument("--start-opt", choices=OPTS)
    parser.add_argument("--timeout", type=float, default=1800)
    parser.add_argument("--mode", choices=RUN_MODES, default="benchmark")
    args = parser.parse_args(argv)
    journal = None
    session_started = dict(monotonic=time.monotonic(), raw_ns=raw_time_ns(), at=now())
    def interrupt(signum, frame):
        raise KeyboardInterrupt
    previous_handler = signal.signal(signal.SIGTERM, interrupt)
    try:
        space = ConfigSpace(tuple(int(s) for s in args.blocks.split(",")), args.opts.split(","))
        if args.budget < 0 or args.repeats < 1 or not math.isfinite(args.timeout) or args.timeout <= 0:
            raise ValueError("budget >= 0, repeats >= 1, and finite timeout > 0 required")
        if args.min_trials < 1 or args.patience < 1 or not math.isfinite(args.min_relative_improvement) or \
                not 0 <= args.min_relative_improvement < 1:
            raise ValueError("min_trials >= 1, patience >= 1, finite min_relative_improvement in [0, 1) required")
        if args.resume and args.output is None:
            raise ValueError("--resume requires --output")
        if (args.start_s is None) != (args.start_opt is None):
            raise ValueError("an explicit Greedy start needs both --start-s and --start-opt")
        explicit_start = Config(args.start_s, args.start_opt) if args.start_s is not None else None
        if explicit_start is not None:
            if args.action != "search" or args.algorithm != "greedy":
                raise ValueError("an explicit start is only supported for greedy search")
            space.check(explicit_start)
        if args.action == "search" and args.algorithm == "recheck" and (args.budget < 4 or args.repeats != 1):
            raise ValueError("recheck requires budget >= 4 and repeats=1")
        if args.action == "search" and args.mode != "benchmark":
            raise ValueError("search requires benchmark mode; correctness/diagnostic use run or build")
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
            min_trials=args.min_trials, patience=args.patience,
            min_relative_improvement=args.min_relative_improvement,
            repeats=args.repeats, timeout=args.timeout,
            runtime_affinity=sorted(os.sched_getaffinity(0)),
            mode=args.mode, primary_clock=PRIMARY_CLOCK, primary_clock_unit="ns",
            protocol_sha256=digest(args.protocol.read_bytes()) if args.protocol else None,
            cache_dir=str(target.cache_dir))
        if args.action == "search" and args.algorithm == "recheck":
            metadata.update(schema=2, recheck=dict(exploration_trials=min(len(space.configs), args.budget - 2),
                finalist_limit=2, rechecks_per_finalist=1, return_rule="successful_finalists_only",
                score="median_of_online_samples", tie_rule="random_visit_order"))
        if explicit_start is not None:
            metadata.update(schema=2, greedy_start=asdict(explicit_start))
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
            strategy = SearchStrategy(metadata["algorithm"], space, args.seed,
                                      args.min_trials, args.patience, args.min_relative_improvement,
                                      budget=metadata["budget"], start=explicit_start)
            result = search(strategy, Evaluator(target, space, journal, args.repeats, args.timeout, mode=args.mode),
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
