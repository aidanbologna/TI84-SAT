"""Trig Center cases with known answers: checks the exact text that appears on screen."""
import sys
from pathlib import Path

from sim import Machine, OutOfEvents, TIError, render

SRC = Path(__file__).resolve().parent.parent / "source"
ENTER = ("enter", None)
VERBOSE = "-v" in sys.argv


def M(x):
    return ("menu", x)


def I(x):
    return ("input", x)


def run(target, events, degree=False):
    m = Machine((SRC / f"{target}.txt").read_text(encoding="utf-8").rstrip("\n"), events, degree, 1)
    err = None
    try:
        m.run()
    except OutOfEvents:
        pass
    except TIError as e:
        err = f"ERR {e} at {m.cur}"
    return m, err


def trig(path, inputs, pauses, target="SAT", **kw):
    first = [M("Trig Center")] if target == "SAT" else []
    ev = [ENTER] + first + [M(p) for p in path] + [I(x) for x in inputs] + [ENTER] * pauses
    return run(target, ev, **kw)


# (title, menu path, inputs, pauses, [text that must appear on the screens])
CASES = [
    ("Right tri 3,4 legs", ["Right triangle"], ["3", "4", "0", "0"], 3,
     ["a=3", "b=4", "c=5", "angle A=36.8699", "area=6", "sin A=3/5", "cos A=4/5", "tan A=3/4",
      "tan B=4/3", "Pythag. triple!"]),
    ("Right tri legs 1,2 (radicals)", ["Right triangle"], ["1", "2", "0", "0"], 3,
     ["c=√(5)", "sin A=√(5)/5", "cos A=2√(5)/5", "tan A=1/2", "area=1"]),
    ("Right tri hyp 10, angle 30", ["Right triangle"], ["0", "0", "10", "30"], 3,
     ["a=5", "b=5√(3)", "c=10", "angle A=30", "sin A=1/2", "cos A=√(3)/2", "tan A=√(3)/3",
      "area=25√(3)/2", "30-60-90 tri!"]),
    ("Right tri leg 7, angle 45", ["Right triangle"], ["7", "0", "0", "45"], 3,
     ["b=7", "c=7√(2)", "sin A=√(2)/2", "45-45-90 tri!"]),
    ("Right tri leg b=4, angle 37 (decimal)", ["Right triangle"], ["0", "4", "0", "37"], 3,
     ["angle A=37", "a=3.01"]),
    ("Right tri b=5 c=13", ["Right triangle"], ["0", "5", "13", "0"], 3,
     ["a=12", "sin A=12/13", "cos A=5/13", "tan A=12/5"]),
    ("Right tri invalid", ["Right triangle"], ["5", "0", "3", "0"], 1, ["NEED 2 SIDES, OR"]),
    ("Right tri DEGREE mode", ["Right triangle"], ["0", "0", "10", "30"], 3, ["a=5", "b=5√(3)"]),
    ("30-60-90 short 4", ["Trig tools", "Special tri", "30-60-90", "Short leg  x"], ["4"], 1,
     ["short=4", "long =4√(3)", "hyp  =8", "area =8√(3)"]),
    ("30-60-90 long 6", ["Trig tools", "Special tri", "30-60-90", "Long leg x√(3)"], ["6"], 1,
     ["short=2√(3)", "long =6", "hyp  =4√(3)", "area =6√(3)"]),
    ("30-60-90 hyp 4√(3)", ["Trig tools", "Special tri", "30-60-90", "Hypotenuse 2x"], ["4√(3)"], 1,
     ["short=2√(3)", "long =6", "hyp  =4√(3)"]),
    ("45-45-90 leg 5", ["Trig tools", "Special tri", "45-45-90", "Leg  x"], ["5"], 1,
     ["legs =5", "hyp  =5√(2)", "area =25/2"]),
    ("45-45-90 hyp 10", ["Trig tools", "Special tri", "45-45-90", "Hyp  x√(2)"], ["10"], 1,
     ["legs =5√(2)", "hyp  =10", "area =25"]),
    ("Unit circle 150", ["Unit circle", "Angle in deg"], ["150"], 1,
     ["angle=150", "rad/π=5/6", "quadrant 2", "ref angle=30", "sin=1/2", "cos=-√(3)/2",
      "tan=-√(3)/3", "sin+ cos- tan-"]),
    ("Unit circle 225", ["Unit circle", "Angle in deg"], ["225"], 1,
     ["quadrant 3", "ref angle=45", "sin=-√(2)/2", "cos=-√(2)/2", "tan=1", "sin- cos- tan+"]),
    ("Unit circle 90", ["Unit circle", "Angle in deg"], ["90"], 1,
     ["on an axis", "sin=1", "cos=0", "tan=undefined", "tan?"]),
    ("Unit circle -60", ["Unit circle", "Angle in deg"], ["~60"], 1,
     ["angle=300", "rad/π=5/3", "quadrant 4", "ref angle=60", "sin=-√(3)/2", "cos=1/2"]),
    ("Unit circle 780", ["Unit circle", "Angle in deg"], ["780"], 1, ["angle=60", "sin=√(3)/2"]),
    ("Unit circle rad 7π/6", ["Unit circle", "Angle in rad"], ["7π/6"], 1,
     ["angle=210", "rad/π=7/6", "sin=-1/2", "cos=-√(3)/2", "tan=√(3)/3"]),
    ("Unit circle 37 (decimal)", ["Unit circle", "Angle in deg"], ["37"], 1, ["quadrant 1", "sin=.601815"]),
    ("Cofunction", ["Trig tools", "Cofunction eqn"], ["2", "10", "3", "~5"], 1, ["17", "44", "46"]),
    ("Law of sines", ["Trig tools", "Law of sines"], ["30", "60", "5"], 1, ["90", "8.660254", "10", "21.650635"]),
    ("Law of sines invalid", ["Trig tools", "Law of sines"], ["100", "90", "5"], 1, ["ANGLES MUST SUM"]),
    ("Law of cosines SAS", ["Trig tools", "Law of cosines", "2 sides+angle"], ["3", "4", "90"], 1,
     ["5", "36.8699", "53.1301", "6"]),
    ("Law of cosines SSS", ["Trig tools", "Law of cosines", "3 sides"], ["5", "5", "5"], 1,
     ["60", "10.825318"]),
    ("Law of cosines bad", ["Trig tools", "Law of cosines", "3 sides"], ["1", "2", "5"], 1, ["NOT A VALID"]),
    ("Similar tri", ["Trig tools", "Similar tri"], ["3", "6", "5"], 1, ["2", "10", "4", "8"]),
]

