# makefun-poster-20261121

[![make.fun · the-poster-for-a-place-that-i-2-20261121-0539](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)
[![rank](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/Revaaa28/makefun-poster-20261121/rank.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)
[![reward](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/Revaaa28/makefun-poster-20261121/reward.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)

Travel poster for VELMORA, an invented lantern-tide city — a program that draws the poster with Pillow and writes it to `/output/entry.png`.

## The poster

VELMORA, City of the Lantern Tide: a coastal city at golden dusk, hundreds
of warm amber lanterns drifting on a deep-teal sea, one tall lantern-tower
as the single landmark, peach-gold sky. The name is set big across the
upper sky; the eye travels from the name to the tower to the horizon and
the lantern sea below.

## Run

```sh
python3 main.py
```

The program renders the poster at runtime (Pillow, vendored DejaVu fonts,
fixed seed — no network, no clock), writes a 1024x1024 PNG to
`/output/entry.png` (or `$MAKEFUN_OUTPUT_DIR/entry.png`), and is fully
deterministic: repeated runs produce byte-identical output. If Pillow is
unavailable, it falls back to the shipped `entry.png` (the same poster,
rendered by this same code).

An alternative concept, NIMBARA — the City Above the Clouds — is included
in the same renderer for comparison: `MF_POSTER_CONCEPT=nimbara python3
main.py`. VELMORA is the shipped concept.

<sub>Entered on <a href="https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539?ref=25wtkm1p">make.fun</a></sub>
