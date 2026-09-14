#!/usr/bin/env python3
"""Check the small HW1 matrices against their printed inputs."""
from pathlib import Path
import re
import subprocess

directory = Path(__file__).resolve().parents[1] / "mit6172/matrix-multiply"
for option in ("-p", "-pz"):
    previous = None
    for trial in range(1, 4):
        result = subprocess.run(
            ["./matrix_multiply", option], cwd=directory,
            text=True, capture_output=True, check=True,
        )
        print(f"$ ./matrix_multiply {option} (trial {trial}, exit 0)")
        print(result.stderr + result.stdout, end="")
        blocks = re.findall(r"------------\n(.*?)------------", result.stdout, re.S)
        assert len(blocks) == 3, "expected A, B and C"
        a, b, c = [
            [[int(value) for value in row.split()] for row in block.strip().splitlines()]
            for block in blocks
        ]
        assert all(len(matrix) == 4 and all(len(row) == 4 for row in matrix)
                   for matrix in (a, b, c))
        expected = [[sum(x * y for x, y in zip(row, column))
                     for column in zip(*b)] for row in a]
        assert c == expected, (c, expected)
        if option == "-pz":
            assert all(value == 0 for matrix in (a, b, c)
                       for row in matrix for value in row)
        if previous is not None:
            assert (a, b, c) == previous, "fixed-seed results changed"
        previous = (a, b, c)
        print("CORRECTNESS=PASS\n")
print("6 runs passed; timings were not used to claim a speedup.")
