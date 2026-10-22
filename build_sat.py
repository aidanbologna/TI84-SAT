"""
Builds SAT.8xp, a TI-84 Plus / TI-84 Plus CE SAT study + solver program.

All screen text and program logic lives in this file. Run:
    python build_sat.py
Outputs SAT.8xp (load with TI Connect CE) and SAT_source.txt (readable listing).

Conventions in the TI-BASIC templates below:
  @NAME    -> a 2-char label, auto-assigned
  W(X)     -> width in characters of integer variable X when printed by Output(
  ~        -> negation (the (-) key), '-' is subtraction
  π        -> the pi token, in code and in strings
Every screen is designed for the 16x8 home screen so it works on all TI-84s.
"""

import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent

# Build targets. SAT is the full program for the TI-84 Plus CE (lots of RAM).
# SATMATH + SATRW split the content for the older TI-84 Plus / Silver Edition,
# which only has ~24 KB of RAM, and use uppercase text (half the bytes).
TARGETS = {
    "SAT": dict(upper=False, sections={"core", "solvers", "formulas", "rw", "strategy",
                                       "quizmath", "quizgrammar", "quizfinal"}),
    "SATMATH": dict(upper=True, sections={"core", "solvers", "formulas", "strategy",
                                          "quizmath", "quizfinal"}),
    "SATRW": dict(upper=True, sections={"core", "rw", "strategy", "quizgrammar", "quizfinal"}),
}
PROG_NAME = sys.argv[1] if len(sys.argv) > 1 else "SAT"
CFG = TARGETS[PROG_NAME]

code: list[str] = []
PROBLEMS: list[str] = []
_labels: dict[str, str] = {}
_POOL = [a + b for a in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" for b in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"]


def lb(name: str) -> str:
    if name not in _labels:
        _labels[name] = _POOL[len(_labels)]
    return _labels[name]


def width(v: str) -> str:
    return f"(1+({v}<0)+int(log(abs({v})+not({v}))))"


def T(template: str) -> None:
    """Append a TI-BASIC template, expanding @labels and W(X)."""
    for line in template.strip("\n").split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        line = re.sub(r"@(\w+)", lambda m: lb(m.group(1)), line)
        line = re.sub(r"W\(([A-Zθ])\)", lambda m: width(m.group(1)), line)
        code.append(line)


def section(name: str) -> None:
    """Following lines belong to this section (dropped if the target excludes it)."""
    code.append(f"#SECTION {name}")


def q(s: str) -> str:
    assert '"' not in s and "→" not in s, s
    return '"' + s + '"'


def menu(name: str, title: str, items: list[tuple[str, str]]) -> None:
    assert len(title) <= 16 and 1 <= len(items) <= 7, title
    for text, _ in items:
        assert len(text) <= 14, text
    parts = ",".join(f"{q(t)},{lb(n)}" for t, n in items)
    T(f"Lbl @{name}")
    code.append(f"Menu({q(title)},{parts})")


def out_line(row: int, text: str) -> str | None:
    """Output( a line of page text; leading spaces become a column offset."""
    stripped = text.lstrip(" ")
    if not stripped:
        return None
    col = 1 + len(text) - len(stripped)
    if col - 1 + disp_len(stripped) > 16:
        PROBLEMS.append(f"too wide: {text!r}")
    return f"Output({row},{col},{q(stripped)})"


def disp_len(s: str) -> int:
    return len(s)  # every char we use (incl. "√(" as 2 chars) is one display cell


def pager(name: str, title: str, pages: list[list[str]], back: str) -> None:
    """A topic: pages of up to 6 lines, browsed with arrows, CLEAR exits."""
    n = len(pages)
    assert 1 <= n <= 9
    assert len(title) <= (12 if n > 1 else 16), title
    T(f"""
Lbl @{name}
1→P
Repeat K=45 or P>{n}
ClrHome
""")
    code.append(f"Output(1,1,{q(title)})")
    if n > 1:
        code.append("Output(1,14,P)")
        code.append(f'Output(1,15,"/{n}")')
        code.append('Output(8,1,"<- -> CLEAR:menu")')
    else:
        code.append('Output(8,1,"ENTER: back")')
    for i, page in enumerate(pages, 1):
        assert len(page) <= 6, (title, i, page)
        lines = [out_line(r, t) for r, t in enumerate(page, 2)]
        lines = [l for l in lines if l]
        if n > 1:
            code.append(f"If P={i}")
            code.append("Then")
        code.extend(lines)
        if n > 1:
            code.append("End")
    T(f"""
Repeat K
getKey→K
End
P+(K=26 or K=34 or K=105)-(P>1)(K=24 or K=25)→P
End
Goto @{back}
""")


def radical(row: int, n: str, col: int = 1, prefix: str = "=") -> None:
    """If integer n is not a perfect square, Output its simplified radical U√(V)."""
    T(f"""
If not(fPart({n})) and fPart(√({n}))
Then
int(√({n}))→U
While fPart({n}/U²)
U-1→U
End
{n}/U²→V
Output({row},{col},"{prefix}")
{col + len(prefix)}→θ
If U≠1:Then:Output({row},θ,U):θ+W(U)→θ:End
Output({row},θ,"√(")
Output({row},θ+2,V)
Output({row},θ+2+W(V),")")
End
""")


def seg_row(row: int, segs: list) -> None:
    """Print a mix of text and integer variables on one row (for quiz questions).
    segs items:
      "text"            literal text
      ("n", V)          number as-is (TI shows negatives as raised minus, fine for points)
      ("c", V, "x")     leading coefficient: -x, 3x, -3x (1 is hidden when a suffix follows)
      ("t", V, "x")     later term: +3x, -x, skipped entirely when V=0"""
    T("1→θ")
    for s in segs:
        if isinstance(s, str):
            code.append(f"Output({row},θ,{q(s)})")
            code.append(f"θ+{disp_len(s)}→θ")
            continue
        kind, v, *rest = s
        if kind == "n":
            T(f"Output({row},θ,{v})")
            T(f"θ+W({v})→θ")
            continue
        suffix = rest[0] if rest else ""
        a = f"abs({v})"
        body = []
        if kind == "t":
            body.append(f'If {v}>0:Then:Output({row},θ,"+"):θ+1→θ:End')
        body.append(f'If {v}<0:Then:Output({row},θ,"-"):θ+1→θ:End')
        num = f"Output({row},θ,{a}):θ+{width(a)}→θ"
        body.append(f"If {a}≠1:Then:{num}:End" if suffix else num)
        if suffix:
            body.append(f"Output({row},θ,{q(suffix)}):θ+{disp_len(suffix)}→θ")
        if kind == "t":
            code.append(f"If {v}")
            code.append("Then")
            code.extend(body)
            code.append("End")
        else:
            code.extend(body)


