#!/usr/bin/env python3
"""Check the review ZIP, its file hashes, report links and absence of build files."""

import hashlib
from pathlib import PurePosixPath
import re
import sys
from zipfile import ZipFile

with ZipFile(sys.argv[1]) as archive:
    assert archive.testzip() is None, "ZIP CRC failure"
    names = archive.namelist()
    assert len(names) == len(set(names)), "Duplicate archive entries"
    for name in names:
        path = PurePosixPath(name)
        assert path.parts[0] == "P2" and ".." not in path.parts
        assert not path.is_absolute()
        assert path.suffix not in {".o", ".pyc", ".zip", ".pdf", ".docx", ".cg", ".data"}, name
        assert "__pycache__" not in path.parts and ".cache" not in path.parts
        assert path.name != "AGENTS.md"
        assert not archive.read(name).startswith(b"\x7fELF"), name
    manifest_name = "P2/evidence/final/manifest.sha256"
    expected = {}
    for line in archive.read(manifest_name).decode().splitlines():
        checksum, path = line.split("  ", 1)
        expected["P2/" + path] = checksum
    assert set(expected) == set(names) - {manifest_name}, "Manifest/file list mismatch"
    for name, checksum in expected.items():
        assert hashlib.sha256(archive.read(name)).hexdigest() == checksum, name
    report = archive.read("P2/README.md").decode()
    links = re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", report)
    local = [link.split("#", 1)[0] for link in links if not link.startswith(("https://", "http://", "#"))]
    assert all("P2/" + link in expected for link in local), "Missing report link target"
    headings = re.findall(r"^## (.+)$", report, flags=re.M)
    assert headings == ["Checkoff Item 1", "Checkoff Item 2"] + [f"Write-up {n}" for n in range(1, 8)] + ["简短总结"]
    assert not re.search(r"Codex|ChatGPT|\bAI\b|Prompt|Engineering Status|Reviewer Notes|Requirement Matrix", report, re.I)
    images = [name for name in names if name.startswith("P2/images/")]
    assert len(images) == 12
    print(f"ZIP CRC, safe paths and {len(names)} file entries: passed")
    print(f"SHA-256: {len(expected)} manifest entries passed (manifest excludes itself)")
    print(f"Report: 9 questions, {len(local)} local links, {len(images)} images passed")
    print("No ELF/build/cache/input-archive files or formal-report workflow terms found")
