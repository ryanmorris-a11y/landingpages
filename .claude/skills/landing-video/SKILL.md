---
name: landing-video
description: "Landing page video stage v1 (2026-11-17): cloud-only port of the HyperAgent video assembly. Renders the 8 title cards with Pillow and assembles the single-voice 1:45 to 2:00 MP4 with ffmpeg, from voice-over, b-roll, music and product footage inputs. Use when a landing page needs its overview video, as part of the enhance stage of pg-landing-publish. Does not generate the voice-over or b-roll itself."
---

# landing-video

**Version 1 (2026-11-17).** Ports the two local steps of HyperAgent's `pg-landing-enhancer` video pipeline (`make_cards.py`, `build_video.sh`) so they run in a Claude cloud session with no Mac. The generation steps are not ported, because this session had no generation tools. See Inputs.

## What runs here

- `scripts/make_cards.py <config.json> <account_dir>` renders `cards/{s0_overlay,s1,s2,s6,s7,s8}.png` in the locked identity (navy gradient, coral line, Inter). Uses the installed Inter OTF files in `/usr/share/fonts/opentype/inter` (override with `INTER_DIR`). Tested 2026-11-17.
- `scripts/build_video.sh <account_dir> <slug>` assembles `<slug>_video.mp4` with ffmpeg only. Exits 3 and names the file if any input is missing. Assembly itself is untested until real inputs exist.
- `scripts/upload_binary.py` lives in the `pg-landing-enhancer` skill and commits the finished MP4 and poster into `<slug>/` in this repo.

Config for `make_cards.py` is one JSON per account, with the account name, the on-screen overlay text and the three lines for scene 1. Take scene text from the page's dated signals. Never put an unverified claim on a card.

## Inputs this session cannot make

| Input | Where it comes from | Status 2026-11-17 |
|---|---|---|
| `assets/vo.wav` | One continuous narrator clip, about 208 words, 8-scene script, Australian-accented corporate narrator | No generation tool in the cloud session |
| `assets/broll.mp4` | 8 second opening b-roll, no on-screen text | No generation tool |
| `assets/music_src.mp4` | Instrumental bed, verified by transcription to contain no speech | No generation tool |
| `assets/reference.mp4` | Real Airtable product footage | A HyperAgent asset, not in this repo. Ryan to supply once, then commit it to the repo |

The original pipeline used Gemini text to speech and Veo through HyperAgent built-in tools. If Ryan chooses the Gemini API route instead, the session needs network access to the Gemini API host and a key stored as a cloud environment secret by Ryan himself. Never ask for the key in chat and never write it to a file.

## Cloud environment requirements (for Ryan to apply)

1. **Network access, brand kit.** Allow outbound HTTPS to each confirmed customer domain (and its `www.` host) plus `logo.clearbit.com` and `www.google.com` (the hosts `brand_kit.py` calls). Alternatively use full network access for the landing page environment. On 2026-11-17 only package registries and GitHub were reachable, and everything else returned 403 at the egress proxy.
2. **Network access, video.** Allow the host of whichever generation service is chosen. Not decided.
3. **Secrets.** Any generation key goes in the environment's secret settings.
4. **Files.** `reference.mp4` committed once to the repo.

## Rules

1. Single voice only. Use the voice-over plus the verified instrumental bed. Never use b-roll audio.
2. No avatar or talking-head video.
3. Host on GitHub Pages only, media referenced by absolute `https://ryanmorris-a11y.github.io/landingpages/<slug>/...` URLs.
4. Status becomes `Live & Enhanced` only when a non-fallback brand kit and a published video both exist (see `pg-landing-publish`).
5. Plain hyphens only in all copy.