# =====================================================================
# SPLASH + MAIN MENU (differs per target)
# =====================================================================
SPLASH = {"SAT": "|  Math + R&W  |", "SATMATH": "|  Math        |", "SATRW": "|  Read+Write  |"}
section("core")
T(f"""
ClrHome
Output(1,1,"+--------------+")
Output(2,1,"|  SAT TOOLKIT |")
Output(3,1,"{SPLASH[PROG_NAME]}")
Output(4,1,"| Digital  SAT |")
Output(5,1,"+--------------+")
Output(7,3,"press ENTER")
Pause
""")

if PROG_NAME == "SAT":
    menu("MM", "SAT TOOLKIT", [
        ("Math Solvers", "MS"),
        ("Math Formulas", "FA"),
        ("R&W Guide", "RW"),
        ("Practice Quiz", "PQ"),
        ("Test Strategy", "TS"),
        ("How To Use", "HU"),
        ("Quit", "QT"),
    ])
    menu("PQ", "PRACTICE QUIZ", [
        ("Math (random)", "QM"),
        ("Grammar", "QG"),
        ("Main Menu", "MM"),
    ])
elif PROG_NAME == "SATMATH":
    menu("MM", "SAT MATH", [
        ("Math Solvers", "MS"),
        ("Math Formulas", "FA"),
        ("Practice Quiz", "PQ"),
        ("Test Strategy", "TS"),
        ("How To Use", "HU"),
        ("Quit", "QT"),
    ])
    menu("PQ", "PRACTICE QUIZ", [
        ("Math (random)", "QM"),
        ("Main Menu", "MM"),
    ])
else:
    menu("MM", "SAT READ+WRITE", [
        ("R&W Guide", "RW"),
        ("Grammar Quiz", "PQ"),
        ("Test Strategy", "TS"),
        ("How To Use", "HU"),
        ("Quit", "QT"),
    ])
    menu("PQ", "GRAMMAR QUIZ", [
        ("Start quiz", "QG"),
        ("Main Menu", "MM"),
    ])

# =====================================================================
# MATH SOLVERS
# =====================================================================
section("solvers")
menu("MS", "MATH SOLVERS", [
    ("Quadratic", "QD"),
    ("System 2x2", "SY"),
    ("Line: 2 points", "LN"),
    ("Exponential", "EX"),
    ("Percent", "PC"),
    ("Geometry/Stats", "GM"),
    ("Main Menu", "MM"),
])

# ---------- Quadratic ----------
T("""
Lbl @QD
ClrHome
Disp "QUADRATIC","ax²+bx+c=0"
Input "a=",A
Input "b=",B
Input "c=",C
If not(A)
Goto @QL
B²-4AC→D
~B/(2A)→H
AH²+BH+C→K
ClrHome
Disp "DISCRIMINANT"
Disp D►Frac
If D≥0
Then
If D:Then:Disp "2 REAL ROOTS":Else:Disp "1 REAL ROOT":End
√(D)/(2abs(A))→R
Disp "x="
Disp H-R►Frac
If D
Then
Disp "x="
Disp H+R►Frac
End
Else
√(~D)/(2abs(A))→R
Disp "NONREAL: p+/-qi"
Disp "p="
Disp H►Frac
Disp "q="
Disp R►Frac
End
Pause
# exact radical form for integer coefficients
If D>0 and fPart(√(abs(D))) and not(abs(fPart(A))+abs(fPart(B))+abs(fPart(C)))
Then
int(√(D))→U
While fPart(D/U²)
U-1→U
End
D/U²→V
~B→P
2A→S
gcd(U,abs(S))→G
If P:gcd(G,abs(P))→G
P/G→P
U/G→Q
S/G→S
If S<0:Then:~P→P:~S→S:End
ClrHome
Output(1,1,"EXACT ROOTS:")
For(J,0,1)
3J+2→R
Output(R,1,"x=")
3→θ
If S≠1:Then:Output(R+int((θ-1)/16),θ-16int((θ-1)/16),"("):θ+1→θ:End
If P:Then:Output(R+int((θ-1)/16),θ-16int((θ-1)/16),P):θ+W(P)→θ:End
If P or J:Then:Output(R+int((θ-1)/16),θ-16int((θ-1)/16),sub("+-",J+1,1)):θ+1→θ:End
If Q≠1:Then:Output(R+int((θ-1)/16),θ-16int((θ-1)/16),Q):θ+W(Q)→θ:End
Output(R+int((θ-1)/16),θ-16int((θ-1)/16),"√(")
θ+2→θ
Output(R+int((θ-1)/16),θ-16int((θ-1)/16),V)
θ+W(V)→θ
Output(R+int((θ-1)/16),θ-16int((θ-1)/16),")")
θ+1→θ
If S≠1:Then:Output(R+int((θ-1)/16),θ-16int((θ-1)/16),")/"):θ+2→θ:Output(R+int((θ-1)/16),θ-16int((θ-1)/16),S):End
End
Pause
End
ClrHome
Disp "VERTEX x=h"
Disp H►Frac
If A>0:Then:Disp "MIN VALUE y=k":Else:Disp "MAX VALUE y=k":End
Disp K►Frac
Disp "SUM OF ROOTS"
Disp ~B/A►Frac
Disp "PRODUCT OF ROOTS"
Disp C/A►Frac
Pause
Goto @MS
Lbl @QL
ClrHome
Disp "LINEAR (a=0)"
If B:Then:Disp "x=":Disp ~C/B►Frac:Else:Disp "NO x TERM":End
Pause
Goto @MS
""")

# ---------- 2x2 system ----------
T("""
Lbl @SY
ClrHome
Disp "ax+by=c","dx+ey=f"
Input "a=",A
Input "b=",B
Input "c=",C
Input "d=",D
Input "e=",E
Input "f=",F
AE-BD→Z
ClrHome
If Z
Then
Disp "ONE SOLUTION","x="
Disp (CE-BF)/Z►Frac
Disp "y="
Disp (AF-CD)/Z►Frac
Else
If CE-BF or AF-CD
Then
Disp "NO SOLUTION","(parallel lines)"
Else
Disp "INFINITELY MANY","(same line)"
End
End
Pause
Goto @MS
""")

