"""发布前检查最终文件、正确性记录、截图来源和完整 trace 的一致性。"""

import ast
import gzip
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    readme = (ROOT / "README.md").read_text()
    links = re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", readme)
    local_links = [link for link in links if not link.startswith(("https://", "http://", "#"))]
    assert all((ROOT / link.split("#")[0]).is_file() for link in local_links)
    assert len(re.findall(r"!\[", readme)) == 13
    forbidden = r"\b(?:Codex|ChatGPT|AI|Prompt|Engineering Status|Reviewer Notes|Requirement Matrix)\b|工程轨|理解轨|口径|独立核验"
    assert not re.search(forbidden, readme, re.I)

    syntax = []
    for directory in [ROOT / "src", ROOT / "scripts"]:
        for path in sorted(directory.glob("*.py")):
            ast.parse(path.read_text(), filename=str(path))
            syntax.append(str(path.relative_to(ROOT)))
        for path in sorted(directory.glob("*.sh")):
            subprocess.run(["bash", "-n", str(path)], check=True)

    source_manifest = json.loads((ROOT / "evidence/review/remote_source_manifest.json").read_text())
    assert all(sha256((ROOT / path).read_bytes()) == expected
               for path, expected in source_manifest.items())
    for phase in ["cpu", "correctness", "softmax", "online", "attention"]:
        assert (ROOT / f"evidence/commands/jobs/{phase}.exitcode").read_text().strip() == "0"

    correctness = []
    for name in ["school_softmax_cpu", "school_softmax_cuda", "school_triton",
                 "school_attention_cpu", "school_attention_cuda"]:
        result = json.loads((ROOT / f"evidence/correctness/{name}.json").read_text())
        records = result.get("checks", result.get("cases"))
        assert result["rtol"] == 1e-4 and result["atol"] == 1e-6
        assert all(r.get("status") == "PASS" or r.get("passed") is True for r in records)
        correctness.append({"name": name, "cases": len(records), "passed": True})
    assert sum(r["cases"] for r in correctness) == 58

    traces = json.loads((ROOT / "evidence/review/trace_manifest.json").read_text())
    assert len(traces) == 8
    for record in traces:
        compressed = (REPO / record["published_path"]).read_bytes()
        assert sha256(compressed) == record["compressed_sha256"]
        assert sha256(gzip.decompress(compressed)) == record["raw_sha256"]

    provenance = {}
    for path in (ROOT / "evidence/review").glob("perfetto_*.json"):
        record = json.loads(path.read_text())
        assert not record["errors"] and not record["import_statistics"]
        for item in record["images"]:
            provenance[Path(item["file"]).name] = item["sha256"]
    for line in (ROOT / "evidence/commands/screenshots.jsonl").read_text().splitlines():
        record = json.loads(line)
        provenance[Path(record["image"]).name] = record["image_sha256"]
    images = []
    for path in sorted((ROOT / "images").glob("*.png")):
        data = path.read_bytes()
        assert data[:8] == b"\x89PNG\r\n\x1a\n"
        width, height = struct.unpack(">II", data[16:24])
        assert width >= 1500 and height >= 800
        assert sha256(data) == provenance[path.name]
        images.append({"path": str(path.relative_to(ROOT)), "width": width,
                       "height": height, "sha256": sha256(data)})
    assert len(images) == 13

    files = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "A3"],
        cwd=REPO, text=True).splitlines()
    patterns = [re.compile(r"-----BEGIN (?:[A-Z ]* )?PRIVATE KEY-----"),
                re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
                re.compile(r"\bAKIA[0-9A-Z]{16}\b")]
    for name in files:
        path = REPO / name
        assert not set(path.parts) & {"__pycache__", ".venv", ".cache"}
        assert path.suffix not in {".pyc", ".o", ".so", ".pdf", ".docx", ".zip"}
        assert path.stat().st_size < 10_000_000, name
        if path.suffix in {".png", ".gz"}:
            continue
        text = path.read_text()
        for pattern in patterns:
            assert not pattern.search(text), f"possible credential marker in {name}"

    report = {"status": "PASS", "readme_sha256": sha256(readme.encode()),
              "relative_links": local_links, "syntax_checked": syntax,
              "remote_source_files_match": True, "remote_job_exitcodes": "all 0",
              "correctness": correctness, "complete_lossless_traces": len(traces),
              "images": images, "publication_files_checked": len(files),
              "secret_markers_found": 0,
              "boundary": "Artifact self-check only; Engineering final review and teacher submission remain pending."}
    output = ROOT / "evidence/review/final_validation.json"
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print("PASS: source/shell syntax; 58 correctness records; 8 complete lossless traces;")
    print("13 screenshot hashes; README links; source transfer identity; file/credential checks.")
    print("Result:", output.relative_to(ROOT))


if __name__ == "__main__":
    main()
