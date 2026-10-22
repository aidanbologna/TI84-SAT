# TI84-SAT

**A complete SAT toolkit for the TI-84 graphing calculator.** Math solvers that show exact answers, a formula reference, a Reading & Writing guide, practice quizzes, and test-day strategy, all in one menu-driven program.

<p align="center">
  <img src="docs/images/demo.gif" alt="Demo: main menu, quadratic solver, formula pages, grammar quiz" width="360">
</p>

<p align="center">
  <a href="https://github.com/aidanbologna/TI84-SAT/releases/latest"><b>⬇ Download the latest release</b></a>
  &nbsp;·&nbsp; Works on the TI-84 Plus CE and the older TI-84 Plus / Silver Edition
</p>

---

## Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Which file do I need?](#which-file-do-i-need)
- [Install](#install)
- [Controls](#controls)
- [Solver reference](#solver-reference)
- [Building from source](#building-from-source)
- [Testing](#testing)
- [Project layout](#project-layout)
- [Notes](#notes)

## Features

| | |
|---|---|
| 🧮 **Math Solvers** | Quadratics with **exact radical roots** like `(2+√(10))/2`, 2×2 systems, lines from two points, exponential growth, six percent tools, circles from general form, right triangles, arcs and sectors, statistics, a missing-value finder, and degrees ↔ radians |
| 📐 **Math Formulas** | 11 topics in about 35 pages, from linear equations to probability, written for SAT-style questions |
| 📖 **Reading & Writing Guide** | Punctuation, grammar, transitions, student-notes questions, reading question types, R&W pacing |
| ✏️ **Practice Quiz** | Endless random math questions (10 types) and 18 grammar questions with explanations, with score tracking |
| 🎯 **Test Strategy** | Digital SAT format, adaptive modules, rules for typed answers, test-day checklist |

Answers show as **fractions** wherever possible (`4/3`, not `1.333333333`), and square roots are **simplified** (`2√(5)`), which matches how SAT answer choices are written.

## Screenshots

> These are rendered from the program running in the repo's TI-BASIC simulator ([`tools/`](tools)). They show exactly what the program draws on the calculator's 16×8 home screen.

### Menus

<p align="center"><img src="docs/images/sheet-menus.png" alt="Splash screen, main menu, math solvers menu" width="820"></p>

### Quadratic solver

Type in a, b and c to get the discriminant, both roots, the exact simplified radical form, the vertex, min/max, and the sum and product of the roots.

<p align="center"><img src="docs/images/sheet-quadratic.png" alt="Quadratic solver input, roots, exact roots, vertex" width="560"></p>

### More solvers

Line through two points, circle from `x²+y²+dx+ey+f=0`, and a right-triangle solver with trig ratios as fractions.

<p align="center"><img src="docs/images/sheet-solvers.png" alt="Line slope, midpoint and distance, circle center and radius, right triangle trig" width="560"></p>

### Formula & R&W reference

Every topic is a set of pages you flip with the arrow keys.

<p align="center"><img src="docs/images/sheet-reference.png" alt="Quadratics formulas, circles formulas, punctuation rules, transition words" width="560"></p>

### Practice quizzes

<p align="center"><img src="docs/images/sheet-quiz.png" alt="Math quiz question and feedback, grammar question and explanation" width="560"></p>

## Which file do I need?

| Your calculator | How to tell | Download |
|---|---|---|
| **TI-84 Plus CE** | Color screen, rechargeable battery | `SAT.8xp` (33.7 KB) |
| **TI-84 Plus / Silver Edition** | Gray screen, AAA batteries | `SATMATH.8xp` + `SATRW.8xp` |

The older TI-84 Plus only has about 24 KB of RAM, so its version comes in two halves with uppercase text, which takes half the space. The halves are the same as the CE version, just divided:

- **SATMATH** (17.5 KB): math solvers, formulas, math quiz, strategy
- **SATRW** (11.9 KB): Reading & Writing guide, grammar quiz, strategy

Both together don't fit in RAM at once, so keep one **archived**. Press `2nd` `+` (MEM) → `2:Mem Mgmt/Del` → `7:Prgm`, then press `ENTER` on a program to archive or unarchive it (a `*` means archived). Older models can't run archived programs.

## Install

1. Download the file(s) from the [latest release](https://github.com/aidanbologna/TI84-SAT/releases/latest), or from the [`TI-84 Plus CE`](TI-84%20Plus%20CE) and [`TI-84 Plus (older models)`](TI-84%20Plus%20(older%20models)) folders.
2. Install **TI Connect CE** (free from [education.ti.com](https://education.ti.com/en/products/computer-software/ti-connect-ce-sw)).
3. Connect the calculator with its USB cable and turn it on.
4. Drag the `.8xp` file into TI Connect CE and choose **Send to calculator**.
5. On the calculator, press `prgm`, choose **SAT** (or **SATMATH** / **SATRW**), then press `ENTER` twice.

## Controls

| Key | Action |
|---|---|
| Number keys or `ENTER` | Pick a menu item |
| `←` `→` (or `ENTER`) | Previous / next page in a reference topic |
| `CLEAR` | Leave a topic or end a quiz |
| `1`–`4` | Answer a grammar question |
| `(-)` | Type a negative number (not the minus key) |
| `ON` | Break out of the program at any time |

Fractions work anywhere a number is asked for, so `2/3` is fine. Where angles are asked for in radians, you can type `π/3` using the `π` key.

## Solver reference

| Solver | You enter | You get |
|---|---|---|
| Quadratic | a, b, c | Discriminant, number of real roots, roots, exact radical roots, complex roots `p ± qi`, vertex, min/max, sum and product of roots |
| System 2×2 | `ax+by=c`, `dx+ey=f` | The solution, or "no solution" / "infinitely many" |
| Line: 2 points | (x1, y1), (x2, y2) | Slope, y-intercept, x-intercept, perpendicular slope, midpoint, distance (also as a simplified radical) |
| Exponential | Start, rate %, times per year, years | End value, yearly growth factor, total % change |
| Exponential rate | Start, end, periods | Growth factor and % rate per period |
| Percent | Six tools | % change, x% of y, x is ?% of y, undo a % change, stacked % changes, proportion `a/b = c/x` |
| Circle | `ax²+ay²+dx+ey+f=0` | Center, r², r, exact radical r |
| Right triangle | Any two sides (0 = unknown) | Missing side, both angles, sin/cos/tan of A as fractions |
| Arc & sector | Radius, angle (degrees or radians) | Arc length, sector area (both also in π units), fraction of the circle, circumference |
| Mean/Median/SD | A list like `{2,5,9}` | Mean, median, range, SD, count, sum, min/max, sorted list |
| Missing value | Count, current mean, target mean | The value needed to hit the target |
| Deg ↔ Rad | An angle | The converted angle, with radians in π units |

## Building from source

All screen text and program logic lives in one file, [`build_sat.py`](build_sat.py). It writes TI-BASIC from templates and tokenizes it into `.8xp` files with [tivars](https://pypi.org/project/tivars/).

```bash
pip install tivars
```

```bash
python build_sat.py
```

That regenerates all three programs:

```
SAT       2104 lines  33602 bytes
SATMATH   1371 lines  17432 bytes
SATRW      842 lines  11822 bytes
```

The build fails if any line of text is too wide for the 16-character screen, if a label is missing, if a block is unbalanced, or if a `Goto` jumps out of an `If`/loop block. On a real TI, that last one slowly leaks memory until `ERR:MEMORY`. The readable TI-BASIC listings are written to [`source/`](source).

## Testing

[`tools/sim.py`](tools/sim.py) is a small TI-BASIC interpreter for the subset this program uses. It models the 16×8 home screen, `Disp` scrolling, `Output(` wrapping, `►Frac`, and real TI behavior such as `and` not short-circuiting and `√(` of a negative raising `ERR:NONREAL ANS`.

```bash
python tools/test_solvers.py
```

```bash
python tools/test_all.py
```

- `test_solvers.py` runs about 40 solver cases with known answers, including edge cases (a = 0, complex roots, vertical lines, invalid triangles, Degree vs Radian mode).
- `test_all.py` flips through every reference page in all three builds, plays both quizzes (checking the final score), and runs 450 random fuzz walks with odd inputs (0, negatives, fractions, π), failing on any crash or screen overflow.

To regenerate the README images and demo GIF (needs Pillow):

```bash
python tools/screenshots.py
```

## Project layout

```
TI84-SAT/
├── build_sat.py                  # all content + program logic → .8xp
├── TI-84 Plus CE/SAT.8xp         # full program (CE)
├── TI-84 Plus (older models)/
│   ├── SATMATH.8xp               # math half (TI-84 Plus / SE)
│   └── SATRW.8xp                 # reading & writing half
├── source/                       # readable TI-BASIC listings
├── tools/
│   ├── sim.py                    # TI-BASIC simulator
│   ├── test_solvers.py           # solver cases with known answers
│   ├── test_all.py               # pages, quizzes, fuzzing
│   └── screenshots.py            # README images + demo GIF
└── docs/images/                  # screenshots
```

## Notes

- The program uses variables **A–Z**, **θ** and list **L6**, and overwrites whatever was in them.
- Calculators are only allowed during the **Math** section of the SAT. The Reading & Writing content is for studying beforehand.
- Check the College Board's current calculator policy before test day.
- The screenshots come from the simulator, not photos of a calculator. On a TI-84 Plus CE the same text appears in the top-left of its larger screen.
- This project is not affiliated with or endorsed by the College Board or Texas Instruments. SAT is a trademark of the College Board, and TI-84 is a trademark of Texas Instruments.
