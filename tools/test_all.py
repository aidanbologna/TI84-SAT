"""Pagers, quizzes, and a random fuzz walk over all three targets."""
import random
import sys

from sim import Machine, OutOfEvents, TIError, render
from pathlib import Path
SRC = Path(__file__).resolve().parent.parent / "source"

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)

problems = []


def machine(target, events, seed=1, degree=False):
    return Machine((SRC / f"{target}.txt").read_text(encoding="utf-8").rstrip("\n"), events, degree, seed)


def go(target, m, label):
    try:
        m.run()
    except OutOfEvents:
        pass
    except TIError as e:
        problems.append(f"{target} {label}: ERR {e} at {m.cur}")
    for w in m.warnings:
        problems.append(f"{target} {label}: WARN {w}")


# ---------- every reference page ----------
PAGERS = {
    "SAT": [("Math Formulas", t) for t in ["Linear eqns", "Quadratics", "Exponents/Rads", "Exponential", "Functions"]]
    + [("Math Formulas", "More formulas", t) for t in ["Geometry", "Circles", "Triangles/Trig", "Statistics",
                                                        "Probability", "Percent/Units"]]
    + [("R&W Guide", t) for t in ["Punctuation", "Grammar", "Transitions", "Notes Qs", "Reading Qs", "R&W Strategy"]]
    + [("Strategy/Help", "Test Strategy"), ("Strategy/Help", "How To Use")]
    + [("Trig Center", "Learn trig", t) for t in ["SOH CAH TOA", "Special tri", "Unit circle", "Radians/arcs",
                                                   "Identities", "Traps + tips"]]
    + [("Trig Center", "Unit circle", "Values table")],
}
HELP = [("Test Strategy",), ("How To Use",)]
PAGERS["SATMATH"] = [p for p in PAGERS["SAT"] if p[0] == "Math Formulas"] + HELP
PAGERS["SATRW"] = [p for p in PAGERS["SAT"] if p[0] == "R&W Guide"] + HELP
PAGERS["SATTRIG"] = [p[1:] for p in PAGERS["SAT"] if p[0] == "Trig Center"]

page_shots = []
for target, paths in PAGERS.items():
    for path in paths:
        state = {"menus": 0, "keys": 0}
        script = list(path)

        def ev(kind, m, script=script, state=state):
            if kind == "enter":
                return None
            if kind == "menu":
                state["menus"] += 1
                if script:
                    return script.pop(0)
                raise OutOfEvents()  # back at a menu: pager exited
            if kind == "key":
                state["keys"] += 1
                if state["keys"] > 12:
                    raise TIError("pager never exits")
                # left once on page 1 (should stay), then right through
                return 24 if state["keys"] == 1 else 26
        m = machine(target, ev)
        orig_get = m.pop

        def snap_on_key(kind, m=m, orig=orig_get):
            if kind == "key":
                m.snap(f"page")
            return orig(kind)
        m.pop = snap_on_key
        go(target, m, "/".join(path))
        if target == "SAT":
            page_shots.append(("/".join(path), [s for s in m.snaps if s[0] == "page"]))

with open(OUT / "pages_out.txt", "w", encoding="utf-8") as f:
    for title, snaps in page_shots:
        f.write(f"## {title}\n")
        seen = []
        for _, rows in snaps:
            if rows not in seen:
                seen.append(rows)
        for k in range(0, len(seen), 4):
            group = seen[k:k + 4]
            for r in range(8):
                f.write("   ".join("|" + g[r] + "|" for g in group) + "\n")
            f.write("\n")

# ---------- math quiz: answer right, then wrong, many questions ----------
all_types = {}
for target in ("SAT", "SATMATH"):
    for seed in range(5):
        n = {"q": 0}
        types = set()

        def ev(kind, m, n=n, types=types):
            if kind == "enter":
                return None
            if kind == "menu":
                if m.snaps[-1][1][0] in ("SAT TOOLKIT", "SAT MATH"):
                    if n["q"]:
                        raise OutOfEvents()
                    return "Practice Quiz"
                if n["q"] >= 40:
                    raise OutOfEvents()
                return "Math (random)"
            if kind == "input":
                n["q"] += 1
                types.add(int(m.vars["Z"]))
                m.snap(f"question type {int(m.vars['Z'])}")
                x = m.vars["X"]
                return repr(x if n["q"] % 3 else x + 1).replace("-", "~")
            if kind == "key":
                return 105 if n["q"] < 40 else 45
        m = machine(target, ev, seed=seed)
        go(target, m, f"math quiz seed {seed}")
        all_types.setdefault(target, set()).update(types)
        final = [s for s in m.snaps if s[0] == "Pause"][-1][1]
        if seed == 0 and target == "SAT":
            qs = {}
            for why, rows in m.snaps:
                if why.startswith("question") and why not in qs:
                    qs[why] = rows
            with open(OUT / "quiz_out.txt", "w", encoding="utf-8") as f:
                for why in sorted(qs):
                    f.write(why + "\n" + "\n".join("|" + r + "|" for r in qs[why]) + "\n")
                f.write("FINAL\n" + "\n".join("|" + r + "|" for r in final) + "\n")
        exp_score = 40 - 40 // 3
        if f"{exp_score}/40" not in "".join(final).replace(" ", ""):
            problems.append(f"{target} math quiz seed {seed}: final screen {final}")

