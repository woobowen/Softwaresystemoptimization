"""将当前 A3 的源码和已生成结果导出到目录之外，不改变原始结果。"""

import argparse
import hashlib
from pathlib import Path
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    destination = args.output.resolve()
    if destination.is_relative_to(root):
        parser.error("write the ZIP outside A3 to prevent recursive packaging")
    destination.parent.mkdir(parents=True, exist_ok=True)
    files = [p for p in root.rglob("*") if p.is_file()
             and not any(part in {"__pycache__", ".ipynb_checkpoints", ".cache", ".venv"}
                         for part in p.relative_to(root).parts)
             and p.suffix not in {".pyc", ".zip"}]
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(files):
            archive.write(path, Path("A3") / path.relative_to(root))
    print(destination)
    print("files:", len(files))
    print("SHA256:", hashlib.sha256(destination.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
