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
# SATMATH + SATTRIG + SATRW split the content for the older TI-84 Plus / Silver
# Edition, which only has ~24 KB of RAM, and use uppercase text (half the bytes).
TARGETS = {
    "SAT": dict(upper=False, sections={"core", "solvers", "trig", "formulas", "rw", "strategy",
                                       "quizmath", "quizgrammar", "quizfinal"}),
    "SATMATH": dict(upper=True, sections={"core", "solvers", "formulas", "strategy",
                                          "quizmath", "quizfinal"}),
    "SATTRIG": dict(upper=True, sections={"core", "trig", "quizfinal"}),
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


# ---------------------------------------------------------------------
# Exact-value printer. TI-BASIC has no subroutines, so each call stores its
# arguments, jumps to the shared routine, and the routine jumps back through
# a dispatch table on Z. Calls must sit at the top level (never inside a block).
#   in:  X value, R row, θ start column, Z return id
#   out: prints X as  [-]p√(q)/d  (or a plain fraction / integer), θ advances
#   uses: I J K O Q U W Y as scratch
# Works for any value whose square is a fraction with denominator <= 9999,
# which covers every SAT triangle and unit-circle value. Otherwise: decimal.
# ---------------------------------------------------------------------
_exact_returns: list[str] = []


def exact(expr: str, row: int, col) -> None:
    rid = len(_exact_returns) + 1
    ret = f"XR{rid}"
    _exact_returns.append(ret)
    T(f"""
{expr}→X
{row}→R
{col}→θ
{rid}→Z
Goto @XA
Lbl @{ret}
""")


def exact_routine() -> list[str]:
    """Emitted at the very top of the program so Goto finds it quickly."""
    global code
    saved, code = code, []
    T("""
Goto @ST0
Lbl @XA
If abs(X)<.000000001
Goto @XZ
X²→Y
Y→Q
0→I
1→J
1→U
0→O
Repeat abs(J/O-Y)<.00000000001max(1,Y) or O>9999
int(Q)→W
WJ+I→K
J→I
K→J
WO+U→K
O→U
K→O
If Q-W:1/(Q-W)→Q
End
If O>9999 or J>99999
Goto @XD
If not(J)
Goto @XZ
int(√(J))→I
While fPart(J/I²)
I-1→I
End
J/I²→U
int(√(O))→K
While fPart(O/K²)
K-1→K
End
O/K²→W
UW→U
KW→O
gcd(I,O)→W
I/W→I
O/W→O
(X<0)+(U=1 or I≠1)W(I)+(U≠1)(3+W(U))+(O≠1)(1+W(O))→K
If θ+K>17
Goto @XD
If X<0:Then:Output(R,θ,"-"):θ+1→θ:End
If U=1 or I≠1:Then:Output(R,θ,I):θ+W(I)→θ:End
If U≠1:Then:Output(R,θ,"√("):Output(R,θ+2,U):θ+3+W(U)→θ:Output(R,θ-1,")"):End
If O≠1:Then:Output(R,θ,"/"):Output(R,θ+1,O):θ+1+W(O)→θ:End
Goto @XR
Lbl @XD
Output(R,θ,round(X,max(0,min(6,16-θ-(X<0)-int(log(max(1,abs(X))))))))
Goto @XR
Lbl @XZ
Output(R,θ,"0")
θ+1→θ
Lbl @XR
""")
    for i, ret in enumerate(_exact_returns, 1):
        T(f"If Z={i}")
        T(f"Goto @{ret}")
    T("Lbl @ST0")
    out, code = code, saved
    return ["#SECTION trig"] + out


def triple() -> None:
    """Random scaled Pythagorean triple: legs A, B (randomly swapped), hyp C."""
    T("""
randInt(1,4)→N
randInt(1,3)→H
H(3(N=1)+5(N=2)+8(N=3)+7(N=4))→A
H(4(N=1)+12(N=2)+15(N=3)+24(N=4))→B
H(5(N=1)+13(N=2)+17(N=3)+25(N=4))→C
If randInt(0,1):Then:A→H:B→A:H→B:End
""")


# =====================================================================
# SPLASH + MAIN MENU (differs per target)
# =====================================================================
SPLASH = {"SAT": "|  Math + R&W  |", "SATMATH": "|  Math        |", "SATTRIG": "|  Trig Center |",
          "SATRW": "|  Read+Write  |"}
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
        ("Trig Center", "TC"),
        ("Math Formulas", "FA"),
        ("R&W Guide", "RW"),
        ("Practice Quiz", "PQ"),
        ("Strategy/Help", "SH"),
        ("Quit", "QT"),
    ])
    menu("PQ", "PRACTICE QUIZ", [
        ("Math (random)", "QM"),
        ("Trig", "TQ"),
        ("Grammar", "QG"),
        ("Main Menu", "MM"),
    ])
    menu("SH", "STRATEGY + HELP", [
        ("Test Strategy", "TS"),
        ("How To Use", "HU"),
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
elif PROG_NAME == "SATTRIG":
    # the trig center is the main menu; TC and PQ are aliases so shared code can jump back
    T("Lbl @MM")
    T("Lbl @PQ")
    menu("TC", "SAT TRIG CENTER", [
        ("Any triangle", "TA"),
        ("Right triangle", "T1"),
        ("Unit circle", "T3"),
        ("Trig tools", "T4"),
        ("Learn trig", "T5"),
        ("Trig quiz", "TQ"),
        ("Quit", "QT"),
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
] + ([("Right triangle", "T1")] if "trig" in CFG["sections"] else []) + [
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
Disp RRT/2
Disp "SECTOR AREA / π"
Disp RRT/(2π)►Frac
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
# TRIG CENTER
# Variables: callers use A-H, M, N, P, S, V (+ T/L in the quiz). The exact()
# routine owns I J K O Q U W Y X R Z θ, so nothing here keeps a value in
# those across an exact() call.
# =====================================================================
section("trig")
if PROG_NAME != "SATTRIG":
    menu("TC", "TRIG CENTER", [
        ("Any triangle", "TA"),
        ("Right triangle", "T1"),
        ("Unit circle", "T3"),
        ("Trig tools", "T4"),
        ("Learn trig", "T5"),
        ("Trig quiz", "TQ"),
        ("Main Menu", "MM"),
    ])

# ---------- Right triangle: any 2 sides, or 1 side + 1 angle ----------
T("""
Lbl @T1
ClrHome
Disp "RIGHT TRIANGLE","legs a,b hyp c","0 = unknown"
Input "a=",A
Input "b=",B
Input "c=",C
Input "angle A°=",D
abs(A)→A
abs(B)→B
abs(C)→C
If D≤0 or D≥90:0→D
If D
Then
If A
Then
A/tan(D°)→B
A/sin(D°)→C
Else
If B
Then
Btan(D°)→A
B/cos(D°)→C
Else
Csin(D°)→A
Ccos(D°)→B
End
End
Else
If not(C):√(A²+B²)→C
If not(A) and C>B:√(C²-B²)→A
If not(B) and C>A:√(C²-A²)→B
End
ClrHome
If A≤0 or B≤0 or C≤max(A,B)
Goto @T1X
45/tan⁻¹(1)→F
Ftan⁻¹(A/B)→E
Output(1,1,"a=")
""")
exact("A", 1, 3)
T('Output(2,1,"b=")')
exact("B", 2, 3)
T('Output(3,1,"c=")')
exact("C", 3, 3)
T("""
Output(4,1,"angle A=")
Output(4,9,round(E,4))
Output(5,1,"angle B=")
Output(5,9,round(90-E,4))
Output(6,1,"area=")
""")
exact("AB/2", 6, 6)
T("""
Output(7,1,"perim=")
Output(7,7,round(A+B+C,4))
Output(8,1,"ENTER: trig")
Pause
ClrHome
Output(1,1,"TRIG RATIOS")
Output(2,1,"sin A=")
""")
exact("A/C", 2, 7)
T('Output(3,1,"cos A=")')
exact("B/C", 3, 7)
T('Output(4,1,"tan A=")')
exact("A/B", 4, 7)
T('Output(5,1,"sin B=")')
exact("B/C", 5, 7)
T('Output(6,1,"cos B=")')
exact("A/C", 6, 7)
T('Output(7,1,"tan B=")')
exact("B/A", 7, 7)
T("""
Output(8,1,"ENTER: notes")
Pause
ClrHome
Output(1,1,"NOTES")
Output(2,1,"sinA = cosB")
Output(3,1," since A+B=90°")
Output(4,1,"sin²A+cos²A=1")
If abs(E-45)<.0001:Output(6,1,"45-45-90 tri!")
If abs(E-30)<.0001 or abs(E-60)<.0001:Output(6,1,"30-60-90 tri!")
If not(fPart(round(A,6))+fPart(round(B,6))+fPart(round(C,6))):Output(7,1,"Pythag. triple!")
Pause
Goto @TC
Lbl @T1X
Disp "NEED 2 SIDES, OR","1 SIDE + ANGLE A"
Pause
Goto @TC
""")

# ---------- Any triangle: enter whatever you know ----------
# L₆ holds up to two solutions: L₆(1..3) sides a,b,c, L₆(4..6) angles A,B,C
# (degrees) for solution 1, and L₆(7..12) the same for solution 2.
def tri_load(slot) -> None:
    """Solution `slot` (number, or the variable H) -> A,B,C sides and D,E,F angles."""
    for i, v in enumerate("ABCDEF", 1):
        idx = f"6{slot}-{6 - i}" if isinstance(slot, str) else str(6 * (slot - 1) + i)
        T(f"L₆({idx.replace('-0', '')})→{v}")


def tri_store(slot: int) -> None:
    for i, v in enumerate("ABCDEF", 1):
        T(f"{v}→L₆({6 * (slot - 1) + i})")


def tri_angles() -> None:
    """Sides A,B,C -> angles D,E,F (law of cosines)."""
    T("""
45/tan⁻¹(1)→M
Mcos⁻¹(max(~1,min(1,(B²+C²-A²)/(2BC))))→D
Mcos⁻¹(max(~1,min(1,(A²+C²-B²)/(2AC))))→E
180-D-E→F
""")


def tri_sas() -> None:
    """Side P is unknown, the other two sides and angle P are known: law of cosines."""
    T("""
L₆(1)+L₆(2)+L₆(3)-L₆(P)→M
L₆(1)²+L₆(2)²+L₆(3)²-L₆(P)²→N
√(max(0,N-(M²-N)cos(L₆(P+3)°)))→L₆(P)
""")


def tri_tan(row: int, ang: str, name: str) -> None:
    T(f'Output({row},1,"tan {name}=")')
    T(f"If abs(cos({ang}°))<.000000001")
    T(f"Goto @TU{name}")
    exact(f"tan({ang}°)", row, 7)
    T(f"Goto @TV{name}")
    T(f"Lbl @TU{name}")
    T(f'Output({row},7,"undefined")')
    T(f"Lbl @TV{name}")


T("""
Lbl @TA
ClrHome
Disp "ENTER KNOWN, 0=?"
Input "side a=",A
Input "side b=",B
Input "side c=",C
Input "angle A°=",D
Input "angle B°=",E
Input "angle C°=",F
Input "area=",G
{abs(A),abs(B),abs(C),D,E,F,0,0,0,0,0,0}→L₆
For(I,4,6)
If L₆(I)≤0 or L₆(I)≥180:0→L₆(I)
End
abs(G)→G
0→V
(L₆(1)>0)+(L₆(2)>0)+(L₆(3)>0)→S
(L₆(4)>0)+(L₆(5)>0)+(L₆(6)>0)→P
If P=2
Then
180-L₆(4)-L₆(5)-L₆(6)→M
For(I,4,6)
If not(L₆(I)):M→L₆(I)
End
3→P
If M≤0:~1→P
End
If P=3 and abs(L₆(4)+L₆(5)+L₆(6)-180)>.000001:~1→P
If P<0
Goto @TXA
If S=3
Goto @TSS
If P=3
Goto @TAA
If S=2 and P=1
Goto @TS2
If S=2 and not(P) and G>0
Goto @TSK
If S=1 and P=1 and G>0
Goto @TS1
Goto @TXN
""")

# --- 3 sides
T("""
Lbl @TSS
""")
tri_load(1)
T("""
If A+B≤C or A+C≤B or B+C≤A
Goto @TXT
""")
tri_angles()
tri_store(1)
T("""
1→N
Goto @TOU
""")

# --- 3 angles (+ a side, or the area, or nothing = shape only)
T("""
Lbl @TAA
""")
tri_load(1)
T("""
If S
Then
If C:C/sin(F°)→M
If B:B/sin(E°)→M
If A:A/sin(D°)→M
Else
If G
Then
√(2G/(sin(D°)sin(E°)sin(F°)))→M
Else
1/min(sin(D°),min(sin(E°),sin(F°)))→M
1→V
End
End
Msin(D°)→A
Msin(E°)→B
Msin(F°)→C
""")
tri_store(1)
T("""
1→N
Goto @TOU
""")

# --- 2 sides + 1 angle: SAS if the angle is between them, else SSA
T("""
Lbl @TS2
For(I,1,3)
If L₆(I+3):I→P
End
If L₆(P)
Goto @TSA
""")
tri_sas()
tri_load(1)
tri_angles()
tri_store(1)
T("""
1→N
Goto @TOU
Lbl @TSA
For(I,1,3)
If I≠P and L₆(I)>0:I→H
End
6-P-H→T
L₆(H)sin(L₆(P+3)°)/L₆(P)→M
If M>1.000000001
Goto @TXT
If M>.999999999:1→M
45/tan⁻¹(1)→F
Fsin⁻¹(M)→D
180-D→E
180-L₆(P+3)-D→C
If C≤.000001
Goto @TXT
D→L₆(H+3)
C→L₆(T+3)
L₆(P)sin(C°)/sin(L₆(P+3)°)→L₆(T)
1→N
If L₆(P+3)+E<179.999999 and E-D>.000001
Then
For(I,1,6):L₆(I)→L₆(I+6):End
E→L₆(H+9)
180-L₆(P+3)-E→C
C→L₆(T+9)
L₆(P)sin(C°)/sin(L₆(P+3)°)→L₆(T+6)
2→N
End
Goto @TOU
""")

# --- 2 sides + area: the angle between them is θ or 180-θ
T("""
Lbl @TSK
For(I,1,3)
If not(L₆(I)):I→P
End
L₆(1)+L₆(2)+L₆(3)→M
L₆(1)²+L₆(2)²+L₆(3)²→N
4G/(M²-N)→M
If M>1.000000001
Goto @TXT
If M>.999999999:1→M
45/tan⁻¹(1)→F
Fsin⁻¹(min(M,1))→S
1→H
If abs(S-90)>.000001
Then
180-S→L₆(P+3)
""")
tri_sas()
tri_load(1)
tri_angles()
tri_store(2)
T("""
0→L₆(P)
2→H
End
S→L₆(P+3)
""")
tri_sas()
tri_load(1)
tri_angles()
tri_store(1)
T("""
H→N
Goto @TOU
""")

# --- 1 side + 1 angle next to it + area -> the other side, then SAS
T("""
Lbl @TS1
For(I,1,3)
If L₆(I):I→H
If L₆(I+3):I→P
End
If H=P
Goto @TXN
6-H-P→T
2G/(L₆(H)sin(L₆(P+3)°))→L₆(T)
""")
tri_sas()
tri_load(1)
tri_angles()
tri_store(1)
T("""
1→N
Goto @TOU
""")

# --- errors
T("""
Lbl @TXA
ClrHome
Disp "ANGLES MUST ADD","UP TO 180°"
Pause
Goto @TC
Lbl @TXT
ClrHome
Disp "NO TRIANGLE FITS","THIS INFO","","(check sides:","a+b must be > c)"
Pause
Goto @TC
Lbl @TXN
ClrHome
Disp "NOT ENOUGH INFO","Give 3 things:","3 sides, or","2 sides+1 angle,","or 2 angles and","a side or area.","(2 sides + area","also works)"
Pause
Goto @TC
""")

# --- results: 4 pages per solution
T("""
Lbl @TOU
1→H
Lbl @TO1
""")
tri_load("H")
T("""
ABsin(F°)/2→G
ClrHome
If N=2:Then:Output(1,1,"SOLUTION   OF 2"):Output(1,10,H):Else:Output(1,1,"TRIANGLE"):End
If V:Output(1,1,"SIDES = RATIOS")
Output(2,1,"a=")
""")
exact("A", 2, 3)
T('Output(3,1,"b=")')
exact("B", 3, 3)
T('Output(4,1,"c=")')
exact("C", 4, 3)
T("""
Output(5,1,"angle A=")
Output(5,9,round(D,4))
Output(6,1,"angle B=")
Output(6,9,round(E,4))
Output(7,1,"angle C=")
Output(7,9,round(F,4))
max(D,max(E,F))→M
If abs(M-90)<.000001:Output(8,1,"right")
If M>90.000001:Output(8,1,"obtuse")
If M<89.999999:Output(8,1,"acute")
(abs(A-B)<.000001max(A,B))+(abs(B-C)<.000001max(B,C))+(abs(A-C)<.000001max(A,C))→M
If M=3:Output(8,8,"equilat.")
If M=1:Output(8,8,"isosceles")
If not(M):Output(8,8,"scalene")
Pause
ClrHome
Output(1,1,"area=")
""")
exact("G", 1, 6)
T('Output(2,1,"perim=")')
exact("A+B+C", 2, 7)
T('Output(3,1,"h(a)=")')
exact("2G/A", 3, 6)
T('Output(4,1,"h(b)=")')
exact("2G/B", 4, 6)
T('Output(5,1,"h(c)=")')
exact("2G/C", 5, 6)
T('Output(6,1,"circumR=")')
exact("A/(2sin(D°))", 6, 9)
T('Output(7,1,"inradius=")')
exact("2G/(A+B+C)", 7, 10)
T("""
Output(8,1,"h=height to side")
Pause
ClrHome
Output(1,1,"sin A=")
""")
exact("sin(D°)", 1, 7)
T('Output(2,1,"sin B=")')
exact("sin(E°)", 2, 7)
T('Output(3,1,"sin C=")')
exact("sin(F°)", 3, 7)
T('Output(4,1,"cos A=")')
exact("cos(D°)", 4, 7)
T('Output(5,1,"cos B=")')
exact("cos(E°)", 5, 7)
T('Output(6,1,"cos C=")')
exact("cos(F°)", 6, 7)
T("""
Output(8,1,"ENTER: tan")
Pause
ClrHome
""")
tri_tan(1, "D", "A")
tri_tan(2, "E", "B")
tri_tan(3, "F", "C")
T("""
Output(5,1,"a/sinA = b/sinB")
Output(6,1," = c/sinC")
Output(7,1," =")
""")
exact("A/sin(D°)", 7, 4)
T("""
If H<N:Output(8,1,"ENTER: next sol.")
Pause
H+1→H
If H≤N
Goto @TO1
Goto @TC
""")


# ---------- Special right triangles ----------
menu("T2", "SPECIAL RIGHT", [
    ("30-60-90", "S1"),
    ("45-45-90", "S2"),
    ("Back", "T4"),
])
menu("S1", "30-60-90 KNOWN:", [
    ("Short leg  x", "S3"),
    ("Long leg x√(3)", "S4"),
    ("Hypotenuse 2x", "S5"),
    ("Back", "T2"),
])
T("""
Lbl @S3
1→N
Goto @S6
Lbl @S4
2→N
Goto @S6
Lbl @S5
3→N
Lbl @S6
ClrHome
Disp "30-60-90","(4√(3) is ok)"
Input "length=",V
abs(V)→P
If N=2:P/√(3)→P
If N=3:P/2→P
ClrHome
Output(1,1,"30-60-90")
Output(2,1,"short=")
""")
exact("P", 2, 7)
T('Output(3,1,"long =")')
exact("P√(3)", 3, 7)
T('Output(4,1,"hyp  =")')
exact("2P", 4, 7)
T('Output(5,1,"area =")')
exact("P²√(3)/2", 5, 7)
T("""
Output(6,1,"perim=")
Output(6,7,round(P(3+√(3)),4))
Output(7,1,"short is opp 30°")
Output(8,1,"long is opp 60°")
Pause
Goto @S1
""")
menu("S2", "45-45-90 KNOWN:", [
    ("Leg  x", "S7"),
    ("Hyp  x√(2)", "S8"),
    ("Back", "T2"),
])
T("""
Lbl @S7
1→N
Goto @S9
Lbl @S8
2→N
Lbl @S9
ClrHome
Disp "45-45-90","(4√(2) is ok)"
Input "length=",V
abs(V)→P
If N=2:P/√(2)→P
ClrHome
Output(1,1,"45-45-90")
Output(2,1,"legs =")
""")
exact("P", 2, 7)
T('Output(3,1,"hyp  =")')
exact("P√(2)", 3, 7)
T('Output(4,1,"area =")')
exact("P²/2", 4, 7)
T("""
Output(5,1,"perim=")
Output(5,7,round(P(2+√(2)),4))
Output(7,1,"isosceles right")
Output(8,1,"triangle")
Pause
Goto @S2
""")

# ---------- Unit circle explorer ----------
menu("T3", "UNIT CIRCLE", [
    ("Angle in deg", "U1"),
    ("Angle in rad", "U2"),
    ("Values table", "TL3"),
    ("Back", "TC"),
])
T("""
Lbl @U1
ClrHome
Disp "UNIT CIRCLE"
Input "angle°=",D
Goto @U3
Lbl @U2
ClrHome
Disp "UNIT CIRCLE","(π key is ok)"
Input "angle rad=",V
180V/π→D
Lbl @U3
round(D-360int(D/360),9)→E
If E≥360:E-360→E
sin(E°)→S
cos(E°)→C
S(abs(S)>.000000001)→S
C(abs(C)>.000000001)→C
E→G
If E>90 and E≤180:180-E→G
If E>180 and E≤270:E-180→G
If E>270:360-E→G
ClrHome
Output(1,1,"angle=")
Output(1,7,round(E,4))
Output(2,1,"rad/π=")
""")
exact("E/180", 2, 7)
T("""
If fPart(E/90):Then:Output(3,1,"quadrant"):Output(3,10,1+int(E/90)):Else:Output(3,1,"on an axis"):End
Output(4,1,"ref angle=")
Output(4,11,round(G,4))
Output(5,1,"sin=")
""")
exact("S", 5, 5)
T('Output(6,1,"cos=")')
exact("C", 6, 5)
T("""
Output(7,1,"tan=")
If not(C)
Goto @U4
""")
exact("S/C", 7, 5)
T("""
Goto @U5
Lbl @U4
Output(7,5,"undefined")
Lbl @U5
Output(8,1,"sin")
Output(8,4,sub("0+-",1+(S>0)+2(S<0),1))
Output(8,6,"cos")
Output(8,9,sub("0+-",1+(C>0)+2(C<0),1))
Output(8,11,"tan")
Output(8,14,sub("0+-?",1+(SC>0)+2(SC<0)+3not(C),1))
Pause
Goto @T3
""")

# ---------- Trig tools ----------
menu("T4", "TRIG TOOLS", [
    ("Special tri", "T2"),
    ("Cofunction eqn", "CO"),
    ("Law of sines", "LS"),
    ("Law of cosines", "LC"),
    ("Similar tri", "SM"),
    ("Back", "TC"),
])
T("""
Lbl @CO
ClrHome
Disp "sin(ax+b)°","=cos(cx+d)°"
Input "a=",A
Input "b=",B
Input "c=",C
Input "d=",D
ClrHome
If A+C
Then
(90-B-D)/(A+C)→V
Disp "angles sum to 90"
Disp "x="
Disp V►Frac
Disp "1st angle (°)"
Disp AV+B►Frac
Disp "2nd angle (°)"
Disp CV+D►Frac
Else
Disp "a+c CAN'T BE 0"
End
Pause
Goto @T4
Lbl @LS
ClrHome
Disp "LAW OF SINES","2 angles + side","a (opposite A)"
Input "angle A°=",A
Input "angle B°=",B
Input "side a=",P
ClrHome
180-A-B→C
If A≤0 or B≤0 or C≤0 or P≤0
Goto @LSX
Psin(B°)/sin(A°)→M
Psin(C°)/sin(A°)→N
Disp "angle C (°)"
Disp C
Disp "side b"
Disp round(M,6)
Disp "side c"
Disp round(N,6)
Disp "area"
Disp round(PMsin(C°)/2,6)
Pause
Goto @T4
Lbl @LSX
Disp "ANGLES MUST SUM","< 180, side > 0"
Pause
Goto @T4
""")
menu("LC", "LAW OF COSINES", [
    ("2 sides+angle", "C1"),
    ("3 sides", "C2"),
    ("Back", "T4"),
])
T("""
Lbl @C1
ClrHome
Disp "SIDES a, b AND","angle C between"
Input "side a=",A
Input "side b=",B
Input "angle C°=",D
ClrHome
If A≤0 or B≤0 or D≤0 or D≥180
Goto @CX
√(A²+B²-2ABcos(D°))→C
45/tan⁻¹(1)→F
Fcos⁻¹((B²+C²-A²)/(2BC))→E
Disp "side c"
Disp round(C,6)
Disp "angle A (°)"
Disp round(E,4)
Disp "angle B (°)"
Disp round(180-D-E,4)
Disp "area"
Disp round(ABsin(D°)/2,6)
Pause
Goto @LC
Lbl @C2
ClrHome
Disp "3 SIDES a, b, c"
Input "a=",A
Input "b=",B
Input "c=",C
ClrHome
If A≤0 or B≤0 or C≤0 or A+B≤C or A+C≤B or B+C≤A
Goto @CX
45/tan⁻¹(1)→F
Fcos⁻¹((B²+C²-A²)/(2BC))→D
Fcos⁻¹((A²+C²-B²)/(2AC))→E
(A+B+C)/2→S
Disp "angle A (°)"
Disp round(D,4)
Disp "angle B (°)"
Disp round(E,4)
Disp "angle C (°)"
Disp round(180-D-E,4)
Disp "area (Heron)"
Disp round(√(S(S-A)(S-B)(S-C)),6)
Pause
Goto @LC
Lbl @CX
Disp "NOT A VALID","TRIANGLE"
Pause
Goto @LC
Lbl @SM
ClrHome
Disp "SIMILAR TRI'S","matching sides:"
Input "small side=",A
Input "big side=",B
Input "other small=",C
ClrHome
If A
Then
B/A→M
Disp "SCALE k=big/sm"
Disp M►Frac
Disp "MATCHING BIG"
Disp CM►Frac
Disp "AREA RATIO k²"
Disp M²►Frac
Disp "VOLUME RATIO k³"
Disp M³►Frac
Else
Disp "SIDE CAN'T BE 0"
End
Pause
Goto @T4
""")

# ---------- Lessons ----------
menu("T5", "LEARN TRIG", [
    ("SOH CAH TOA", "TL1"),
    ("Special tri", "TL2"),
    ("Unit circle", "TL3"),
    ("Radians/arcs", "TL4"),
    ("Identities", "TL5"),
    ("Traps + tips", "TL6"),
    ("Back", "TC"),
])

pager("TL1", "SOH CAH TOA", [
    ["For angle θ in a",
     " right triangle:",
     "sin = opp/hyp",
     "cos = adj/hyp",
     "tan = opp/adj",
     "hyp: across 90°"],
    ["OPP = side",
     " across from θ",
     "ADJ = side that",
     " touches θ",
     " (not the hyp)",
     "Use YOUR angle!"],
    ["Ex: legs 3, 4,",
     " hyp 5. Angle A",
     " is opp side 3:",
     "sin A = 3/5",
     "cos A = 4/5",
     "tan A = 3/4"],
    ["Find a side:",
     " opp = hyp*sin",
     " adj = hyp*cos",
     " opp = adj*tan",
     "Find an angle:",
     " sin⁻¹, cos⁻¹.."],
    ["SIMILAR tri's",
     " have the SAME",
     " trig ratios.",
     "sin A = 3/5 in",
     " one means 3/5",
     " in every copy."],
    ["Ratios depend on",
     " the ANGLE only,",
     " not the size.",
     "Acute angle:",
     " 0<sin,cos<1",
     " tan can be >1"],
], "T5")

pager("TL2", "SPECIAL TRI", [
    ["45-45-90",
     " legs:  x, x",
     " hyp:   x√(2)",
     "Isosceles right",
     " triangle",
     "hyp = leg*√(2)"],
    ["30-60-90",
     " short: x",
     " long:  x√(3)",
     " hyp:   2x",
     "short is opp 30°",
     "long is opp 60°"],
    ["Going backward:",
     "45: leg=hyp/√(2)",
     "  = hyp*√(2)/2",
     "30-60-90:",
     " short = hyp/2",
     " short=long/√(3)"],
    ["Spot them:",
     "angle 30 or 60",
     " or hyp=2*short",
     " -> 30-60-90",
     "angle 45 or",
     " equal legs ->45"],
    ["Equilateral tri",
     " split in half =",
     " two 30-60-90s",
     "height=s√(3)/2",
     "area=s²√(3)/4",
     "Sq. diag=s√(2)"],
    ["Pythag. triples",
     " 3-4-5",
     " 5-12-13",
     " 8-15-17",
     " 7-24-25",
     "...and multiples"],
], "T5")

pager("TL3", "UNIT CIRCLE", [
    ["Unit circle r=1",
     "Point at angle θ",
     " = (cos θ,sin θ)",
     "x = cos, y = sin",
     "tan = sin/cos",
     " = slope of ray"],
    ["θ  sin    cos",
     "0  0      1",
     "30 1/2    √(3)/2",
     "45 √(2)/2 √(2)/2",
     "60 √(3)/2 1/2",
     "90 1      0"],
    ["θ   tan",
     "0   0",
     "30  √(3)/3",
     "45  1",
     "60  √(3)",
     "90  undefined"],
    ["Signs by quad.:",
     "Q1 0-90:  all +",
     "Q2 90-180: sin +",
     "Q3 180-270:tan +",
     "Q4 270-360:cos +",
     "Mnemonic: ASTC"],
    ["Reference angle:",
     " Q2: 180-θ",
     " Q3: θ-180",
     " Q4: 360-θ",
     "Value = ref's",
     " value + sign"],
    ["Ex: sin 150°",
     " Q2, ref 30°",
     " sin + in Q2",
     " = 1/2",
     "Ex: cos 240°",
     " Q3,ref 60: -1/2"],
    ["Coterminal:",
     " +/- 360° (2π)",
     " = same point",
     "sin(-θ) = -sin θ",
     "cos(-θ) = cos θ",
     ""],
], "T3" if PROG_NAME == "SATTRIG" else "T5")

pager("TL4", "RADIANS", [
    ["π rad = 180°",
     "deg->rad: *π/180",
     "rad->deg: *180/π",
     "full turn = 2π",
     "1 rad ~ 57.3°",
     ""],
    ["30° = π/6",
     "45° = π/4",
     "60° = π/3",
     "90° = π/2",
     "180° = π",
     "360° = 2π"],
    ["120° = 2π/3",
     "135° = 3π/4",
     "150° = 5π/6",
     "210° = 7π/6",
     "270° = 3π/2",
     "330° = 11π/6"],
    ["Arc length:",
     " s = rθ  (rad)",
     " s=(deg/360)2πr",
     "Sector area:",
     " A = (1/2)r²θ",
     " A=(deg/360)πr²"],
    ["Central angle",
     " in radians =",
     " arc / radius",
     "Ex: arc 6, r 3",
     " -> θ = 2 rad",
     ""],
    ["MODE matters!",
     "sin(30) in RAD",
     " mode = -.988",
     "Type 30° (° is",
     " in 2nd APPS)",
     " works any mode"],
], "T5")

pager("TL5", "IDENTITIES", [
    ["COFUNCTIONS:",
     "sin x=cos(90-x)",
     "cos x=sin(90-x)",
     "So if sin A =",
     " cos B, then",
     " A + B = 90°"],
    ["SAT favorite:",
     "sin(2x+10)°",
     " = cos(3x-5)°",
     "2x+10+3x-5=90",
     "5x+5=90",
     "x = 17"],
    ["In a right tri",
     " w/ acute A, B:",
     "sin A = cos B",
     "cos A = sin B",
     "tan A = 1/tan B",
     ""],
    ["PYTHAGOREAN:",
     "sin²x+cos²x=1",
     "If sin x = 3/5:",
     " cos²x=1-9/25",
     "  =16/25",
     " cos x = 4/5"],
    ["tan x=sinx/cosx",
     "sin(-x)=-sin x",
     "cos(-x)= cos x",
     "sin(180-x)",
     " = sin x",
     "cos(180-x)=-cosx"],
], "T5")

pager("TL6", "TRIG TRAPS", [
    ["TRAP: wrong side",
     "OPP and ADJ",
     " change with the",
     " angle you use.",
     "Re-label for",
     " each angle!"],
    ["TRAP: hyp is",
     " always LONGEST",
     " & opposite 90°",
     "sin, cos never",
     " above 1. An",
     " answer >1=wrong"],
    ["TRAP: deg/rad",
     "Check MODE on a",
     " real calc. This",
     " app uses ° so",
     " it works in",
     " either mode."],
    ["TIP: draw it!",
     "Sketch, label",
     " the angle and",
     " the given sides",
     "Write SOH CAH",
     " TOA above it."],
    ["TIP: no picture?",
     "sin A = 5/13 ->",
     " draw opp 5,",
     " hyp 13, then",
     " adj = 12 by",
     " a²+b²=c²"],
    ["TIP: radian Q?",
     "Change to deg",
     " if it's easier:",
     " π/3 = 60°",
     "TIP: Desmos is",
     " built in. Use!"],
], "T5")

# ---------- Trig quiz: 10 generated question types ----------
T("""
Lbl @TQ
0→L
0→T
Lbl @TN
randInt(1,10)→Z
ClrHome
Disp "","","","","",""
Output(1,1,"TRIG Q")
Output(1,7,T+1)
""")


def t_ratio():
    triple()
    T("""
randInt(1,3)→V
Output(2,1,"Right triangle")
""")
    seg_row(3, ["a=", ("n", "A"), " b=", ("n", "B")])
    seg_row(4, ["c=", ("n", "C"), " (hyp)"])
    T("""
Output(5,1,"A is opp a.")
If V=1:Then:Output(6,1,"Find sin A"):A/C→X:End
If V=2:Then:Output(6,1,"Find cos A"):B/C→X:End
If V=3:Then:Output(6,1,"Find tan A"):A/B→X:End
""")


def t_cofunction():
    T("""
randInt(1,4)→A
randInt(1,4)→C
randInt(2,int(80/(A+C)))→X
90-(A+C)X→N
randInt(0,N)→B
N-B→D
Output(2,1,"Find x if")
""")
    seg_row(3, ["sin(", ("c", "A", "x"), ("t", "B"), ")°"])
    seg_row(4, ["=cos(", ("c", "C", "x"), ("t", "D"), ")°"])


def t_special():
    T("""
randInt(1,4)→V
randInt(2,9)→P
If V≤2 or V=4:Output(2,1,"30-60-90 tri")
If V=3:Output(2,1,"45-45-90 tri")
If V=1
Then
""")
    T("2P→H")
    seg_row(3, ["hyp = ", ("n", "H")])
    T("""
Output(4,1,"Find short leg")
P→X
End
If V=2 or V=4
Then
""")
    seg_row(3, ["short leg = ", ("n", "P")])
    T("""
If V=2:Then:Output(4,1,"Find hyp"):2P→X:End
If V=4:Then:Output(4,1,"Find long leg"):P√(3)→X:End
End
If V=3
Then
""")
    seg_row(3, ["leg = ", ("n", "P")])
    T("""
Output(4,1,"Find hyp")
P√(2)→X
End
Output(5,1,"(4√(2) is ok)")
""")


def t_unit():
    T("""
randInt(0,2)→N
30+15N→B
randInt(0,3)→H
(H=0)B+(H=1)(180-B)+(H=2)(180+B)+(H=3)(360-B)→D
randInt(1,3)→V
If V=1:sin(D°)→X
If V=2:cos(D°)→X
If V=3:tan(D°)→X
Output(2,1,"Exact value of")
""")
    seg_row(3, [("n", "D"), "°:"])
    T("""
If V=1:Output(4,1,"sin")
If V=2:Output(4,1,"cos")
If V=3:Output(4,1,"tan")
Output(5,1,"ex: -√(3)/2")
""")


def t_radians():
    T("""
15randInt(1,24)→D
gcd(D,180)→H
D/H→N
180/H→P
randInt(0,1)→V
If V
Then
Output(2,1,"Write in rad:")
""")
    seg_row(3, [("n", "D"), "° = ?π"])
    T("""
Output(4,1,"Find ?")
D/180→X
Else
Output(2,1,"Write in deg:")
1→θ
If N≠1:Then:Output(3,θ,N):θ+W(N)→θ:End
Output(3,θ,"π")
θ+1→θ
If P≠1:Then:Output(3,θ,"/"):Output(3,θ+1,P):End
Output(4,1,"radians = ?°")
D→X
End
""")


def t_arc():
    T("""
randInt(2,12)→P
15randInt(2,16)→D
randInt(0,1)→V
""")
    seg_row(2, ["Circle r=", ("n", "P")])
    T('Output(3,1,"central angle")')
    seg_row(4, ["= ", ("n", "D"), "°"])
    T("""
If V
Then
Output(5,1,"Arc length = kπ")
DP/180→X
Else
Output(5,1,"Sector area=kπ")
DP²/360→X
End
Output(6,1,"Find k.")
""")


def t_complement():
    triple()
    T("""
randInt(1,2)→V
Output(2,1,"Right triangle,")
""")
    seg_row(3, ["sin A = ", ("n", "A"), "/", ("n", "C")])
    T("""
If V=1:Then:Output(4,1,"Find cos B."):A/C→X:End
If V=2:Then:Output(4,1,"Find cos A."):B/C→X:End
Output(5,1,"(A,B acute)")
""")


def t_missing():
    triple()
    T('Output(2,1,"Right triangle")')
    seg_row(3, ["leg=", ("n", "A"), ", hyp=", ("n", "C")])
    T("""
Output(4,1,"Find other leg")
B→X
""")


def t_tan():
    triple()
    T("""
randInt(1,2)→V
""")
    seg_row(2, ["tan A = ", ("n", "A"), "/", ("n", "B")])
    T("""
Output(3,1,"A is acute.")
If V=1:Then:Output(4,1,"Find sin A"):A/C→X:End
If V=2:Then:Output(4,1,"Find cos A"):B/C→X:End
""")


def t_angle():
    T("""
randInt(2,9)→P
randInt(1,3)→V
2P→H
Output(2,1,"Right triangle")
If V=1
Then
""")
    seg_row(3, ["legs ", ("n", "P"), " and ", ("n", "P")])
    T("""
45→X
End
If V≥2
Then
""")
    seg_row(3, ["hyp=", ("n", "H")])
    T("If V=2")
    T("Then")
    seg_row(4, ["opp A = ", ("n", "P")])
    T("""
30→X
Else
""")
    seg_row(4, ["adj A = ", ("n", "P")])
    T("""
60→X
End
End
Output(5,1,"Find angle A°")
""")


for i, fn in enumerate([t_ratio, t_cofunction, t_special, t_unit, t_radians,
                        t_arc, t_complement, t_missing, t_tan, t_angle], 1):
    qtype(i, fn)

T("""
Input "answer=",G
T+1→T
abs(G-X)<.000001→V
ClrHome
If V
Then
L+1→L
Output(1,1,"CORRECT!")
Else
Output(1,1,"NOT QUITE.")
End
Output(3,1,"answer:")
""")
exact("X", 3, 9)
T("""
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
Goto @TN
Goto @QF
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
                    # the Pause token's name includes its trailing space; without
                    # it the encoder spells P,a,u,s,e (ERR:SYNTAX on the calculator)
                    part = re.sub(r"Pause(?! )", "Pause ", part)
                    out += encode(part.replace("π", "pi"), trie=trie, mode="max")[0]
            else:  # string literal
                j = 0
                while j < len(part):
                    if part.startswith("√(", j):
                        out += b"\xbc"
                        j += 2
                    elif part.startswith("⁻¹", j):
                        out += b"\x0c"
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
    lines = select_sections(exact_routine() + code, CFG["sections"])
    if CFG["upper"]:
        lines = [upper_strings(l) for l in lines]
    errs = check_structure(lines)
    if errs:
        sys.exit("\n".join(errs))
    src = "\n".join(lines)
    (HERE / "source").mkdir(exist_ok=True)
    (HERE / "source" / f"{PROG_NAME}.txt").write_text(src + "\n", encoding="utf-8")
    data = tokenize(lines)
    errs = check_tokens(data)
    if errs:
        sys.exit("\n".join(errs))
    prog = TIProgram(name=PROG_NAME)
    prog.data = data
    out = HERE / ("TI-84 Plus CE" if PROG_NAME == "SAT" else "TI-84 Plus (older models)")
    out.mkdir(exist_ok=True)
    prog.save(str(out / f"{PROG_NAME}.8xp"), model=TI_84P)
    print(f"{PROG_NAME:8} {len(lines):5} lines {len(data):6} bytes")


# Every multi-character token allowed in code (outside strings). Anything else
# means the tokenizer glued characters into a token we did not intend, like
# "R²T" becoming the statistics variable R² followed by T.
CODE_TOKENS = {
    "►Frac", "round(", "max(", "min(", "median(", "mean(", " or ", " and ", "L₆", "not(", "If ", "Then",
    "Else", "While ", "Repeat ", "For(", "End", "Lbl ", "Goto ", "Input ", "Disp ", "Output(", "ClrHome",
    "SortA(", "Menu(", "int(", "abs(", "dim(", "sum(", "fPart(", "gcd(", "randInt(", "sub(", "√(", "log(",
    "sin(", "sin⁻¹(", "cos(", "cos⁻¹(", "tan(", "tan⁻¹(", "DelVar ", "getKey", "⁻¹", "Pause", "\n",
}


def check_tokens(data: bytes) -> list[str]:
    from tivars.models import TI_84P
    from tivars.types import TIProgram

    prog = TIProgram(name="CHECK")
    prog.data = data
    errs, in_str, line = [], False, 1
    for tok in prog.tokens():
        disp = tok.langs["en"].display
        if tok.bits == b"\x3f":
            in_str, line = False, line + 1
        elif tok.bits == b"\x2a":
            in_str = not in_str
        elif tok.bits == b"\x04":
            in_str = False
        elif not in_str and len(disp) > 1 and disp.strip() not in CODE_TOKENS and disp not in CODE_TOKENS:
            errs.append(f"line {line}: unexpected token {disp!r} in code")
        elif not in_str and len(disp) == 1 and "a" <= disp <= "z":
            # code never uses lowercase letters; one here means a command name
            # was spelled out letter by letter instead of becoming its token
            errs.append(f"line {line}: lowercase {disp!r} in code")
    return errs


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
