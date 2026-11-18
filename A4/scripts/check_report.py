#!/usr/bin/env python3
import re
import sys
from pathlib import Path
text = Path(sys.argv[1]).read_text()
rows = re.findall(r'^\s*\d+\s+"([^"]+)"\s+([0-9.]+) sec', text, re.M)
groups = re.findall(r'^Total absolute time for (.+): ([0-9.]+) sec$', text, re.M)
if len(rows) != 144 or len(groups) != 30 or len({x[0] for x in rows}) != len(rows):
    sys.exit(f'invalid report: {len(rows)} rows, {len(groups)} groups, {len(set(x[0] for x in rows))} unique labels')
if any(float(t) <= 0 for _, t in rows):
    sys.exit('nonpositive time')