# ---------- Line through 2 points ----------
T("""
Lbl @LN
ClrHome
Disp "LINE: 2 POINTS"
Input "x1=",P
Input "y1=",Q
Input "x2=",R
Input "y2=",S
(R-P)²+(S-Q)²→N
ClrHome
If R=P
Then
Disp "VERTICAL LINE","x="
Disp P►Frac
Disp "SLOPE UNDEFINED"
Else
(S-Q)/(R-P)→M
Q-MP→B
Disp "SLOPE m"
Disp M►Frac
Disp "Y-INTERCEPT b"
Disp B►Frac
If M
Then
Disp "X-INTERCEPT"
Disp ~B/M►Frac
Disp "PERP. SLOPE"
Disp ~1/M►Frac
Else
Disp "HORIZONTAL LINE"
End
End
Pause
ClrHome
Disp "MIDPOINT (x,y)"
Disp (P+R)/2►Frac
Disp (Q+S)/2►Frac
Disp "DISTANCE"
Disp √(N)
""")
radical(6, "N")
T("""
Pause
Goto @MS
""")

# ---------- Exponential ----------
menu("EX", "EXPONENTIAL", [
    ("Find end value", "E1"),
    ("Find rate %", "E2"),
    ("Back", "MS"),
])
T("""
Lbl @E1
ClrHome
Disp "a(1+r/n)^(nt)","r in %, - decay","n=1 if yearly"
Input "start a=",A
Input "rate %=",R
Input "times/yr n=",N
Input "years t=",T
If N<1 or fPart(N):1→N
1+R/(100N)→G
ClrHome
If G>0
Then
AG^(NT)→Y
Disp "END VALUE"
Disp Y
Disp "FACTOR PER YEAR"
Disp G^N
If A
Then
Disp "TOTAL % CHANGE"
Disp 100(Y/A-1)
End
Else
Disp "RATE MUST BE","MORE THAN -100%"
End
Pause
Goto @EX
Lbl @E2
ClrHome
Disp "FIND RATE","y=a(1+r)^t"
Input "start a=",A
Input "end y=",Y
Input "periods t=",T
ClrHome
If T and AY>0
Then
(Y/A)^(1/T)→G
Disp "GROWTH FACTOR"
Disp G
Disp "RATE % PER t"
Disp 100(G-1)
Else
Disp "INVALID INPUT"
End
Pause
Goto @EX
""")

# ---------- Percent ----------
menu("PC", "PERCENT", [
    ("% change", "P1"),
    ("x% of y", "P2"),
    ("x is ?% of y", "P3"),
    ("Undo a % chg", "P4"),
    ("Stacked %s", "P5"),
    ("Proportion", "P6"),
    ("Back", "MS"),
])
T("""
Lbl @P1
ClrHome
Disp "% CHANGE"
Input "old=",O
Input "new=",N
ClrHome
If O
Then
Disp "% CHANGE"
Disp 100(N-O)/O
Disp "MULTIPLIER"
Disp N/O►Frac
Else
Disp "OLD CAN'T BE 0"
End
Pause
Goto @PC
Lbl @P2
ClrHome
Disp "x% OF y"
Input "x (%)=",X
Input "y=",Y
Disp "RESULT"
Disp XY/100►Frac
Pause
Goto @PC
Lbl @P3
ClrHome
Disp "x IS WHAT % OF y"
Input "x=",X
Input "y=",Y
If Y
Then
Disp "PERCENT"
Disp 100X/Y
End
Pause
Goto @PC
Lbl @P4
ClrHome
Disp "FIND ORIGINAL","after a % chg"
Input "new value=",N
Input "% chg (+/-)=",P
If P≠~100
Then
Disp "ORIGINAL"
Disp N/(1+P/100)►Frac
End
Pause
Goto @PC
Lbl @P5
ClrHome
Disp "STACKED CHANGES","use - for drops"
Input "1st %=",P
Input "2nd %=",Q
(1+P/100)(1+Q/100)→M
Disp "NET MULTIPLIER"
Disp M
Disp "NET % CHANGE"
Disp 100(M-1)
Pause
Goto @PC
Lbl @P6
ClrHome
Disp "a/b = c/x"
Input "a=",A
Input "b=",B
Input "c=",C
If A
Then
Disp "x=bc/a"
Disp BC/A►Frac
End
Pause
Goto @PC
""")

# ---------- Geometry / stats ----------
menu("GM", "GEOMETRY/STATS", [
    ("Circle eqn", "CI"),
    ("Right triangle", "RT"),
    ("Arc & sector", "AR"),
    ("Mean/Median/SD", "ST"),
    ("Missing value", "MV"),
    ("Deg <-> Rad", "DR"),
    ("Back", "MS"),
])
T("""
Lbl @CI
ClrHome
Disp "ax²+ay²+dx+ey","+f=0 (often a=1)"
Input "a=",A
Input "d=",D
Input "e=",E
Input "f=",F
If not(A):1→A
~D/(2A)→H
~E/(2A)→K
H²+K²-F/A→N
ClrHome
Disp "CENTER (h,k)"
Disp H►Frac
Disp K►Frac
Disp "RADIUS SQUARED"
Disp N►Frac
If N>0
Then
Disp "RADIUS"
Disp √(N)
""")
radical(8, "N")
T("""
Else
Disp "NOT A CIRCLE"
End
Pause
Goto @GM
""")

T("""
Lbl @RT
ClrHome
Disp "RIGHT TRIANGLE","legs a,b; hyp c","0 = unknown"
Input "a=",A
Input "b=",B
Input "c=",C
abs(A)→A
abs(B)→B
abs(C)→C
If not(C):√(A²+B²)→C
If not(A) and C>B:√(C²-B²)→A
If not(B) and C>A:√(C²-A²)→B
ClrHome
If A≤0 or B≤0 or C≤max(A,B)
Goto @RX
45/tan⁻¹(1)→F
Disp "SIDES a, b, c"
Disp round(A,4)
Disp round(B,4)
Disp round(C,4)
Disp "ANGLE A (opp a)"
Disp round(Ftan⁻¹(A/B),4)
Disp "ANGLE B"
Disp round(90-Ftan⁻¹(A/B),4)
Pause
ClrHome
Disp "sin A = a/c"
Disp A/C►Frac
Disp "cos A = b/c"
Disp B/C►Frac
Disp "tan A = a/b"
Disp A/B►Frac
Disp "TIP: sinA=cosB"
Pause
Goto @GM
Lbl @RX
Disp "NEED 2 VALID","SIDES (c = hyp)"
Pause
Goto @GM
""")

menu("AR", "ANGLE UNITS?", [
    ("Degrees", "A1"),
    ("Radians", "A2"),
    ("Back", "GM"),
])
T("""
Lbl @A1
ClrHome
Disp "ARC & SECTOR"
Input "radius r=",R
Input "angle deg=",D
πD/180→T
Goto @A3
Lbl @A2
ClrHome
Disp "ARC & SECTOR","(π key is ok)"
Input "radius r=",R
Input "angle rad=",T
Lbl @A3
ClrHome
Disp "ARC LENGTH"
Disp RT
Disp "ARC / π"
Disp RT/π►Frac
Disp "SECTOR AREA"
Disp R²T/2
Disp "SECTOR AREA / π"
Disp R²T/(2π)►Frac
Pause
ClrHome
Disp "FRACTION OF"
Disp "WHOLE CIRCLE"
Disp T/(2π)►Frac
Disp "ANGLE (DEGREES)"
Disp 180T/π►Frac
Disp "CIRCUMFERENCE"
Disp 2πR
Pause
Goto @GM
""")

