#!/usr/bin/env python3
"""Copy the pre-rendered entry image to the output directory.

The image (entry.png, 1024x1024) is the verified v2 render of
"The World Today" front page for Sunday 22 November 2026. This program
is standard library only: it just copies the file, so repeated runs
produce byte-identical output.

Usage:  python3 main.py
Output: entry.png in $MAKEFUN_OUTPUT_DIR if set, else /output/entry.png
"""

import os
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "entry.png"


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    shutil.copyfile(SRC, os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
