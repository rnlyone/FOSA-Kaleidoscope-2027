# FOSA Kaleidoscope 2027

Website and promotional material for **FOSA Kaleidoscope**, the 2027 Culture Show of the
Fukuoka Overseas Students Association (FOSA).

- **When:** Sunday 17 January 2027, 1:00 to 3:00 PM (reception from 12:30 PM)
- **Where:** Acros Fukuoka Event Hall, B2F, 1-1-1 Tenjin, Chuo-ku, Fukuoka
- **Entry:** free, open to everyone

## What is in this repository

| Path | What it is |
| --- | --- |
| `index.html` | The website: a single page with no build step. GSAP and ScrollTrigger load from cdnjs. |
| `a/` | The poster cut into about 200 pieces (WebP), the Josefin Sans fonts taken from the original PPT, and the logos |
| `p/` | Photographs from past FOSA culture shows |
| `instagram/` | The 5-slide Instagram carousel (1080×1440), numbered in posting order |
| `tools/` | The scripts that cut the poster into pieces and build the page and the Instagram slides |

## The website

The poster assembles itself from its own shards on load. The mandala keeps turning and the pieces
drift. Moving the pointer gives depth, and clicking the poster shatters it. On wide screens the
burst continues past the poster to the edges of the window. Scrolling flies through the
kaleidoscope into the sections About, Visit, Moments and Perform. Detailed information stays
folded until a visitor opens it, and two buttons lead to the Google Forms:

- Reserve a free seat: <https://docs.google.com/forms/d/e/1FAIpQLScnq_7KdX7n0TUb3ejYYVlVX7Rb1DaBfD8H6RL7N6RVIiZ0eA/viewform>
- Apply to perform (deadline 22 December 2026, 23:59): <https://docs.google.com/forms/d/e/1FAIpQLSf-Yb4Z6fFtThfv4eqUFXkcBd-k0pBupnIcVt54X3RXIHmTBQ/viewform>

All motion respects `prefers-reduced-motion`.

### Run it locally

Any static server works, for example:

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000>.

### Publish with GitHub Pages

Settings › Pages › Deploy from a branch › `main` / root. The site has no build step.

## Instagram carousel

| File | Slide |
| --- | --- |
| `01_kaleidoscope-intro.mp4` | The poster's intro animation (9 s, H.264, silent track) |
| `02_event.png` | Date, time and venue |
| `03_perform.png` | Call for performers |
| `04_moments.png` | Photos from past shows |
| `05_fukuoka-is-open.png` | FUKUOKA IS OPEN International Exchange Festival (国際交流フェスタ), held the same day at JR Kyushu Hall |

Slides 2 to 5 are designed as one panorama, so some shards continue across slide edges when swiped.

## Tools

The scripts in `tools/` document how the material was made. They expect the extracted PPT
(`ppt/media`, `ppt/slides`) and use hard-coded working paths, so adjust those before you rerun them.

- `seg.py` cuts the poster's flattened background into separate transparent pieces.
- `build.py` reads the slide, exports the overlays and text positions, and fills `template.html` to produce `index.html`.
- `template.html` is the source of the page: its CSS and the GSAP animation.
- `render.py` renders the intro video frame by frame. `slides.tpl.html` and `shot_slides.py` render the static slides.

## Contact

FOSA, Fukuoka Overseas Students Association.
Email info.fosa16@gmail.com · Instagram [@fosafukuoka](https://www.instagram.com/fosafukuoka/)
