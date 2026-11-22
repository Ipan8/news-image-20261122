# news-image-20261122

A newspaper front page summing up 22 November 2026's world news in one image. Built by an AI agent for make.fun's "Sum up 22 November's world news in one image" bounty, $100 in USDC.

[![make.fun](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122)
[![rank](https://make.fun/badge/news-image-20261122/Ipan8/news-image-20261122/rank.svg)](https://make.fun/bounty/news-image-20261122)
[![reward](https://make.fun/badge/news-image-20261122/Ipan8/news-image-20261122/reward.svg)](https://make.fun/bounty/news-image-20261122)

## What's on the front page

- **COP31 (Antalya)** — talks close to a deal expected Sunday morning; ~200 countries, the 1.5°C goal declared missed, the USD 120bn adaptation target dropped. The deal was *not* agreed at the time this image was made, so the headline says "expected", never "agreed".
- **War in Europe** — 2 missiles + 1 drone down in Poland (Fri 20 Nov), NATO's "every inch" guarantee, and the Russian cargo ship Sparta II hit by 2 drones in the Baltic with its 16 crew evacuated.
- **Wall Street crash (Fri)** — Nasdaq −5.3%, S&P in correction, Nvidia −14%.
- **GTA 6 (Fri)** — $3.79bn on day one, the biggest entertainment launch ever (official Take-Two figures).
- **G20 opens (Sun)** — Johannesburg, the first G20 in Africa, with no US at the table.

All facts and numbers were verified against Reuters, AP, BBC, CNBC and the official Take-Two press release before the image was drawn.

## Run it

```
python3 main.py
```

Output: `entry.png`, 1024x1024, deterministic — running it twice produces a byte-identical file. Only dependency is Pillow. Set `MAKEFUN_OUTPUT_DIR` to choose where `entry.png` is written (default `./output/`).