T("""
Lbl @ST
ClrHome
Disp "ENTER A LIST","like {2,5,9}"
Input "list=",L₆
dim(L₆)→N
ClrHome
Disp "MEAN"
Disp mean(L₆)►Frac
Disp "MEDIAN"
Disp median(L₆)►Frac
Disp "RANGE"
Disp max(L₆)-min(L₆)
Disp "SD (POPULATION)"
Disp √(sum((L₆-mean(L₆))²)/N)
Pause
ClrHome
Disp "COUNT n"
Disp N
Disp "SUM"
Disp sum(L₆)
Disp "MIN, MAX"
Disp {min(L₆),max(L₆)}
SortA(L₆)
Disp "SORTED:"
Disp L₆
Pause
Goto @GM
""")

T("""
Lbl @MV
ClrHome
Disp "ADD 1 VALUE TO","HIT A NEW MEAN"
Input "count n=",N
Input "mean now=",M
Input "target mean=",T
ClrHome
Disp "VALUE NEEDED"
Disp (N+1)T-NM►Frac
Disp "SUM NOW"
Disp NM►Frac
Disp "SUM NEEDED"
Disp (N+1)T►Frac
Pause
Goto @GM
""")

menu("DR", "CONVERT ANGLE", [
    ("Deg -> Radians", "D1"),
    ("Rad -> Degrees", "D2"),
    ("Back", "GM"),
])
T("""
Lbl @D1
ClrHome
Input "degrees=",D
Disp "RADIANS / π"
Disp D/180►Frac
Disp "RADIANS"
Disp πD/180
Pause
Goto @DR
Lbl @D2
ClrHome
Disp "(π key is ok)"
Input "radians=",T
Disp "DEGREES"
Disp 180T/π►Frac
Pause
Goto @DR
""")

# =====================================================================
# MATH FORMULAS (reference pages)
# =====================================================================
section("formulas")
menu("FA", "ALGEBRA FORMULAS", [
    ("Linear eqns", "F1"),
    ("Quadratics", "F2"),
    ("Exponents/Rads", "F3"),
    ("Exponential", "F4"),
    ("Functions", "F5"),
    ("More formulas", "FG"),
    ("Main Menu", "MM"),
])
menu("FG", "GEOMETRY + DATA", [
    ("Geometry", "G1"),
    ("Circles", "G2"),
    ("Triangles/Trig", "G3"),
    ("Statistics", "G4"),
    ("Probability", "G5"),
    ("Percent/Units", "G6"),
    ("Back", "FA"),
])

pager("F1", "LINEAR EQNS", [
    ["y=mx+b",
     "m=slope b=y-int",
     "slope=rise/run",
     "=(y2-y1)/(x2-x1)",
     "Point-slope:",
     "y-y1=m(x-x1)"],
    ["Standard form:",
     "  Ax+By=C",
     "slope = -A/B",
     "y-int = C/B",
     "x-int = C/A"],
    ["Parallel:",
     "  same slope",
     "Perpendicular:",
     " flip & negate m",
     "Horizontal: y=k",
     "Vertical: x=k"],
    ["ax+by=c, dx+ey=f",
     "1 sol: a/d≠b/e",
     "None: a/d=b/e",
     "      but ≠c/f",
     "Inf: a/d=b/e=c/f",
     "(same line)"],
], "FA")

pager("F2", "QUADRATICS", [
    ["ax²+bx+c=0",
     "x=(-b +/- √(D))",
     "      /(2a)",
     "D = b²-4ac",
     "D>0: 2 real sol",
     "D=0: 1  D<0: 0"],
    ["Vertex form:",
     "  y=a(x-h)²+k",
     "vertex (h,k)",
     "h = -b/(2a)",
     "a>0 opens up",
     "a<0 opens down"],
    ["Factored form:",
     "  y=a(x-r)(x-s)",
     "zeros: r and s",
     "Sum roots=-b/a",
     "Prod roots=c/a",
     "Axis x=(r+s)/2"],
    ["y-int = c",
     "max/min = k",
     "(x+a)²=x²+2ax+a²",
     "(x-a)²=x²-2ax+a²",
     "x²-a²=(x+a)(x-a)"],
], "FA")

pager("F3", "EXPONENTS", [
    ["x^a*x^b=x^(a+b)",
     "x^a/x^b=x^(a-b)",
     "(x^a)^b=x^(ab)",
     "(xy)^a=x^a*y^a",
     "x^0=1",
     "x^-n=1/x^n"],
    ["x^(1/2)=√(x)",
     "x^(m/n)=",
     " (nth root x)^m",
     "√(ab)=√(a)√(b)",
     "√(a/b)=√(a)/√(b)",
     "1/√(a)=√(a)/a"],
], "FA")

pager("F4", "EXPONENTIAL", [
    ["y=a(1+r)^t",
     "a=start value",
     "r=rate (decimal)",
     "Grow: a(1+r)^t",
     "Decay:a(1-r)^t",
     "b>1 grow b<1 dec"],
    ["Compound n/yr:",
     "  a(1+r/n)^(nt)",
     "Doubles every d:",
     "  a*2^(t/d)",
     "Half-life h:",
     "  a*(1/2)^(t/h)"],
    ["LINEAR: adds a",
     " constant amount",
     "EXP: multiplies",
     " by same factor",
     "",
     "+5/yr vs +5%/yr"],
], "FA")

pager("F5", "FUNCTIONS", [
    ["Graph shifts:",
     "f(x)+k  up k",
     "f(x-h)  right h",
     "f(x+h)  left h",
     "-f(x)  flip vert",
     "f(-x)  flip horz"],
    ["Zeros = roots =",
     " x-intercepts:",
     " where f(x)=0",
     "f(a)=b means",
     " point (a,b)",
     "f(g(x)): g first"],
    ["Domain: x values",
     "Range: y values",
     "Avoid /0, √(neg)",
     "TI TIP: graph in",
     "Y=, 2nd TRACE:",
     "zero/min/max/int"],
], "FA")

