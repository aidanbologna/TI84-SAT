"""Tiny TI-BASIC interpreter for the subset used by build_sat.py, with a 16x8 home screen."""
import math
import random
import re
from fractions import Fraction


class TIError(Exception):
    pass


class OutOfEvents(Exception):
    pass


FUNCS = ["tan⁻¹(", "sin⁻¹(", "cos⁻¹(", "sin(", "cos(", "tan(", "randInt(", "median(", "fPart(", "round(", "mean(", "not(", "abs(", "int(",
         "log(", "gcd(", "max(", "min(", "sum(", "dim(", "sub(", "√("]
TOKEN_RE = re.compile(
    r'\s*(?:(?P<str>"[^"]*"?)|(?P<num>\d+\.?\d*|\.\d+)|(?P<func>' + "|".join(re.escape(f) for f in FUNCS) +
    r')|(?P<word>getKey|and|or|pi)|(?P<list>L₆)|(?P<frac>►Frac)|(?P<var>[A-Zθ])|(?P<op>≠|≤|≥|[-+*/^²³°~=<>(){},π]))')


def lex(s):
    toks, i = [], 0
    while i < len(s):
        if s[i] == " ":
            i += 1
            continue
        m = TOKEN_RE.match(s, i)
        if not m or m.end() == i:
            raise TIError(f"SYNTAX lex at {s[i:]!r} in {s!r}")
        kind = m.lastgroup
        toks.append((kind, m.group(kind)))
        i = m.end()
    return toks


def elementwise(f, a, b=None):
    if b is None:
        return [f(x) for x in a] if isinstance(a, list) else f(a)
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            raise TIError("DIM MISMATCH")
        return [f(x, y) for x, y in zip(a, b)]
    if isinstance(a, list):
        return [f(x, b) for x in a]
    if isinstance(b, list):
        return [f(a, y) for y in b]
    return f(a, b)


def div(x, y):
    if y == 0:
        raise TIError("DIVIDE BY 0")
    return x / y


def power(x, y):
    if x == 0 and y < 0:
        raise TIError("DIVIDE BY 0")
    if x < 0 and y != int(y):
        raise TIError("NONREAL ANS")
    return x ** y


def sqrt(x):
    if x < 0:
        raise TIError("NONREAL ANS")
    return math.sqrt(x)


def fpart(x):
    return x - math.trunc(x)


def tround(x, n=9):
    return round(x, int(n))