for target, types in all_types.items():
    if types != set(range(1, 11)):
        problems.append(f"{target} math quiz: only saw types {sorted(types)}")

# ---------- trig quiz ----------
trig_types = set()
for target in ("SAT", "SATTRIG"):
    for seed in range(4):
        n = {"q": 0}

        def ev(kind, m, n=n):
            if kind == "enter":
                return None
            if kind == "menu":
                title = m.snaps[-1][1][0].upper()
                if n["q"]:
                    raise OutOfEvents()  # back at a menu after the final score
                if title == "SAT TOOLKIT":
                    return "Trig Center"
                return "Trig quiz"
            if kind == "input":
                n["q"] += 1
                trig_types.add(int(m.vars["Z"]))
                x = m.vars["X"]
                return repr(x if n["q"] % 4 else x + 1).replace("-", "~")
            if kind == "key":
                return 105 if n["q"] < 40 else 45
        m = machine(target, ev, seed=seed, degree=bool(seed % 2))
        go(target, m, f"trig quiz seed {seed}")
        final = [s for s in m.snaps if s[0] == "Pause"][-1][1]
        if "30/40" not in "".join(final).replace(" ", ""):
            problems.append(f"{target} trig quiz seed {seed}: final screen {final}")
if trig_types != set(range(1, 11)):
    problems.append(f"trig quiz: only saw types {sorted(trig_types)}")

# ---------- grammar quiz ----------
KEYS = {1: 92, 2: 93, 3: 94, 4: 82}
for target in ("SAT", "SATRW"):
    n = {"q": 0, "phase": "answer"}
    seen_q = set()

    def ev(kind, m, n=n, seen_q=seen_q):
        if kind == "enter":
            return None
        if kind == "menu":
            title = m.snaps[-1][1][0].upper()
            if title in ("SAT TOOLKIT", "SAT READ+WRITE"):
                if n["q"]:
                    raise OutOfEvents()
                return "Practice Quiz" if target == "SAT" else "Grammar Quiz"
            if n["q"]:
                return "Main Menu"
            return "Grammar" if target == "SAT" else "Start quiz"
        if kind == "key":
            if n["phase"] == "answer":
                n["phase"] = "next"
                n["q"] += 1
                seen_q.add(int(m.vars["Q"]))
                m.snap(f"gq {int(m.vars['Q'])}")
                x = int(m.vars["X"])
                return KEYS[x if n["q"] % 2 else (x % 4) + 1]
            n["phase"] = "answer"
            m.snap(f"gf {int(m.vars['Q'])}")
            return 105 if n["q"] < 120 else 45
    m = machine(target, ev, seed=3)
    go(target, m, "grammar quiz")
    if len(seen_q) != 18:
        problems.append(f"{target} grammar: saw {len(seen_q)} questions")
    if target == "SAT":
        with open(OUT / "grammar_out.txt", "w", encoding="utf-8") as f:
            done = set()
            for why, rows in m.snaps:
                key = why.split()[1] if why[:2] in ("gq", "gf") else None
                if key and (why, key) not in done:
                    done.add((why, key))
            shots = {}
            for why, rows in m.snaps:
                if why[:2] in ("gq", "gf"):
                    shots.setdefault(why, rows)
            for qn in range(1, 19):
                a, b = shots.get(f"gq {qn}"), shots.get(f"gf {qn}")
                f.write(f"Q{qn}\n")
                for r in range(8):
                    f.write("|" + a[r] + "|   |" + b[r] + "|\n")
        final = [s for s in m.snaps if s[0] == "Pause"][-1][1]
        if "60/120" not in "".join(final).replace(" ", ""):
            problems.append(f"grammar final {final}")

# ---------- fuzz: random walk through everything ----------
POOL = ["0", "1", "2", "~3", "5", "1/2", "~2/3", "10", "100", "~100", "7", "3.5", "π", "~1", "12"]
LISTS = ["{1}", "{2,5,9}", "{3,3,3}", "{~4,0,10,2}"]
for target in TARGETS if (TARGETS := ["SAT", "SATMATH", "SATTRIG", "SATRW"]) else []:
    for seed in range(150):
        r = random.Random(seed)
        budget = {"n": 0}

        def ev(kind, m, r=r, budget=budget):
            budget["n"] += 1
            if budget["n"] > 400:
                raise OutOfEvents()
            if kind == "enter":
                return None
            if kind == "menu":
                items = m.snaps[-1][1][1:]
                choice = r.randint(1, len(items))
                if items[choice - 1].endswith("Quit") and r.random() < 0.9:
                    choice = 1
                return choice
            if kind == "input":
                if m.cur[1].endswith("L₆"):
                    return r.choice(LISTS)
                return r.choice(POOL)
            if kind == "key":
                return r.choice([24, 25, 26, 34, 105, 105, 45, 92, 93, 94, 82, 0])
        m = machine(target, ev, seed=seed, degree=bool(seed % 2))
        go(target, m, f"fuzz {seed}")

print(f"{len(problems)} problems")
for p in sorted(set(problems)):
    print(" ", p)
sys.exit(1 if problems else 0)