pager("G1", "GEOMETRY", [
    ["AREA",
     "Rect: lw",
     "Tri: (1/2)bh",
     "Trap: (b1+b2)h/2",
     "Circle: πr²",
     "Circum: 2πr"],
    ["VOLUME",
     "Box: lwh",
     "Cyl: πr²h",
     "Sphere: 4/3πr³",
     "Cone: 1/3πr²h",
     "Pyramid: 1/3lwh"],
    ["ANGLES",
     "Line: 180°",
     "Triangle: 180°",
     "n-gon: 180(n-2)",
     "Vertical angles=",
     "Parallel+transv."],
    ["SIMILAR SHAPES",
     "side ratio k",
     "area ratio k²",
     "volume ratio k³",
     "Ex: double r",
     " -> area *4"],
], "FG")

pager("G2", "CIRCLES", [
    ["(x-h)²+(y-k)²=r²",
     "center (h,k)",
     "radius r",
     "Got x²+y²+dx..?",
     "complete square",
     "or use SOLVER"],
    ["Complete square:",
     "x²+6x -> add 9",
     " = (x+3)²",
     "Add (b/2)² to",
     " BOTH sides"],
    ["Arc=(θ/360)2πr",
     "Sect=(θ/360)πr²",
     "In radians:",
     " Arc = rθ",
     " Sect=(1/2)r²θ",
     "180° = π rad"],
    ["Tangent line is",
     " perp to radius",
     "Inscribed angle",
     " = half its arc",
     "Central angle",
     " = its arc"],
], "FG")

pager("G3", "TRIANGLES", [
    ["a²+b²=c²",
     "Triples: 3-4-5",
     " 5-12-13 8-15-17",
     " 7-24-25",
     "45-45-90:",
     " x, x, x√(2)"],
    ["30-60-90:",
     " x, x√(3), 2x",
     "(short,long,hyp)",
     "Triangle ineq:",
     " c < a+b",
     "Lg side=lg angle"],
    ["SOH CAH TOA",
     "sin=opp/hyp",
     "cos=adj/hyp",
     "tan=opp/adj",
     "sin(x)=cos(90-x)",
     "Check MODE:DEG!"],
    ["deg*π/180=rad",
     "rad*180/π=deg",
     "sin²x+cos²x=1",
     "Unit circle pt:",
     " (cos θ, sin θ)"],
], "FG")

pager("G4", "STATISTICS", [
    ["Mean=sum/count",
     "Median=middle",
     " (sort first!)",
     "Mode=most often",
     "Range=max-min",
     "Sum=mean*count"],
    ["Outlier effect:",
     "Mean moves a lot",
     "Median barely",
     "SD = spread",
     "More spread out",
     " = bigger SD"],
    ["Margin of error:",
     " est +/- MOE",
     " = likely range",
     "Bigger sample",
     " = smaller MOE"],
    ["Random sample:",
     " results apply",
     " to population",
     "Random assign:",
     " can show cause",
     "Else: only link"],
], "FG")

pager("G5", "PROBABILITY", [
    ["P=want/total",
     "P(A or B)=",
     " P(A)+P(B)-both",
     "Indep: P(A)P(B)",
     "P(not A)=1-P(A)"],
    ["Two-way tables:",
     "P(A given B)=",
     " count A&B",
     " / count B",
     "The GIVEN group",
     " = your total!"],
], "FG")

pager("G6", "PERCENT/UNIT", [
    ["%chg=",
     " (new-old)/old",
     "x% of y=(x/100)y",
     "Up p%:*(1+p/100)",
     "Dn p%:*(1-p/100)",
     "Orig=new/mult"],
    ["Stacked changes:",
     "+20% then -20%",
     " =1.2*.8=.96",
     " = 4% DECREASE",
     "Units: multiply",
     " by unit ratios"],
    ["1 ft=12 in",
     "1 yd=3 ft",
     "1 mi=5280 ft",
     "1 hr=3600 s",
     "ft²->in²: *144",
     "ft³->in³: *1728"],
], "FG")

# =====================================================================
# READING & WRITING GUIDE
# =====================================================================
section("rw")
menu("RW", "READING+WRITING", [
    ("Punctuation", "R1"),
    ("Grammar", "R2"),
    ("Transitions", "R3"),
    ("Notes Qs", "R4"),
    ("Reading Qs", "R5"),
    ("R&W Strategy", "R6"),
    ("Main Menu", "MM"),
])

pager("R1", "PUNCTUATION", [
    ["IC=independent",
     " clause (could",
     " be a sentence)",
     "IC; IC   OK",
     "IC, IC   WRONG",
     " (comma splice)"],
    ["Fix a splice:",
     "IC. IC / IC; IC",
     "IC, FANBOYS IC",
     "FANBOYS =",
     "for,and,nor,but,",
     "or,yet,so"],
    ["COLON :",
     "IC: list/explain",
     "Before the colon",
     " = a full IC!",
     "I had one goal:",
     " to win."],
    ["DASH --",
     "acts as a colon",
     " OR like a pair",
     " of commas",
     "Match the pair:",
     ",X,  -X-  (X)"],
    ["COMMAS: use for",
     "-intro phrases,",
     "-extra info, in",
     " a matched pair,",
     "-lists: a, b, c",
     "-IC, FANBOYS IC"],
    ["NO comma between",
     "-subject & verb",
     "-verb & object",
     "-before 'that'",
     "-essential info",
     "Doubt? Cut it."],
    ["APOSTROPHES '",
     "dog's = 1 dog",
     "dogs' = 2+ dogs",
     "its = possessive",
     "it's = it is",
     "whose vs who's"],
], "RW")

pager("R2", "GRAMMAR", [
    ["SUBJECT-VERB",
     "Cross out 'of'",
     " phrases:",
     "The box of toys",
     " IS heavy.",
     "Each/every = 1"],
    ["Tricky singular:",
     "each, everyone,",
     "team, group,",
     "either, neither",
     "There IS a cat",
     "There ARE cats"],
    ["Or/nor: verb",
     " matches the",
     " NEARER noun:",
     "Neither he nor",
     " they ARE ready",
     ""],
    ["PRONOUNS match",
     " their noun:",
     "company -> its",
     "parents -> their",
     "who = people",
     "which = things"],
    ["who = he (subj)",
     "whom = him (obj)",
     "I vs me: drop",
     " the other noun",
     "Me and Al went X",
     "Al and I went OK"],
    ["VERB TENSE:",
     "match nearby",
     " verbs & dates",
     "In 1990 -> past",
     "had + verb =",
     " earlier past"],
    ["MODIFIERS:",
     "Walking home,",
     " SHE saw a dog.",
     "Noun after the",
     " comma does the",
     " intro action!"],
    ["PARALLEL lists:",
     "to run, swim,",
     " and bike  OK",
     "running, swim,",
     " to bike  WRONG",
     "CONCISE wins!"],
], "RW")