# Any triangle: inputs are side a, b, c, angle A, B, C, area (0 = unknown); 4 pages per solution
AT = ["Any triangle"]
CASES += [
    ("ANY SSS 3-4-5", AT, ["3", "4", "5", "0", "0", "0", "0"], 4,
     ["TRIANGLE", "a=3", "b=4", "c=5", "angle A=36.8699", "angle C=90", "right", "scalene", "area=6", "perim=12",
      "h(a)=4", "h(b)=3", "h(c)=12/5", "circumR=5/2", "inradius=1", "sin A=3/5", "cos A=4/5", "tan A=3/4",
      "tan C=undefined", "=5"]),
    ("ANY SSS equilateral 5", AT, ["5", "5", "5", "0", "0", "0", "0"], 4,
     ["angle A=60", "acute", "equilat.", "area=25√(3)/4", "h(a)=5√(3)/2", "circumR=5√(3)/3",
      "inradius=5√(3)/6", "sin A=√(3)/2", "cos A=1/2", "tan A=√(3)"]),
    ("ANY SSS 13-14-15", AT, ["13", "14", "15", "0", "0", "0", "0"], 4,
     ["area=84", "perim=42", "h(b)=12", "sin A=4/5", "cos A=3/5", "sin B=56/65", "inradius=4", "circumR=65/8"]),
    ("ANY SSS obtuse isosceles", AT, ["5", "5", "8", "0", "0", "0", "0"], 4,
     ["obtuse", "isosceles", "area=12", "cos C=-7/25"]),
    ("ANY SAS", AT, ["5", "7", "0", "0", "0", "60", "0"], 4,
     ["c=√(39)", "angle C=60", "area=35√(3)/4"]),
    ("ANY ASA", AT, ["0", "0", "10", "30", "45", "0", "0"], 4,
     ["angle C=105", "obtuse", "a=5.176", "b=7.320"]),
    ("ANY AAS 30-60 a=1", AT, ["1", "0", "0", "30", "60", "0", "0"], 4,
     ["a=1", "b=√(3)", "c=2", "angle C=90", "right", "area=√(3)/2"]),
    ("ANY SSA two solutions", AT, ["6", "10", "0", "30", "0", "0", "0"], 8,
     ["SOLUTION 1 OF 2", "SOLUTION 2 OF 2", "angle B=56.4427", "angle B=123.5573", "ENTER: next sol."]),
    ("ANY SSA one solution", AT, ["10", "6", "0", "30", "0", "0", "0"], 4,
     ["TRIANGLE", "angle B=17.4576"]),
    ("ANY SSA right", AT, ["5", "10", "0", "30", "0", "0", "0"], 4,
     ["TRIANGLE", "angle B=90", "c=5√(3)"]),
    ("ANY SSA none", AT, ["2", "10", "0", "30", "0", "0", "0"], 1, ["NO TRIANGLE FITS"]),
    ("ANY AAA shape", AT, ["0", "0", "0", "30", "60", "90", "0"], 4,
     ["SIDES = RATIOS", "a=1", "b=√(3)", "c=2"]),
    ("ANY AA + area", AT, ["0", "0", "0", "30", "60", "0", "8√(3)"], 4,
     ["a=4", "b=4√(3)", "c=8", "area=8√(3)"]),
    ("ANY 2 sides + area (2 sol)", AT, ["4", "6", "0", "0", "0", "0", "6"], 8,
     ["SOLUTION 1 OF 2", "angle C=30", "angle C=150", "area=6"]),
    ("ANY 2 sides + area right", AT, ["3", "4", "0", "0", "0", "0", "6"], 4, ["TRIANGLE", "c=5", "angle C=90"]),
    ("ANY side + adj angle + area", AT, ["4", "0", "0", "0", "90", "0", "6"], 4, ["a=4", "b=5", "c=3"]),
    ("ANY side + opp angle + area", AT, ["4", "0", "0", "90", "0", "0", "6"], 1, ["NOT ENOUGH INFO"]),
    ("ANY not enough", AT, ["5", "0", "0", "0", "0", "0", "0"], 1, ["NOT ENOUGH INFO"]),
    ("ANY bad angles", AT, ["0", "0", "5", "100", "90", "0", "0"], 1, ["ANGLES MUST ADD"]),
    ("ANY bad sides", AT, ["1", "2", "5", "0", "0", "0", "0"], 1, ["NO TRIANGLE FITS"]),
    ("ANY DEGREE mode SAS", AT, ["5", "7", "0", "0", "0", "60", "0"], 4, ["c=√(39)"]),
]

