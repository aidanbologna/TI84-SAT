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
    ("30-60-90 short 4", ["Special tri", "30-60-90", "Short leg  x"], ["4"], 1,
     ["short=4", "long =4√(3)", "hyp  =8", "area =8√(3)"]),
    ("30-60-90 long 6", ["Special tri", "30-60-90", "Long leg x√(3)"], ["6"], 1,
     ["short=2√(3)", "long =6", "hyp  =4√(3)", "area =6√(3)"]),
    ("30-60-90 hyp 4√(3)", ["Special tri", "30-60-90", "Hypotenuse 2x"], ["4√(3)"], 1,
     ["short=2√(3)", "long =6", "hyp  =4√(3)"]),
    ("45-45-90 leg 5", ["Special tri", "45-45-90", "Leg  x"], ["5"], 1,
     ["legs =5", "hyp  =5√(2)", "area =25/2"]),
    ("45-45-90 hyp 10", ["Special tri", "45-45-90", "Hyp  x√(2)"], ["10"], 1,
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

# the older-model SATTRIG build goes straight to the trig menu
m, err = trig(["Right triangle"], ["1", "2", "0", "0"], 3, target="SATTRIG")
flat = "".join("".join(r) for _, r in m.snaps).replace(" ", "")
if err or "COSA=2√(5)/5" not in flat:
    ok = False
    print("SATTRIG right triangle FAIL", err)
sys.exit(0 if ok else 1)
