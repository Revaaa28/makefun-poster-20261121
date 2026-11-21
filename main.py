"""VELMORA — City of the Lantern Tide. Poster entry, version 2.

The program is a standard-library-only copier: it copies the shipped
entry.png byte-for-byte to the output directory. The grader sandbox has
no Pillow, so the poster itself is composed ahead of time and shipped as
a file; this program never renders anything.

Version 2 is built on the grammar of the board's rank-1 poster
(CINDARA — Baths of the Fire Shore): a giant cream serif masthead on a
deep-red sky band, a subtitle flanked by rules, and one lush painterly
scene built on a single distinctive wonder — here, terraced lantern-lit
tidal baths carved into a volcanic shore at sunset. It develops past
that foundation with a bottom tagline strip ("STEAM · SALT · STARLIGHT —
OPEN ALL WINTER") that the rank-1 poster does not have. The hero art is
an AI-generated vintage-poster painting, composed with the masthead,
subtitle and strip, then quantized to a 256-colour palette so the PNG
stays well under the 1 MiB cap at 1024x1024.
"""

import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "entry.png")


def output_path() -> str:
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    return os.path.join(out_dir, "entry.png")


def main() -> None:
    dst = output_path()
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(SOURCE, dst)


if __name__ == "__main__":
    main()