pager("R3", "TRANSITIONS", [
    ["Read sentence",
     " BEFORE & after",
     "Name the link:",
     "contrast? cause?",
     " example? more?",
     "Then pick word."],
    ["CONTRAST:",
     "however, but",
     "nevertheless,",
     "in contrast,",
     "conversely,",
     "still, yet"],
    ["ADD / SAME WAY:",
     "furthermore,",
     "moreover,",
     "additionally,",
     "similarly,",
     "likewise,"],
    ["CAUSE->EFFECT:",
     "therefore,",
     "thus, hence,",
     "consequently,",
     "as a result,",
     "accordingly,"],
    ["EXAMPLE:",
     "for example,",
     "for instance,",
     "CLARIFY:",
     "in other words,",
     "that is,"],
    ["TIME / ORDER:",
     "subsequently,",
     "meanwhile, then",
     "CONCLUDE:",
     "in sum, overall",
     "ultimately,"],
], "RW")

pager("R4", "NOTES Qs", [
    ["Student notes Qs",
     "1. Read the GOAL",
     " in the question",
     "2. Pick choice",
     " that does ONLY",
     " that goal"],
    ["Goal keywords:",
     "compare->2 items",
     "contrast->diffs",
     "emphasize->focus",
     "unfamiliar aud.",
     "->explain/define"],
    ["Wrong answers:",
     "-true but off-",
     " goal",
     "-only half of",
     " the goal",
     "-extra details"],
], "RW")

pager("R5", "READING Qs", [
    ["WORDS IN CONTEXT",
     "Cover choices.",
     "Predict your own",
     " word from clues",
     "Match prediction",
     ""],
    ["MAIN PURPOSE:",
     "Whole text, not",
     " one detail",
     "Verbs: argue,",
     " describe, show,",
     " challenge..."],
    ["EVIDENCE Qs:",
     "Find the claim",
     "Choice must",
     "DIRECTLY back it",
     "Data Qs: read",
     " the labels!"],
    ["INFERENCE:",
     "Most logical",
     " completion",
     "Must be PROVEN",
     " by the text",
     "Avoid extremes"],
    ["CROSS-TEXT:",
     "Text 1 vs Text 2",
     "How would the",
     " author of 2",
     " respond to 1?",
     "agree/disagree?"],
    ["TEXT STRUCTURE:",
     "Label each line:",
     " claim/evidence/",
     " counter/example",
     "Purpose of a",
     " line = its job"],
], "RW")

pager("R6", "R&W STRATEGY", [
    ["Module: 27 Qs",
     " in 32 minutes",
     "~70 sec per Q",
     "No penalty for",
     " guessing, so",
     " answer EVERY Q"],
    ["Grammar Qs:",
     "What differs in",
     " the choices?",
     "That is the",
     " rule being",
     " tested."],
    ["Stuck? Use",
     "Mark for Review",
     " and come back",
     "Elimination:",
     "Wrong if ANY",
     " part is wrong"],
], "RW")

# =====================================================================
# TEST STRATEGY + HELP
# =====================================================================
section("strategy")
pager("TS", "STRATEGY", [
    ["DIGITAL SAT",
     "R&W: 2x32 min",
     " 54 questions",
     "Math: 2x35 min",
     " 44 questions",
     "Score 400-1600"],
    ["ADAPTIVE:",
     "Module 2 gets",
     " harder if M1",
     " goes well.",
     "Accuracy in M1",
     " matters most!"],
    ["MATH:",
     "~95 sec per Q",
     "Calc OK on all",
     " of Math",
     "Plug in answers",
     " or pick numbers"],
    ["TYPED ANSWERS:",
     "Negative OK",
     "Fractions OK",
     "5 chars (+)",
     "6 chars (-)",
     "No mixed #s"],
    ["TEST DAY:",
     "Fresh batteries!",
     "Bring a backup",
     "Sleep > cramming",
     "Arrive early",
     "You've got this!"],
], "MM")

section("core")
pager("HU", "HOW TO USE", [
    ["Menus: press #",
     "Pages: < > keys",
     " or ENTER",
     "CLEAR: go back",
     "Frozen? ON key",
     "Uses A-Z,θ,L6"],
], "MM")

# =====================================================================
# PRACTICE QUIZ
# =====================================================================
# ---------- Math quiz: 10 generated question types ----------
section("quizmath")
T("""
Lbl @QM
0→L
0→T
Lbl @QN
randInt(1,10)→Z
ClrHome
Disp "","","","","",""
Output(1,1,"MATH Q")
Output(1,7,T+1)
""")


def qtype(n: int, body) -> None:
    T(f"If Z={n}")
    T("Then")
    body()
    T("End")


def q_linear():
    T("""
randInt(2,9)→A
randInt(~9,9)→X
randInt(1,15)(2randInt(0,1)-1)→B
AX+B→C
Output(3,1,"Solve for x:")
""")
    seg_row(5, [("c", "A", "x"), ("t", "B"), "=", ("n", "C")])


def q_percent():
    T("""
5randInt(1,19)→P
20randInt(1,10)→N
PN/100→X
Output(3,1,"What is")
""")
    seg_row(4, [("n", "P"), "% of ", ("n", "N"), "?"])


def q_slope():
    T("""
randInt(~9,9)→P
randInt(~9,9)→Q
P+randInt(1,6)(2randInt(0,1)-1)→R
randInt(~9,9)→S
(S-Q)/(R-P)→X
Output(2,1,"Slope of line")
Output(3,1,"through:")
""")
    seg_row(4, ["(", ("n", "P"), ",", ("n", "Q"), ")"])
    seg_row(5, ["and (", ("n", "R"), ",", ("n", "S"), ")"])


def q_exponent():
    T("""
randInt(2,9)→A
randInt(2,9)→B
randInt(0,1)→V
Output(2,1,"Find n:")
If V
Then
A+B→X
""")
    seg_row(4, ["x^", ("n", "A"), "*x^", ("n", "B")])
    T("""
Else
AB→X
""")
    seg_row(4, ["(x^", ("n", "A"), ")^", ("n", "B")])
    T("""
End
Output(5,1,"= x^n")
""")


def q_mean():
    T("""
randInt(1,15)→A
randInt(1,15)→B
randInt(1,15)→C
randInt(1,15)→D
4fPart((A+B+C+D)/4)→U
D+(4-U)(U>0)→D
D→X
(A+B+C+D)/4→M
Output(2,1,"Mean of 4 nums")
""")
    seg_row(3, ["is ", ("n", "M"), ". Three are"])
    seg_row(4, [("n", "A"), ", ", ("n", "B"), ", ", ("n", "C"), "."])
    T('Output(5,1,"Find the 4th.")')