class Machine:
    def __init__(self, src, events, degree=False, seed=1):
        self.lines = src.split("\n")
        self.stmts = []
        for n, line in enumerate(self.lines, 1):
            for s in split_stmts(line):
                self.stmts.append((n, s))
        self.labels = {s[4:]: i for i, (n, s) in enumerate(self.stmts) if s.startswith("Lbl ")}
        self.match_blocks()
        self.vars = {c: 0.0 for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZθ"}
        self.lists = {}
        self.events = events if callable(events) else list(events)
        self.degree = degree
        self.rng = random.Random(seed)
        self.screen = [[" "] * 16 for _ in range(8)]
        self.row = 0
        self.snaps = []
        self.warnings = []
        self.steps = 0

    # ---- structure ----
    def match_blocks(self):
        self.end_of, self.else_of, self.opener = {}, {}, {}
        stack = []
        for i, (n, s) in enumerate(self.stmts):
            nxt = self.stmts[i + 1][1] if i + 1 < len(self.stmts) else ""
            if s.startswith("If ") and nxt == "Then":
                stack.append(i)
            elif s.startswith(("While ", "Repeat ", "For(")):
                stack.append(i)
            elif s == "Else":
                self.else_of[stack[-1]] = i
                self.opener[i] = stack[-1]
            elif s == "End":
                o = stack.pop()
                self.end_of[o] = i
                self.opener[i] = o

    # ---- events ----
    def pop(self, kind):
        if callable(self.events):
            return self.events(kind, self)
        if not self.events:
            raise OutOfEvents(kind)
        k, v = self.events[0]
        if k != kind:
            raise TIError(f"script expected {k} but program wants {kind}")
        self.events.pop(0)
        return v(self) if callable(v) else v

    # ---- screen ----
    def snap(self, why):
        self.snaps.append((why, ["".join(r) for r in self.screen]))

    def scroll(self):
        self.screen.pop(0)
        self.screen.append([" "] * 16)
        self.row = 7

    def newline(self):
        self.row += 1
        if self.row > 7:
            self.scroll()

    def put(self, r, c, text, wrap=True):
        for ch in text:
            if c > 15:
                if not wrap:
                    break
                r, c = r + 1, 0
            if r > 7:
                self.warnings.append(f"Output past bottom: {text!r}")
                return
            self.screen[r][c] = ch
            c += 1

    # ---- formatting ----
    def fmt_num(self, x, frac=False):
        if frac:
            f = Fraction(x).limit_denominator(9999)
            if f.denominator != 1 and abs(float(f) - x) < 1e-9 * max(1, abs(x)):
                return ("⁻" if f < 0 else "") + f"{abs(f.numerator)}/{f.denominator}"
        x = round(x, 9 - int(math.floor(math.log10(abs(x)))) if x else 0) if abs(x) > 1e-12 else 0
        s = f"{abs(x):.10g}"
        if "e" in s:
            m, e = s.split("e")
            s = f"{m}E{int(e)}"
        if s.startswith("0."):
            s = s[1:]
        return ("⁻" if x < 0 else "") + s

    def fmt(self, v, frac=False):
        if isinstance(v, str):
            return v
        if isinstance(v, list):
            return "{" + " ".join(self.fmt_num(x, frac) for x in v) + "}"
        return self.fmt_num(v, frac)

    # ---- expression parser ----
    def eval(self, s):
        frac = False
        if s.endswith("►Frac"):
            s, frac = s[:-5], True
        self.toks = lex(s)
        self.p = 0
        v = self.p_or()
        if self.p != len(self.toks):
            raise TIError(f"SYNTAX trailing {self.toks[self.p:]} in {s!r}")
        return v, frac

    def peek(self):
        return self.toks[self.p] if self.p < len(self.toks) else (None, None)

    def take(self, val=None):
        t = self.peek()
        if val is not None and t[1] != val:
            raise TIError(f"SYNTAX expected {val} got {t}")
        self.p += 1
        return t

    def p_or(self):
        v = self.p_and()
        while self.peek() == ("word", "or"):
            self.take()
            v = elementwise(lambda a, b: float(bool(a) or bool(b)), v, self.p_and())
        return v

    def p_and(self):
        v = self.p_rel()
        while self.peek() == ("word", "and"):
            self.take()
            v = elementwise(lambda a, b: float(bool(a) and bool(b)), v, self.p_rel())
        return v

    def p_rel(self):
        v = self.p_add()
        ops = {"=": lambda a, b: a == b, "≠": lambda a, b: a != b, "<": lambda a, b: a < b,
               ">": lambda a, b: a > b, "≤": lambda a, b: a <= b, "≥": lambda a, b: a >= b}
        while self.peek()[0] == "op" and self.peek()[1] in ops:
            f = ops[self.take()[1]]
            v = elementwise(lambda a, b: float(f(a, b)), v, self.p_add())
        return v

    def p_add(self):
        v = self.p_mul()
        while self.peek() in (("op", "+"), ("op", "-")):
            op = self.take()[1]
            r = self.p_mul()
            if isinstance(v, str) or isinstance(r, str):
                if op == "+" and isinstance(v, str) and isinstance(r, str):
                    v = v + r
                    continue
                raise TIError("DATA TYPE")
            v = elementwise((lambda a, b: a + b) if op == "+" else (lambda a, b: a - b), v, r)
        return v

    def starts_atom(self):
        k, t = self.peek()
        return k in ("num", "func", "var", "list", "str") or t in ("(", "{", "π") or (k == "word" and t in ("pi", "getKey"))

    def p_mul(self):
        v = self.p_neg()
        while True:
            k, t = self.peek()
            if (k, t) == ("op", "*"):
                self.take()
                v = elementwise(lambda a, b: a * b, v, self.p_neg())
            elif (k, t) == ("op", "/"):
                self.take()
                v = elementwise(div, v, self.p_neg())
            elif self.starts_atom():
                v = elementwise(lambda a, b: a * b, v, self.p_pow())
            else:
                return v

    def p_neg(self):
        if self.peek() == ("op", "~"):
            self.take()
            return elementwise(lambda a: -a, self.p_neg())
        if self.peek() == ("op", "-"):
            raise TIError("SYNTAX: subtraction used as negation")
        return self.p_pow()

    def p_pow(self):
        v = self.p_post()
        while self.peek() == ("op", "^"):
            self.take()
            if self.peek() == ("op", "~"):
                self.take()
                r = elementwise(lambda a: -a, self.p_post())
            else:
                r = self.p_post()
            v = elementwise(power, v, r)
        return v

    def p_post(self):
        v = self.p_atom()
        while self.peek()[1] in ("²", "³", "°"):
            op = self.take()[1]
            if op == "²":
                v = elementwise(lambda a: a * a, v)
            elif op == "³":
                v = elementwise(lambda a: a ** 3, v)
            elif not self.degree:  # x° means degrees in any mode
                v = elementwise(math.radians, v)
        return v

    def args(self):
        out = [self.p_or()]
        while self.peek() == ("op", ","):
            self.take()
            out.append(self.p_or())
        if self.peek() == ("op", ")"):
            self.take()
        return out

    def p_atom(self):
        k, t = self.take()
        if k == "num":
            return float(t)
        if k == "str":
            return t.strip('"')
        if k == "var":
            return self.vars[t]
        if k == "list":
            if t not in self.lists:
                raise TIError("UNDEFINED list")
            if self.peek() == ("op", "("):  # element access L₆(n)
                self.take()
                idx = self.p_or()
                if self.peek() == ("op", ")"):
                    self.take()
                return self.list_get(t, idx)
            return list(self.lists[t])
        if t in ("pi", "π"):
            return math.pi
        if t == "getKey":
            return float(self.pop("key"))
        if t == "(":
            v = self.p_or()
            if self.peek() == ("op", ")"):
                self.take()
            return v
        if t == "{":
            items = [self.p_or()]
            while self.peek() == ("op", ","):
                self.take()
                items.append(self.p_or())
            if self.peek() == ("op", "}"):
                self.take()
            return items
        if k == "func":
            a = self.args()
            return self.call(t, a)
        raise TIError(f"SYNTAX unexpected {t!r}")

    def call(self, f, a):
        e = elementwise
        if f == "not(":
            return e(lambda x: float(x == 0), a[0])
        if f == "abs(":
            return e(abs, a[0])
        if f == "int(":
            return e(lambda x: float(math.floor(x)), a[0])
        if f == "fPart(":
            return e(fpart, a[0])
        if f == "log(":
            def lg(x):
                if x <= 0:
                    raise TIError("DOMAIN log")
                return math.log10(x)
            return e(lg, a[0])
        if f == "√(":
            return e(sqrt, a[0])
        if f in ("sin(", "cos(", "tan("):
            fn = {"sin(": math.sin, "cos(": math.cos, "tan(": math.tan}[f]
            return e(lambda x: fn(math.radians(x)) if self.degree else fn(x), a[0])
        if f in ("sin⁻¹(", "cos⁻¹("):
            fn = math.asin if f == "sin⁻¹(" else math.acos

            def inv(x):
                if abs(x) > 1:
                    raise TIError("DOMAIN inverse trig")
                return math.degrees(fn(x)) if self.degree else fn(x)
            return e(inv, a[0])
        if f == "tan⁻¹(":
            return e(lambda x: math.degrees(math.atan(x)) if self.degree else math.atan(x), a[0])
        if f == "gcd(":
            def g(x, y):
                if x != int(x) or y != int(y) or x < 0 or y < 0:
                    raise TIError(f"DOMAIN gcd({x},{y})")
                return float(math.gcd(int(x), int(y)))
            return e(g, a[0], a[1])
        if f in ("max(", "min("):
            fn = max if f == "max(" else min
            if len(a) == 1:
                return float(fn(a[0]))
            return e(lambda x, y: fn(x, y), a[0], a[1])
        if f == "mean(":
            return sum(a[0]) / len(a[0])
        if f == "median(":
            s = sorted(a[0])
            n = len(s)
            return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
        if f == "sum(":
            return float(sum(a[0]))
        if f == "dim(":
            return float(len(a[0]))
        if f == "round(":
            return e(lambda x: tround(x, a[1] if len(a) > 1 else 9), a[0])
        if f == "sub(":
            s, st, ln = a
            return s[int(st) - 1:int(st) - 1 + int(ln)]
        if f == "randInt(":
            lo, hi = int(a[0]), int(a[1])
            return float(self.rng.randint(lo, hi))
        raise TIError(f"unknown func {f}")

    def list_get(self, name, idx):
        i = int(idx)
        if idx != i or not 1 <= i <= len(self.lists[name]):
            raise TIError(f"INVALID DIM {name}({idx})")
        return self.lists[name][i - 1]

    def list_set(self, name, idx, v):
        if isinstance(v, list):
            raise TIError("DATA TYPE")
        lst = self.lists.setdefault(name, [])
        i = int(idx)
        if idx != i or not 1 <= i <= len(lst) + 1:
            raise TIError(f"INVALID DIM {name}({idx})")
        if i == len(lst) + 1:
            lst.append(v)
        else:
            lst[i - 1] = v

    def truth(self, s):
        v, _ = self.eval(s)
        if isinstance(v, list):
            raise TIError("DATA TYPE: list as condition")
        return v != 0

    # ---- run ----
    def run(self, max_steps=200000):
        pc = 0
        skip_next = False
        while pc < len(self.stmts):
            self.steps += 1
            if self.steps > max_steps:
                raise TIError("infinite loop?")
            n, s = self.stmts[pc]
            self.cur = (n, s)
            if skip_next:
                skip_next = False
                pc += 1
                continue
            pc = self.exec(pc, s)
            if pc is None:
                return
            if isinstance(pc, tuple):
                pc, skip_next = pc

    def exec(self, pc, s):
        if s.startswith("If "):
            nxt = self.stmts[pc + 1][1] if pc + 1 < len(self.stmts) else ""
            ok = self.truth(s[3:])
            if nxt == "Then":
                if ok:
                    return pc + 2
                if pc in self.else_of:
                    return self.else_of[pc] + 1
                return self.end_of[pc] + 1
            return (pc + 1, not ok)
        if s == "Then":
            return pc + 1
        if s == "Else":
            return self.end_of[self.opener[pc]] + 1
        if s == "End":
            o = self.opener[pc]
            os_ = self.stmts[o][1]
            if os_.startswith("While "):
                return o
            if os_.startswith("Repeat "):
                return pc + 1 if self.truth(os_[7:]) else o + 1
            if os_.startswith("For("):
                var, lo, hi = os_[4:].rstrip(")").split(",")[:3]
                self.vars[var] += 1
                return o + 1 if self.vars[var] <= self.eval(hi)[0] else pc + 1
            return pc + 1
        if s.startswith("While "):
            return pc + 1 if self.truth(s[6:]) else self.end_of[pc] + 1
        if s.startswith("Repeat "):
            return pc + 1
        if s.startswith("For("):
            var, lo, hi = s[4:].rstrip(")").split(",")[:3]
            self.vars[var] = self.eval(lo)[0]
            return pc + 1 if self.vars[var] <= self.eval(hi)[0] else self.end_of[pc] + 1
        if s.startswith("Lbl "):
            return pc + 1
        if s.startswith("Goto "):
            return self.labels[s[5:]]
        if s == "ClrHome":
            self.screen = [[" "] * 16 for _ in range(8)]
            self.row = 0
            return pc + 1
        if s == "Pause":
            self.snap("Pause")
            self.pop("enter")
            return pc + 1
        if s.startswith("Disp "):
            for arg in split_args(s[5:]):
                v, frac = self.eval(arg)
                txt = self.fmt(v, frac)
                if len(txt) > 16:
                    self.warnings.append(f"Disp too wide ({len(txt)}): {txt!r} from {arg}")
                    txt = txt[:15] + "…"
                if self.row > 7:
                    self.scroll()
                    self.warnings.append(f"Disp scrolled screen at line {self.cur[0]}: {txt!r}")
                if isinstance(v, str):
                    self.put(self.row, 0, txt, wrap=False)
                else:
                    self.put(self.row, 16 - len(txt), txt, wrap=False)
                self.row += 1
            return pc + 1
        if s.startswith("Output("):
            r, c, *rest = split_args(s[7:-1] if s.endswith(")") else s[7:])
            r = int(self.eval(r)[0])
            c = int(self.eval(c)[0])
            v, frac = self.eval(",".join(rest))
            if frac:
                raise TIError("►Frac not allowed in Output(")
            if not (1 <= r <= 8 and 1 <= c <= 16):
                raise TIError(f"DOMAIN Output({r},{c})")
            txt = self.fmt(v)
            self.put(r - 1, c - 1, txt)
            return pc + 1
        if s.startswith("Input "):
            prompt, var = split_args(s[6:])
            prompt = prompt.strip('"')
            if self.row > 7:
                self.scroll()
            typed = self.pop("input")
            self.put(self.row, 0, prompt + typed.replace("~", "⁻"), wrap=True)
            self.row += 1 + (len(prompt) + len(typed) - 1) // 16
            if self.row > 7:
                self.row = 8
            v, _ = self.eval(typed)
            if var == "L₆":
                if not isinstance(v, list):
                    raise TIError("DATA TYPE list input")
                self.lists["L₆"] = v
            else:
                if isinstance(v, list):
                    raise TIError("DATA TYPE")
                self.vars[var] = v
            return pc + 1
        if s.startswith("Menu("):
            parts = split_args(s[5:-1] if s.endswith(")") else s[5:])
            title = parts[0].strip('"')
            items = [(parts[i].strip('"'), parts[i + 1]) for i in range(1, len(parts), 2)]
            self.snaps.append(("Menu", [title] + [f"{i}:{t}" for i, (t, _) in enumerate(items, 1)]))
            choice = self.pop("menu")
            if isinstance(choice, str):
                idx = [t.upper() for t, _ in items].index(choice.upper())
            else:
                idx = choice - 1
            return self.labels[items[idx][1]]
        if s.startswith("SortA("):
            self.lists["L₆"].sort()
            return pc + 1
        if s.startswith("DelVar "):
            self.lists.pop("L₆", None)
            return pc + 1
        if "→" in s:
            expr, var = s.rsplit("→", 1)
            v, _ = self.eval(expr)
            if var.startswith("L₆("):
                idx, _ = self.eval(var[3:-1] if var.endswith(")") else var[3:])
                self.list_set("L₆", idx, v)
            elif var == "L₆":
                self.lists[var] = v
            else:
                if isinstance(v, list):
                    raise TIError("DATA TYPE")
                self.vars[var] = v
            return pc + 1
        raise TIError(f"unknown statement {s!r}")


def split_stmts(line):
    out, cur, ins = [], "", False
    for c in line:
        if c == '"':
            ins = not ins
        if c == ":" and not ins:
            out.append(cur)
            cur = ""
        else:
            cur += c
    out.append(cur)
    return [x for x in out if x]


def split_args(s):
    out, cur, depth, ins = [], "", 0, False
    for c in s:
        if c == '"':
            ins = not ins
        if not ins:
            if c in "({":
                depth += 1
            elif c in ")}":
                depth -= 1
            elif c == "," and depth == 0:
                out.append(cur)
                cur = ""
                continue
        cur += c
    out.append(cur)
    return out


def render(snaps):
    out = []
    for why, rows in snaps:
        if why == "Menu":
            out.append("  MENU: " + rows[0] + "\n" + "\n".join("    " + r for r in rows[1:]))
        else:
            out.append("  +----------------+\n" + "\n".join("  |" + r + "|" for r in rows) + "\n  +----------------+")
    return "\n".join(out)
