"""Render README screenshots and a demo GIF by running the program in the simulator.

Every image shows exactly what the program draws on the 16x8 home screen.
Run from anywhere:  python tools/screenshots.py   (writes docs/images/)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from sim import Machine, OutOfEvents

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "images"
OUT.mkdir(parents=True, exist_ok=True)

FONT = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 30)
FONT_B = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 30)
CW, CH = 17, 34            # character cell
PAD = 18                   # LCD inner padding
BEZEL = 26
LCD_BG = (199, 208, 184)
LCD_FG = (28, 34, 26)
LCD_GRID = (190, 199, 175)
BEZEL_C = (44, 47, 54)
BEZEL_EDGE = (70, 74, 84)


def render_rows(rows, inverse=()):
    """rows: 8 strings of 16 chars. inverse: set of (row, col) cells drawn white-on-dark."""
    w, h = 16 * CW + 2 * PAD, 8 * CH + 2 * PAD
    lcd = Image.new("RGB", (w, h), LCD_BG)
    d = ImageDraw.Draw(lcd)
    for x in range(PAD, w - PAD, 3):  # faint pixel grid
        d.line([(x, PAD), (x, h - PAD)], fill=LCD_GRID)
    for y in range(PAD, h - PAD, 3):
        d.line([(PAD, y), (w - PAD, y)], fill=LCD_GRID)
    for r, row in enumerate(rows):
        for c, ch in enumerate(row.ljust(16)[:16]):
            x, y = PAD + c * CW, PAD + r * CH
            inv = (r, c) in inverse
            if inv:
                d.rectangle([x, y + 2, x + CW - 1, y + CH - 2], fill=LCD_FG)
            if ch != " ":
                d.text((x + CW / 2, y + CH / 2), ch, font=FONT_B if inv else FONT,
                       fill=LCD_BG if inv else LCD_FG, anchor="mm")
    img = Image.new("RGB", (w + 2 * BEZEL, h + 2 * BEZEL), (255, 255, 255))
    b = ImageDraw.Draw(img)
    b.rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius=26, fill=BEZEL_C, outline=BEZEL_EDGE, width=3)
    img.paste(lcd, (BEZEL, BEZEL))
    b.rectangle([BEZEL - 2, BEZEL - 2, BEZEL + w + 1, BEZEL + h + 1], outline=(20, 22, 26), width=2)
    # transparent corners outside the rounded bezel
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius=26, fill=255)
    img.putalpha(mask)
    return img


def render_menu(lines, selected=1):
    title, items = lines[0], lines[1:]
    rows = [title] + [it.replace(":", ":", 1) for it in items]
    rows += [""] * (8 - len(rows))
    inv = {(0, c) for c in range(len(title))}
    inv |= {(selected, 0), (selected, 1)}
    return render_rows(rows, inv)


class Capture(Machine):
    """Snapshots the screen right before every ClrHome too (input screens)."""

    def exec(self, pc, s):
        if s == "ClrHome" and any(ch != " " for row in self.screen for ch in row):
            self.snap("clear")
        return super().exec(pc, s)


def capture(target, events, seed=7):
    src = (ROOT / "source" / f"{target}.txt").read_text(encoding="utf-8").rstrip("\n")
    m = Capture(src, events, False, seed)
    try:
        m.run()
    except OutOfEvents:
        pass
    return m.snaps


def screens(snaps):
    out = []
    for why, rows in snaps:
        if why != "Menu" and (not out or rows != out[-1]):
            out.append(rows)
    return out


def menus(snaps):
    return [rows for why, rows in snaps if why == "Menu"]


ENTER = ("enter", None)


def M(x):
    return ("menu", x)


def I(x):
    return ("input", x)


def K(x):
    return ("key", x)


def save(img, name):
    img.save(OUT / f"{name}.png")
    print("wrote", name)


def grid(images, cols, gap=24):
    w, h = images[0].size
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * w + (cols - 1) * gap, rows * h + (rows - 1) * gap), (0, 0, 0, 0))
    for i, im in enumerate(images):
        sheet.paste(im, ((i % cols) * (w + gap), (i // cols) * (h + gap)), im)
    return sheet


# ---------------------------------------------------------------- captures
quad = capture("SAT", [ENTER, M("Math Solvers"), M("Quadratic"), I("2"), I("~4"), I("~3"), ENTER, ENTER, ENTER])
qs = screens(quad)
splash, quad_in, quad_res, quad_exact, quad_vertex = qs[0], qs[1], qs[2], qs[3], qs[4]
main_menu, solver_menu = menus(quad)[0], menus(quad)[1]

line = screens(capture("SAT", [ENTER, M("Math Solvers"), M("Line: 2 points"), I("1"), I("2"), I("4"), I("6"),
                               ENTER, ENTER]))
circle = screens(capture("SAT", [ENTER, M("Math Solvers"), M("Geometry/Stats"), M("Circle eqn"),
                                 I("1"), I("~6"), I("4"), I("~7"), ENTER]))
TCP = [ENTER, M("Trig Center")]
tri = screens(capture("SAT", TCP + [M("Right triangle"), I("1"), I("2"), I("0"), I("0"), ENTER, ENTER, ENTER]))
tri30 = screens(capture("SAT", TCP + [M("Right triangle"), I("0"), I("0"), I("10"), I("30"), ENTER, ENTER, ENTER]))
special = screens(capture("SAT", TCP + [M("Trig tools"), M("Special tri"), M("30-60-90"), M("Long leg x√(3)"), I("6"), ENTER]))
unit = screens(capture("SAT", TCP + [M("Unit circle"), M("Angle in deg"), I("150"), ENTER]))
cofn = screens(capture("SAT", TCP + [M("Trig tools"), M("Cofunction eqn"), I("2"), I("10"), I("3"), I("~5"),
                                     ENTER]))
anyt = screens(capture("SAT", TCP + [M("Any triangle"), I("13"), I("14"), I("15"), I("0"), I("0"), I("0"),
                                     I("0"), ENTER, ENTER, ENTER, ENTER]))
ssa = screens(capture("SAT", TCP + [M("Any triangle"), I("6"), I("10"), I("0"), I("30"), I("0"), I("0"),
                                    I("0")] + [ENTER] * 8))
tc_menu = menus(capture("SAT", TCP))[-1]
learn_menu = menus(capture("SAT", TCP + [M("Learn trig")]))[-1]
tools_menu = menus(capture("SAT", TCP + [M("Trig tools")]))[-1]
geo_menu = menus(capture("SAT", [ENTER, M("Math Solvers"), M("Geometry/Stats")]))[-1]


def pages(path, n):
    keys = [K(26)] * n
    out = []
    m = Capture((ROOT / "source" / "SAT.txt").read_text(encoding="utf-8").rstrip("\n"),
                [ENTER] + [M(p) for p in path] + keys, False, 7)
    orig = m.pop

    def hook(kind):
        if kind == "key":
            out.append(["".join(r) for r in m.screen])
        return orig(kind)
    m.pop = hook
    try:
        m.run()
    except OutOfEvents:
        pass
    return out


quad_pages = pages(["Math Formulas", "Quadratics"], 4)
circle_pages = pages(["Math Formulas", "More formulas", "Circles"], 4)
punct_pages = pages(["R&W Guide", "Punctuation"], 7)
trans_pages = pages(["R&W Guide", "Transitions"], 6)
strat_pages = pages(["Strategy/Help", "Test Strategy"], 5)
soh_pages = pages(["Trig Center", "Learn trig", "SOH CAH TOA"], 6)
uc_pages = pages(["Trig Center", "Learn trig", "Unit circle"], 7)
id_pages = pages(["Trig Center", "Learn trig", "Identities"], 5)
trap_pages = pages(["Trig Center", "Learn trig", "Traps + tips"], 6)
rw_menu = menus(capture("SAT", [ENTER, M("R&W Guide")]))[-1]
fa_menu = menus(capture("SAT", [ENTER, M("Math Formulas")]))[-1]


def quiz_math():
    shots = []
    state = {"n": 0}

    def ev(kind, m):
        if kind == "enter":
            return None
        if kind == "menu":
            title = m.snaps[-1][1][0]
            if title == "SAT TOOLKIT":
                return "Practice Quiz"
            return "Math (random)"
        if kind == "input":
            state["n"] += 1
            if state["n"] > 3:
                raise OutOfEvents()
            ans = m.vars["X"] if state["n"] != 2 else m.vars["X"] + 3
            typed = repr(int(ans) if ans == int(ans) else ans).replace("-", "~")
            rows = [list(r) for r in m.screen]
            for i, ch in enumerate(("answer=" + typed.replace("~", "⁻"))[:16]):
                rows[6][i] = ch
            shots.append(("q", ["".join(r) for r in rows]))
            return typed
        if kind == "key":
            shots.append(("fb", ["".join(r) for r in m.screen]))
            return 105
    src = (ROOT / "source" / "SAT.txt").read_text(encoding="utf-8").rstrip("\n")
    m = Capture(src, ev, False, 11)
    try:
        m.run()
    except OutOfEvents:
        pass
    return shots


def quiz_grammar():
    shots = []
    KEYS = {1: 92, 2: 93, 3: 94, 4: 82}
    state = {"phase": "a", "n": 0}

    def ev(kind, m):
        if kind == "enter":
            return None
        if kind == "menu":
            return "Practice Quiz" if m.snaps[-1][1][0] == "SAT TOOLKIT" else "Grammar"
        if kind == "key":
            if state["phase"] == "a":
                state["phase"] = "f"
                state["n"] += 1
                shots.append(("q", ["".join(r) for r in m.screen]))
                x = int(m.vars["X"])
                return KEYS[x if state["n"] != 2 else x % 4 + 1]
            state["phase"] = "a"
            shots.append(("fb", ["".join(r) for r in m.screen]))
            if state["n"] >= 3:
                raise OutOfEvents()
            return 105
    src = (ROOT / "source" / "SAT.txt").read_text(encoding="utf-8").rstrip("\n")
    m = Capture(src, ev, False, 5)
    try:
        m.run()
    except OutOfEvents:
        pass
    return shots


def quiz_trig(seed):
    shots = []
    state = {"n": 0}

    def ev(kind, m):
        if kind == "enter":
            return None
        if kind == "menu":
            return "Trig Center" if m.snaps[-1][1][0] == "SAT TOOLKIT" else "Trig quiz"
        if kind == "input":
            state["n"] += 1
            if state["n"] > 4:
                raise OutOfEvents()
            shots.append(("q", int(m.vars["Z"]), ["".join(r) for r in m.screen], m.vars["X"]))
            return repr(m.vars["X"] + (0 if state["n"] % 2 else 1)).replace("-", "~")
        if kind == "key":
            shots.append(("fb", int(m.vars["Z"]), ["".join(r) for r in m.screen], None))
            return 105
    src = (ROOT / "source" / "SAT.txt").read_text(encoding="utf-8").rstrip("\n")
    m = Capture(src, ev, False, seed)
    try:
        m.run()
    except OutOfEvents:
        pass
    return shots


def with_answer(rows, typed):
    rows = [list(r) for r in rows]
    for i, ch in enumerate(("answer=" + typed)[:16]):
        rows[6][i] = ch
    return ["".join(r) for r in rows]


# find a unit-circle question (exact answer typed with √) and a triangle-ratio one
tq_unit = tq_ratio = None
for seed in range(60):
    for i, (kind, z, rows, x) in enumerate(quiz_trig(seed)):
        if kind == "q" and z == 4 and tq_unit is None and abs(x) not in (0, 1, .5):
            tq_unit = (rows, seed, i)
        if kind == "q" and z == 1 and tq_ratio is None:
            tq_ratio = (rows, seed, i)
    if tq_unit and tq_ratio:
        break
tq_unit_fb = quiz_trig(tq_unit[1])[tq_unit[2] + 1][2]
tq_ratio_fb = quiz_trig(tq_ratio[1])[tq_ratio[2] + 1][2]

mq = quiz_math()
gq = quiz_grammar()

# ---------------------------------------------------------------- stills
save(render_rows(splash), "splash")
save(render_menu(main_menu), "main-menu")
save(render_menu(solver_menu), "solvers-menu")
save(render_menu(geo_menu), "geometry-menu")
save(render_menu(fa_menu), "formulas-menu")
save(render_menu(rw_menu), "rw-menu")
save(render_rows(quad_in), "quadratic-input")
save(render_rows(quad_res), "quadratic-roots")
save(render_rows(quad_exact), "quadratic-exact")
save(render_rows(quad_vertex), "quadratic-vertex")
save(render_rows(line[2]), "line-slope")
save(render_rows(line[3]), "line-distance")
save(render_rows(circle[2]), "circle")
save(render_menu(tc_menu), "trig-menu")
save(render_rows(anyt[1]), "any-triangle-input")
save(render_rows(anyt[2]), "any-triangle-sides")
save(render_rows(anyt[3]), "any-triangle-measures")
save(render_rows(anyt[4]), "any-triangle-sin-cos")
save(render_rows(anyt[5]), "any-triangle-tan")
save(render_rows(ssa[2]), "any-triangle-ssa-1")
save(render_rows(ssa[6]), "any-triangle-ssa-2")
save(render_menu(learn_menu), "trig-learn-menu")
save(render_menu(tools_menu), "trig-tools-menu")
save(render_rows(tri[1]), "trig-right-input")
save(render_rows(tri[2]), "trig-right-sides")
save(render_rows(tri[3]), "trig-right-ratios")
save(render_rows(tri30[2]), "trig-right-30-sides")
save(render_rows(tri30[3]), "trig-right-30-ratios")
save(render_rows(tri30[4]), "trig-right-30-notes")
save(render_rows(special[2]), "trig-special-30-60-90")
save(render_rows(unit[2]), "trig-unit-circle-150")
save(render_rows(cofn[2]), "trig-cofunction")
save(render_rows(soh_pages[0]), "trig-lesson-soh")
save(render_rows(uc_pages[1]), "trig-lesson-unit-table")
save(render_rows(uc_pages[3]), "trig-lesson-quadrants")
save(render_rows(id_pages[1]), "trig-lesson-cofunction")
save(render_rows(trap_pages[1]), "trig-lesson-trap")
save(render_rows(tq_unit[0]), "trig-quiz-question")
save(render_rows(tq_unit_fb), "trig-quiz-feedback")
save(render_rows(quad_pages[0]), "formula-quadratics")
save(render_rows(circle_pages[2]), "formula-circles")
save(render_rows(punct_pages[0]), "rw-punctuation")
save(render_rows(trans_pages[1]), "rw-transitions")
save(render_rows(strat_pages[0]), "strategy")
save(render_rows(mq[0][1]), "quiz-math-question")
save(render_rows(mq[1][1]), "quiz-math-correct")
save(render_rows(mq[3][1]), "quiz-math-wrong")
save(render_rows(gq[0][1]), "quiz-grammar-question")
save(render_rows(gq[1][1]), "quiz-grammar-feedback")

# contact sheets for the README
save(grid([render_rows(splash), render_menu(main_menu), render_menu(solver_menu)], 3), "sheet-menus")
save(grid([render_rows(quad_in), render_rows(quad_res), render_rows(quad_exact), render_rows(quad_vertex)], 2),
     "sheet-quadratic")
save(grid([render_rows(line[2]), render_rows(line[3]), render_rows(circle[2]), render_menu(geo_menu)], 2),
     "sheet-solvers")
save(grid([render_menu(tc_menu), render_rows(tri[1]), render_rows(tri[2]), render_rows(tri[3])], 2),
     "sheet-trig-right")
save(grid([render_rows(anyt[1]), render_rows(anyt[2]), render_rows(anyt[3]), render_rows(anyt[4])], 2),
     "sheet-any-triangle")
save(grid([render_rows(ssa[1]), render_rows(ssa[2]), render_rows(ssa[6]), render_rows(ssa[3])], 2),
     "sheet-any-triangle-ssa")
save(grid([render_rows(tri30[2]), render_rows(tri30[3]), render_rows(special[2]), render_rows(unit[2])], 2),
     "sheet-trig-exact")
save(grid([render_menu(learn_menu), render_rows(uc_pages[1]), render_rows(uc_pages[3]), render_rows(id_pages[1])], 2),
     "sheet-trig-learn")
save(grid([render_menu(tools_menu), render_rows(cofn[2]), render_rows(tq_ratio[0]), render_rows(tq_ratio_fb)], 2),
     "sheet-trig-tools-quiz")
save(grid([render_rows(quad_pages[0]), render_rows(circle_pages[2]), render_rows(punct_pages[0]),
           render_rows(trans_pages[1])], 2), "sheet-reference")
save(grid([render_rows(mq[0][1]), render_rows(mq[1][1]), render_rows(gq[0][1]), render_rows(gq[1][1])], 2),
     "sheet-quiz")

# ---------------------------------------------------------------- demo GIF
frames = []


def add(img, ms):
    frames.append((img, ms))


def typing(rows, first_input_row, n_inputs):
    """Frames revealing an input screen one answered prompt at a time."""
    out = []
    for k in range(n_inputs + 1):
        r = [row if i < first_input_row + k else " " * 16 for i, row in enumerate(rows)]
        out.append(r)
    return out


add(render_rows(splash), 1600)
for sel in (1,):
    add(render_menu(main_menu, sel), 1000)
for sel in (1,):
    add(render_menu(solver_menu, sel), 1000)
for r in typing(quad_in, 2, 3):
    add(render_rows(r), 600)
add(render_rows(quad_in), 600)
add(render_rows(quad_res), 2200)
add(render_rows(quad_exact), 2200)
add(render_rows(quad_vertex), 2200)
add(render_menu(main_menu, 2), 1000)
add(render_menu(tc_menu, 1), 1000)
for r in typing(anyt[1], 1, 7):
    add(render_rows(r), 400)
add(render_rows(anyt[2]), 2400)
add(render_rows(anyt[3]), 2400)
add(render_rows(anyt[4]), 2400)
add(render_menu(tc_menu, 2), 1000)
add(render_rows(tri30[2]), 2400)
add(render_rows(tri30[3]), 2400)
add(render_menu(tc_menu, 3), 1000)
add(render_rows(unit[2]), 2400)
add(render_menu(main_menu, 3), 1000)
add(render_menu(fa_menu, 2), 1000)
for p in quad_pages:
    add(render_rows(p), 1400)
add(render_menu(main_menu, 4), 1000)
add(render_menu(rw_menu, 1), 1000)
for p in punct_pages[:3]:
    add(render_rows(p), 1400)
add(render_menu(main_menu, 5), 1000)
add(render_rows(gq[0][1]), 2000)
add(render_rows(gq[1][1]), 2200)

bg = (255, 255, 255)
pal = []
for img, ms in frames:
    flat = Image.new("RGB", img.size, bg)
    flat.paste(img, (0, 0), img)
    pal.append(flat.convert("P", palette=Image.ADAPTIVE, colors=64))
pal[0].save(OUT / "demo.gif", save_all=True, append_images=pal[1:], duration=[ms for _, ms in frames],
            loop=0, optimize=True)
print("wrote demo.gif", len(frames), "frames")
