# SAT Toolkit for TI-84

A menu-driven SAT program for the TI-84: math solvers, formula sheets, a Reading & Writing guide, practice quizzes, and test strategy.

## Which file do I use?

| Calculator | File(s) | Size |
|---|---|---|
| **TI-84 Plus CE** (color screen, rechargeable) | `TI-84 Plus CE/SAT.8xp` | 33.7 KB |
| **TI-84 Plus / Silver Edition** (gray screen, AAA batteries) | `TI-84 Plus (older models)/SATMATH.8xp` and `SATRW.8xp` | 17.5 KB + 11.9 KB |

The older TI-84 Plus only has about 24 KB of RAM, so its version comes split in two, with uppercase text to save space. Both halves together are bigger than 24 KB, so keep one in RAM and the other archived. To swap them, press **2nd → + (MEM) → 2:Mem Mgmt → 7:Prgm**, then press ENTER on a program to archive or unarchive it (a `*` means archived). Archived programs can't run on the older models.

## Install

1. Install **TI Connect CE** (free from education.ti.com).
2. Plug in the calculator with its USB cable and turn it on.
3. Drag the `.8xp` file into TI Connect CE and choose **Send to calculator** (send to RAM).
4. On the calculator, press **prgm**, pick **SAT**, then press **ENTER** twice.

## Controls

- **Menus:** press the item's number, or arrow to it and press ENTER.
- **Reference pages:** ← → (or ENTER) to turn pages, **CLEAR** to go back.
- **Quizzes:** type your answer (fractions such as `2/3` are fine), or press 1–4 for grammar questions.
- **Stuck:** press **ON** to break out of the program.
- Use the **(-)** key for negative numbers, not the minus key.

## What's inside

**Math Solvers** (every result is shown as an exact fraction where possible)
- Quadratic: discriminant, roots, *exact radical roots* such as `x=(2+√(10))/2`, complex roots, vertex, min/max, sum and product of roots
- 2×2 system: one, none or infinitely many solutions
- Line through 2 points: slope, intercepts, perpendicular slope, midpoint, distance (also as a simplified radical)
- Exponential: end value with compounding, or the growth rate from start and end values
- Percent: % change, x% of y, what %, undo a % change, stacked % changes, proportions
- Geometry/Stats: circle general form → center and radius, right triangle (sides, angles, sin/cos/tan as fractions), arc length and sector area (also in "π units"), mean/median/SD, missing value for a target mean, degrees ↔ radians

**Math Formulas:** linear equations, quadratics, exponents and radicals, exponential growth, functions, geometry, circles, triangles and trig, statistics, probability, percent and units.

**R&W Guide:** punctuation (semicolons, colons, dashes, commas, apostrophes), grammar (agreement, pronouns, tense, modifiers, parallelism), transitions by type, student-notes questions, reading question types, R&W pacing.

**Practice Quiz:** randomly generated math questions (10 types, endless) and 18 grammar questions with explanations, with score tracking.

**Test Strategy:** digital SAT format, adaptive modules, pacing, rules for typed answers, test-day checklist.

## Notes

- The program uses variables A–Z, θ and list L6, and overwrites whatever was in them.
- The trig solver works in both Degree and Radian mode.
- Calculators are only allowed during the Math section. The R&W content is for studying beforehand.
- Check College Board's current calculator policy before test day.

## Editing

All content and logic lives in `build_sat.py`. Edit it, then run `python build_sat.py` (needs `pip install tivars`) to regenerate all three `.8xp` files. The build checks every screen line for the 16-character width and catches TI-BASIC structure mistakes. The readable source listings are in `source/`.
