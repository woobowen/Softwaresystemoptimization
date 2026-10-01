#!/usr/bin/env python3
"""Copy the complete native result trees named by a completed runner record."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import sys
from urllib.parse import unquote, urlsplit


class Resources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        self.links.extend(value for key, value in attrs if key in ("src", "href") and value)


def hashes(directory):
    return {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(directory.rglob("*")) if p.is_file()}


metadata, destination = map(Path, sys.argv[1:])
run = json.loads(metadata.read_text())
assert run["end"] and run["exit_code"] == 0, "Run has not completed successfully"
assert run["result_paths"], "Run did not produce a result directory"
records = []
for value in run["result_paths"]:
    source = Path(value)
    target = destination / source.name
    if not target.exists():
        shutil.copytree(source, target)
    original, copied = hashes(source), hashes(target)
    assert original == copied, f"Copy differs: {target}"
    for suffix in (".raw", ".txt", ".html", ".summary", ".sub"):
        assert list(target.glob("*" + suffix)), f"Missing {suffix} in {target}"
    links = 0
    for page in target.rglob("*.html"):
        parser = Resources()
        parser.feed(page.read_text(encoding="latin1"))
        for link in parser.links:
            url = urlsplit(link)
            if not url.scheme and not url.netloc and url.path:
                resolved = page.parent / unquote(url.path)
                assert resolved.exists(), f"Broken native resource: {page}: {link}"
                links += 1
    records.append({"source": str(source), "copy": str(target.resolve()),
                    "file_count": len(copied), "relative_links_checked": links,
                    "sha256": copied})
metadata.with_name("copy-manifest.json").write_text(json.dumps(records, indent=2) + "\n")
print(json.dumps([{k: v for k, v in r.items() if k != "sha256"} for r in records], indent=2))
