import sys
from pathlib import Path

from sim import Machine, OutOfEvents, TIError, render

SRC = Path(__file__).resolve().parent.parent / "source"
ENTER = ("enter", None)


def M(x):
    return ("menu", x)


def I(x):
    return ("input", x)


def K(x):
    return ("key", x)


def run(target, events, degree=False, seed=1):
    m = Machine((SRC / f"{target}.txt").read_text(encoding="utf-8").rstrip("\n"), events, degree, seed)
    err = None
    try:
        m.run()
    except OutOfEvents:
        pass
    except TIError as e:
        err = f"ERR {e} at line {m.cur}"
    return m, err


def show(title, m, err, last=None):
    print(f"\n=== {title} ===")
    snaps = m.snaps if last is None else m.snaps[-last:]
    print(render([s for s in snaps if s[0] != "Menu"]))
    for w in m.warnings:
        print("  WARN:", w)
    if err:
        print("  ", err)
    return err is None and not m.warnings


def solver(path, inputs, pauses, **kw):
    ev = [ENTER, M("Math Solvers")] + [M(p) for p in path] + [I(x) for x in inputs] + [ENTER] * pauses
    return run("SAT", ev, **kw)


ok = True
CASES = [
    ("Quadratic x²-2x-4", ["Quadratic"], ["1", "~2", "~4"], 3),
    ("Quadratic 2x²+3x-5", ["Quadratic"], ["2", "3", "~5"], 2),
    ("Quadratic 2x²-4x-3 (D=40)", ["Quadratic"], ["2", "~4", "~3"], 3),
    ("Quadratic -x²+6x-7", ["Quadratic"], ["~1", "6", "~7"], 3),
    ("Quadratic 3x²-12 (b=0)", ["Quadratic"], ["3", "0", "~12"], 2),
    ("Quadratic x²+2x+5 complex", ["Quadratic"], ["1", "2", "5"], 2),
    ("Quadratic 1.5x²+x-2 (non-int)", ["Quadratic"], ["1.5", "1", "~2"], 2),
    ("Quadratic a=0", ["Quadratic"], ["0", "4", "~6"], 1),
    ("System one sol", ["System 2x2"], ["2", "3", "12", "1", "~1", "1"], 1),
    ("System none", ["System 2x2"], ["1", "1", "2", "2", "2", "5"], 1),
    ("System infinite", ["System 2x2"], ["1", "1", "2", "2", "2", "4"], 1),
    ("Line (1,2)(4,6)", ["Line: 2 points"], ["1", "2", "4", "6"], 2),
    ("Line (0,0)(2,2)", ["Line: 2 points"], ["0", "0", "2", "2"], 2),
    ("Line (~1,3)(5,3) horiz", ["Line: 2 points"], ["~1", "3", "5", "3"], 2),
    ("Line vertical", ["Line: 2 points"], ["2", "1", "2", "7"], 2),
    ("Exp end value", ["Exponential", "Find end value"], ["1000", "5", "1", "10"], 1),
    ("Exp monthly decay", ["Exponential", "Find end value"], ["500", "~3", "12", "2"], 1),
    ("Exp find rate", ["Exponential", "Find rate %"], ["100", "200", "5"], 1),
    ("Exp find rate invalid", ["Exponential", "Find rate %"], ["0", "200", "5"], 1),
    ("% change", ["Percent", "% change"], ["80", "100"], 1),
    ("% change old=0", ["Percent", "% change"], ["0", "100"], 1),
    ("x% of y", ["Percent", "x% of y"], ["15", "80"], 1),
    ("x is ?% of y", ["Percent", "x is ?% of y"], ["12", "48"], 1),
    ("Undo % chg", ["Percent", "Undo a % chg"], ["90", "~25"], 1),
    ("Stacked", ["Percent", "Stacked %s"], ["20", "~20"], 1),
    ("Proportion", ["Percent", "Proportion"], ["3", "4", "9"], 1),
    ("Circle 1,-6,4,-12", ["Geometry/Stats", "Circle eqn"], ["1", "~6", "4", "~12"], 1),
    ("Circle r=2√2", ["Geometry/Stats", "Circle eqn"], ["1", "0", "0", "~8"], 1),
    ("Circle 2x²..", ["Geometry/Stats", "Circle eqn"], ["2", "8", "~4", "~8"], 1),
    ("Circle invalid", ["Geometry/Stats", "Circle eqn"], ["1", "0", "0", "5"], 1),
    ("Arc deg", ["Geometry/Stats", "Arc & sector", "Degrees"], ["6", "60"], 2),
    ("Arc rad", ["Geometry/Stats", "Arc & sector", "Radians"], ["3", "π/3"], 2),
    ("Stats", ["Geometry/Stats", "Mean/Median/SD"], ["{2,5,9,4}"], 2),
    ("Missing value", ["Geometry/Stats", "Missing value"], ["4", "12", "13"], 1),
    ("Deg->rad", ["Geometry/Stats", "Deg <-> Rad", "Deg -> Radians"], ["135"], 1),
    ("Rad->deg", ["Geometry/Stats", "Deg <-> Rad", "Rad -> Degrees"], ["π/6"], 1),
]
for title, path, inputs, pauses in CASES:
    m, err = solver(path, inputs, pauses)
    ok &= show(title, m, err)


sys.exit(0 if ok else 1)