def q_discriminant():
    T("""
randInt(~8,8)→B
randInt(~10,10)→C
If randInt(1,3)=1
Then
2randInt(~4,4)→B
B²/4→C
End
B²-4C→D
2(D>0)+(D=0)→X
Output(2,1,"How many real")
Output(3,1,"solutions?")
""")
    seg_row(5, ["x²", ("t", "B", "x"), ("t", "C"), "=0"])


def q_vertex():
    T("""
randInt(1,3)(2randInt(0,1)-1)→A
randInt(~6,6)→H
~2AH→B
randInt(~9,9)→C
H→X
Output(2,1,"x-coord of the")
Output(3,1,"vertex of:")
""")
    seg_row(5, ["y=", ("c", "A", "x²"), ("t", "B", "x"), ("t", "C")])


def q_function():
    T("""
randInt(1,5)→A
randInt(~9,9)→B
randInt(~4,4)→K
AK²+B→X
""")
    seg_row(2, ["f(x)=", ("c", "A", "x²"), ("t", "B")])
    seg_row(4, ["Find f(", ("n", "K"), ")"])


def q_system():
    T("""
randInt(~9,9)→X
randInt(~9,9)→Y
""")
    T("""
X+Y→U
X-Y→V
""")
    seg_row(2, ["x+y=", ("n", "U")])
    seg_row(3, ["x-y=", ("n", "V")])
    T('Output(5,1,"Find x.")')


def q_circle():
    T("""
randInt(~5,5)→H
randInt(~5,5)→K
randInt(1,9)→X
~2H→D
~2K→E
H²+K²-X²→F
~F→G
Output(2,1,"Radius of:")
""")
    seg_row(4, ["x²+y²", ("t", "D", "x"), ("t", "E", "y")])
    seg_row(5, ["=", ("n", "G")])


for i, fn in enumerate([q_linear, q_percent, q_slope, q_exponent, q_mean,
                        q_discriminant, q_vertex, q_function, q_system, q_circle], 1):
    qtype(i, fn)

T("""
Input "answer=",G
T+1→T
abs(G-X)<.000001→V
ClrHome
If V
Then
L+1→L
Disp "CORRECT!"
Else
Disp "NOT QUITE.","ANSWER:"
Disp X►Frac
End
Output(5,1,"SCORE:")
Output(5,8,L)
Output(5,8+W(L),"/")
Output(5,9+W(L),T)
Output(7,1,"ENTER: next")
Output(8,1,"CLEAR: finish")
0→K
Repeat K=45 or K=105
getKey→K
End
If K=105
Goto @QN
Goto @QF
""")

# ---------- Grammar quiz ----------
section("quizgrammar")
GRAMMAR = [
    (["The list of", "items ___ on", "the table."],
     "is", ["are", "were", "have been"],
     ["Subject: list", "(singular). Skip", "the 'of' phrase."]),
    (["She studied all", "night___ she", "aced the test."],
     "; (semicolon)", [", (comma)", "(nothing)", ", then"],
     ["Two full", "sentences need", "; or a period.", "Comma = splice."]),
    (["The company", "said that ___", "profits rose."],
     "its", ["their", "it's", "they're"],
     ["A company is", "one thing: its.", "it's = it is"]),
    (["The plan was", "cheap. ___, it", "failed fast."],
     "However", ["Therefore", "Similarly", "For example"],
     ["Cheap (good) vs", "failed (bad):", "contrast word."]),
    (["It rained all", "day. ___, the", "game was", "canceled."],
     "As a result", ["However", "Likewise", "Meanwhile"],
     ["The rain CAUSED", "the cancel:", "cause->effect."]),
    (["Running late,", "___ missed the", "bus."],
     "Sam", ["the bus", "Sam's bike", "it"],
     ["Who was running", "late? Sam must", "come right after", "the comma."]),
    (["She had one", "goal___ to win", "the title."],
     ": (colon)", ["; (semicolon)", "(nothing)", ", and"],
     ["Full sentence +", "explanation", "= colon."]),
    (["Both ___", "jackets were", "left at school."],
     "girls'", ["girl's", "girls", "girls's"],
     ["2+ girls own", "them: plural", "possessive s'."]),
    (["In 1969, Apollo", "11 ___ on the", "Moon."],
     "landed", ["lands", "will land", "has landed"],
     ["1969 = a done", "past event:", "simple past."]),
    (["He likes to", "hike, swim,", "and ___."],
     "bike", ["biking", "to biking", "bikes"],
     ["Parallel: to", "hike, swim, and", "bike."]),
    (["Neither the", "coach nor the", "players ___", "ready."],
     "were", ["was", "is", "has been"],
     ["With or/nor the", "verb matches the", "nearer noun:", "players."]),
    (["To ___ should I", "give this?"],
     "whom", ["who", "who's", "whose"],
     ["Object of 'to':", "to him -> whom", "(he -> who)"]),
    (["I was tired___", "I kept working."],
     ", but", [", (comma)", "(nothing)", ", however,"],
     ["A FANBOYS word", "after a comma", "joins 2 full", "sentences."]),
    (["The effects of", "the new drug", "___ unknown."],
     "remain", ["remains", "is", "has been"],
     ["Subject is", "effects (plural)", "not drug."]),
    (["Some birds", "can't fly. ___,", "penguins swim", "instead."],
     "For example", ["However", "Therefore", "Meanwhile"],
     ["Penguins are an", "EXAMPLE of birds", "that can't fly."]),
    (["The meeting", "___ at noon."],
     "ended", ["came to an end", "ended and quit", "had an ending"],
     ["All say the", "same thing: the", "shortest clear", "choice wins."]),
    (["Located in Peru", "___ draws many", "tourists."],
     ", Machu Picchu", [", tourists see", ", its fame", ", people visit"],
     ["Located in Peru", "must describe", "the noun right", "after it."]),
    (["My cat, who is", "10___ loves", "naps."],
     ", (comma)", ["; (semicolon)", "(nothing)", "-- (dash)"],
     ["Extra info opens", "with a comma, so", "it must close", "with a comma."]),
]

rng = random.Random(84)  # fixed seed: stable answer positions between builds
T("""
Lbl @QG
0→L
0→T
0→P
Lbl @GN
Repeat Q≠P
""")
code.append(f"randInt(1,{len(GRAMMAR)})→Q")
T("""
End
Q→P
ClrHome
""")
for i, (stem, right, wrong, expl) in enumerate(GRAMMAR, 1):
    if not (len(stem) <= 4 and len(expl) <= 4 and len(wrong) == 3):
        PROBLEMS.append(f"bad question {i}")
    choices = [right] + wrong
    rng.shuffle(choices)
    ans = choices.index(right) + 1
    T(f"If Q={i}")
    T("Then")
    for r, s in enumerate(stem, 1):
        code.append(out_line(r, s))
    for k, c in enumerate(choices, 1):
        if len(c) > 14:
            PROBLEMS.append(f"choice too long: {c!r}")
        code.append(f"Output({4 + k},1,{q(f'{k} {c}')})")
    code.append(f"{ans}→X")
    T("End")