ok = True
for title, path, inputs, pauses, expect in CASES:
    m, err = trig(path, inputs, pauses, degree="DEGREE" in title)
    text = "\n".join("\n".join(rows) for _, rows in m.snaps if _ != "Menu")
    flat = text.replace(" ", "")
    missing = [e for e in expect if e.replace(" ", "") not in flat]
    bad = err or missing or m.warnings
    if bad or VERBOSE:
        print(f"\n=== {title} ===")
        print(render([s for s in m.snaps if s[0] != "Menu"][1:]))
    if bad:
        ok = False
        print("  FAIL:", err or "", "missing:", missing, "warnings:", m.warnings)
print(f"{len(CASES)} trig cases:", "all passed" if ok else "FAILURES")

# fuzz the Any-triangle solver with random combinations of known values
import random  # noqa: E402

POOL = ["0", "0", "0", "1", "3", "5", "7.5", "10", "4√(3)", "30", "45", "60", "90", "120", "150", "~4", "200"]
crashes = 0
for seed in range(400):
    r = random.Random(seed)
    typed = [r.choice(POOL) for _ in range(7)]
    state = {"menus": 0, "inputs": list(typed)}

    def ev(kind, m, state=state):
        if kind == "enter":
            return None
        if kind == "menu":
            state["menus"] += 1
            if state["menus"] == 1:
                return "Trig Center"
            if state["menus"] == 2:
                return "Any triangle"
            raise OutOfEvents()  # solver finished, back at the menu
        if kind == "input":
            return state["inputs"].pop(0)
        raise TIError(f"unexpected {kind}")
    m, err = run("SAT", ev, degree=bool(seed % 2))
    if err or m.warnings or state["menus"] < 3:
        crashes += 1
        ok = False
        print("FUZZ FAIL seed", seed, typed, err, m.warnings)
print("any-triangle fuzz: 400 runs,", crashes, "failures")

# the older-model SATTRIG build goes straight to the trig menu
m, err = trig(["Right triangle"], ["1", "2", "0", "0"], 3, target="SATTRIG")
flat = "".join("".join(r) for _, r in m.snaps).replace(" ", "")
if err or "COSA=2√(5)/5" not in flat:
    ok = False
    print("SATTRIG right triangle FAIL", err)
sys.exit(0 if ok else 1)