T("""
0→K
Repeat max(K={92,93,94,82,45})
getKey→K
End
If K=45
Goto @QF
(K=92)+2(K=93)+3(K=94)+4(K=82)→G
T+1→T
ClrHome
If G=X
Then
L+1→L
Output(1,1,"CORRECT!")
Else
Output(1,1,"NO. ANSWER: ")
Output(1,13,X)
End
""")
for i, (stem, right, wrong, expl) in enumerate(GRAMMAR, 1):
    T(f"If Q={i}")
    T("Then")
    for r, s in enumerate(expl, 3):
        code.append(out_line(r, s))
    T("End")
T("""
Output(7,1,"SCORE:")
Output(7,8,L)
Output(7,8+W(L),"/")
Output(7,9+W(L),T)
Output(8,1,"ENTER:next CLR:x")
0→K
Repeat K=45 or K=105
getKey→K
End
If K=105
Goto @GN
Goto @QF
""")

# ---------- Final score (shared) ----------
section("quizfinal")
T("""
Lbl @QF
ClrHome
Output(2,1,"FINAL SCORE")
Output(4,1,L)
Output(4,1+W(L),"/")
Output(4,2+W(L),T)
If T
Then
round(100L/T,0)→V
Output(5,1,V)
Output(5,1+W(V),"%")
End
Output(7,1,"Keep practicing!")
Pause
Goto @PQ
""")

# =====================================================================
# QUIT (last, so the program ends without printing "Done")
# =====================================================================
section("core")
T("""
Lbl @QT
DelVar L₆
ClrHome
Output(3,3,"Good luck on")
Output(4,3,"the SAT!")
""")


# =====================================================================
# TOKENIZE + SAVE
# =====================================================================
def tokenize(lines: list[str]) -> bytes:
    from tivars.models import TI_84P
    from tivars.tokenizer import encode

    trie = TI_84P.tokens.tries[None]
    cache: dict[str, bytes] = {}

    def str_char(ch: str) -> bytes:
        if ch == "π":
            return b"\xac"
        if ch not in cache:
            cache[ch] = encode(ch, trie=trie, mode="string")[0]
        return cache[ch]

    out = bytearray()
    for n, line in enumerate(lines):
        parts = line.split('"')
        for i, part in enumerate(parts):
            if i % 2 == 0:  # code
                if part:
                    out += encode(part.replace("π", "pi"), trie=trie, mode="max")[0]
            else:  # string literal
                j = 0
                while j < len(part):
                    if part.startswith("√(", j):
                        out += b"\xbc"
                        j += 2
                    else:
                        out += str_char(part[j])
                        j += 1
            if i < len(parts) - 1:
                out += b"\x2a"
        if n < len(lines) - 1:
            out += b"\x3f"
    return bytes(out)


def main() -> None:
    from tivars.models import TI_84P
    from tivars.types import TIProgram

    if PROBLEMS:
        sys.exit("\n".join(PROBLEMS))
    lines = select_sections(code, CFG["sections"])
    if CFG["upper"]:
        lines = [upper_strings(l) for l in lines]
    errs = check_structure(lines)
    if errs:
        sys.exit("\n".join(errs))
    src = "\n".join(lines)
    (HERE / "source").mkdir(exist_ok=True)
    (HERE / "source" / f"{PROG_NAME}.txt").write_text(src + "\n", encoding="utf-8")
    data = tokenize(lines)
    prog = TIProgram(name=PROG_NAME)
    prog.data = data
    out = HERE / ("TI-84 Plus CE" if PROG_NAME == "SAT" else "TI-84 Plus (older models)")
    out.mkdir(exist_ok=True)
    prog.save(str(out / f"{PROG_NAME}.8xp"), model=TI_84P)
    print(f"{PROG_NAME:8} {len(lines):5} lines {len(data):6} bytes")


def select_sections(lines: list[str], keep: set[str]) -> list[str]:
    out, on = [], True
    for line in lines:
        if line.startswith("#SECTION "):
            on = line.split()[1] in keep
        elif on:
            out.append(line)
    return out


def upper_strings(line: str) -> str:
    parts = line.split('"')
    for i in range(1, len(parts), 2):
        parts[i] = "".join(c.upper() if "a" <= c <= "z" else c for c in parts[i])
    return '"'.join(parts)


def statements(line: str) -> list[str]:
    """Split a line on ':' outside of strings."""
    out, cur, in_str = [], "", False
    for c in line:
        if c == '"':
            in_str = not in_str
        if c == ":" and not in_str:
            out.append(cur)
            cur = ""
        else:
            cur += c
    out.append(cur)
    return [s for s in out if s]


def check_structure(lines: list[str]) -> list[str]:
    """Static checks: labels resolve, blocks balance, and no Goto/Menu/Lbl inside
    a block (jumping out of If-Then/loops leaks memory -> ERR:MEMORY over time)."""
    errs = []
    stmts = [(n, s) for n, line in enumerate(lines, 1) for s in statements(line)]
    defined = {}
    for n, s in stmts:
        if s.startswith("Lbl "):
            name = s[4:]
            if name in defined:
                errs.append(f"line {n}: duplicate Lbl {name}")
            defined[name] = n
    stack: list[str] = []
    conditional = False
    for idx, (n, s) in enumerate(stmts):
        nxt = stmts[idx + 1][1] if idx + 1 < len(stmts) else ""
        was_conditional, conditional = conditional, False
        targets = []
        if s.startswith("Goto "):
            targets = [s[5:]]
        elif s.startswith("Menu("):
            targets = re.findall(r'"[^"]*",(\w+)', s)
        for t in targets:
            if t not in defined:
                errs.append(f"line {n}: undefined label {t}")
        if (targets or s.startswith("Lbl ")) and stack:
            errs.append(f"line {n}: '{s}' inside block {stack}")
        if s.startswith("If "):
            if nxt == "Then":
                stack.append("If")
            else:
                conditional = True
        elif s.startswith(("While ", "Repeat ", "For(")):
            stack.append("loop")
        elif s == "Else":
            if not stack or stack[-1] != "If":
                errs.append(f"line {n}: Else without If-Then")
        elif s == "End":
            if not stack:
                errs.append(f"line {n}: End without block")
            else:
                stack.pop()
    if stack:
        errs.append(f"unclosed blocks at end: {stack}")
    return errs


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        import subprocess
        for name in TARGETS:
            r = subprocess.run([sys.executable, __file__, name])
            if r.returncode:
                sys.exit(r.returncode)
