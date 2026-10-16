import ast, json, os, time

SINGLETONS = ["Load","Store","Del","Add","Sub","Mult","Div","Mod","Pow","LShift",
  "RShift","BitOr","BitXor","BitAnd","MatMult","FloorDiv","USub","UAdd","Not",
  "Invert","And","Or","Eq","NotEq","Lt","LtE","Gt","GtE","Is","IsNot","In","NotIn"]
SING = {n: i for i, n in enumerate(SINGLETONS)}
# Base-33 id alphabet: uppercase MINUS C, F, M (those are node opcodes,
# so they must never appear inside an id run).
IDCH = "0123456789ABDEGHIJKLMNOPQRSTUVWXYZ"
def u36(n):
    assert n >= 0
    if n == 0: return "0"
    out = ""
    while n: out = IDCH[n % 33] + out; n //= 33
    return out
def pid(r):
    v = 0
    for c in r: v = v * 33 + IDCH.index(c)
    return v

class Dict:
    def __init__(self): self.d = {}; self.r = []
    def id(self, s):
        if s not in self.d: self.d[s] = len(self.d); self.r.append(s)
        return self.d[s]

class Enc:
    def __init__(self, D): self.D = D
    def S(self, s): return "d" + u36(self.D.id(s))
    def num(self, v): return "#" + repr(v) + ";"
    def sng(self, n): return "&" + u36(SING[n])
    def val(self, v): return "!0" if v is None else self.node(v)
    def item(self, x):
        if x is None: return "!0"
        if isinstance(x, ast.AST): return self.node(x)
        if isinstance(x, str): return self.S(x)
        raise TypeError(repr(x))
    def lst(self, xs): return "(" + u36(len(xs)) + "".join(self.item(x) for x in xs)
    def const(self, v):
        if v is None: return "!0"
        if v is True: return "!1"
        if v is False: return "!2"
        if v is Ellipsis: return "!3"
        if isinstance(v, (int, float, complex)): return self.num(v)
        if isinstance(v, str): return self.S(v)
        if isinstance(v, bytes): return '"' + u36(self.D.id(repr(v)))
        return self.S(repr(v))
    def generic(self, n):
        out = "\u00b5" + self.S(type(n).__name__)
        for f in type(n)._fields:
            v = getattr(n, f, None)
            if isinstance(v, list): out += self.lst(v)
            elif v is None: out += "!0"
            elif isinstance(v, str): out += self.S(v)
            elif isinstance(v, (int, float, complex)): out += self.num(v)
            elif isinstance(v, ast.AST): out += self.item(v)
            else: out += self.S(repr(v))
        return out
    def node(self, n):
        t = type(n).__name__; E = self
        if t == "Module": return "M" + E.lst(n.body)
        if t == "FunctionDef": return "F" + u36(E.D.id(n.name)) + E.node(n.args) + E.lst(n.body) + E.lst(n.decorator_list) + E.val(n.returns)
        if t == "ClassDef": return "C" + u36(E.D.id(n.name)) + E.lst(n.bases) + E.lst(n.keywords) + E.lst(n.body) + E.lst(n.decorator_list)
        if t == "Assign": return "a" + E.lst(n.targets) + E.node(n.value)
        if t == "AugAssign": return "u" + E.node(n.target) + E.sng(type(n.op).__name__) + E.node(n.value)
        if t == "AnnAssign": return "v" + E.node(n.target) + E.node(n.annotation) + E.val(n.value) + E.num(n.simple)
        if t == "Return": return "r" + E.val(n.value)
        if t == "Expr": return "e" + E.node(n.value)
        if t == "Call": return "c" + E.node(n.func) + E.lst(n.args) + E.lst(n.keywords)
        if t == "keyword":
            return "k" + (u36(E.D.id(n.arg)) if n.arg else "!0") + E.node(n.value)
        if t == "Name":
            if isinstance(n.ctx, ast.Del): return E.generic(n)  # Del has no 1-char opcode; lossless via µ-fallback
            return ("n" if isinstance(n.ctx, ast.Load) else "m") + u36(E.D.id(n.id))
        if t == "Attribute": return "t" + E.node(n.value) + E.S(n.attr) + E.sng(type(n.ctx).__name__)
        if t == "Subscript": return "x" + E.node(n.value) + E.node(n.slice) + E.sng(type(n.ctx).__name__)
        if t == "Constant": return "o" + E.const(n.value)
        if t == "If": return "i" + E.node(n.test) + E.lst(n.body) + E.lst(n.orelse)
        if t == "IfExp": return "/" + E.node(n.test) + E.node(n.body) + E.node(n.orelse)
        if t == "NamedExpr": return ")" + E.node(n.target) + E.node(n.value)
        if t == "For": return "f" + E.node(n.target) + E.node(n.iter) + E.lst(n.body) + E.lst(n.orelse)
        if t == "While": return "w" + E.node(n.test) + E.lst(n.body) + E.lst(n.orelse)
        if t == "Compare": return "z" + E.node(n.left) + E.lst(n.ops) + E.lst(n.comparators)
        if t == "BinOp": return "q" + E.node(n.left) + E.sng(type(n.op).__name__) + E.node(n.right)
        if t == "BoolOp": return "l" + E.sng(type(n.op).__name__) + E.lst(n.values)
        if t == "UnaryOp": return "y" + E.sng(type(n.op).__name__) + E.node(n.operand)
        if t == "Tuple": return "j" + E.lst(n.elts) + E.sng(type(n.ctx).__name__)
        if t == "List": return "g" + E.lst(n.elts) + E.sng(type(n.ctx).__name__)
        if t == "Set":
            c = getattr(n, "ctx", None)
            return "h" + E.lst(n.elts) + (E.sng(type(c).__name__) if c else "!0")
        if t == "Dict": return "s" + E.lst(n.keys) + E.lst(n.values)
        if t == "JoinedStr": return "p" + E.lst(n.values)
        if t == "FormattedValue": return "b" + E.node(n.value) + E.num(n.conversion) + E.val(n.format_spec)
        if t == "arguments": return "|" + E.lst(n.posonlyargs) + E.lst(n.args) + E.val(n.vararg) + E.lst(n.kwonlyargs) + E.lst(n.kw_defaults) + E.val(n.kwarg) + E.lst(n.defaults)
        if t == "arg": return "%" + u36(E.D.id(n.arg)) + E.val(n.annotation)
        if t == "Import": return "$" + E.lst(n.names)
        if t == "ImportFrom": return "?" + (u36(E.D.id(n.module)) if n.module else "!0") + E.lst(n.names) + E.num(n.level)
        if t == "alias": return "@" + E.S(n.name) + (E.S(n.asname) if n.asname else "!0")
        if t == "Pass": return ":"
        if t == "Break": return ";"
        if t == "Continue": return "^"
        if t == "Global": return "~" + "(" + u36(len(n.names)) + "".join(E.S(x) for x in n.names)
        if t == "Nonlocal": return "\\" + "(" + u36(len(n.names)) + "".join(E.S(x) for x in n.names)
        if t == "Try": return "[" + E.lst(n.body) + E.lst(n.handlers) + E.lst(n.orelse) + E.lst(n.finalbody)
        if t == "ExceptHandler": return "]" + E.val(n.type) + (E.S(n.name) if n.name else "!0") + E.lst(n.body)
        if t == "With": return "{" + E.lst(n.items) + E.lst(n.body)
        if t == "withitem": return "}" + E.node(n.context_expr) + E.val(n.optional_vars)
        if t == "comprehension": return "*" + E.node(n.target) + E.node(n.iter) + E.lst(n.ifs) + E.num(n.is_async)
        if t == "ListComp": return "<" + E.node(n.elt) + E.lst(n.generators)
        if t == "SetComp": return "," + E.node(n.elt) + E.lst(n.generators)
        if t == "DictComp": return ">" + E.node(n.key) + E.node(n.value) + E.lst(n.generators)
        if t == "GeneratorExp": return "=" + E.node(n.elt) + E.lst(n.generators)
        if t == "Starred": return "_" + E.node(n.value) + E.sng(type(n.ctx).__name__)
        if t == "Await": return "'" + E.node(n.value)
        if t == "Slice": return "`" + E.val(n.lower) + E.val(n.upper) + E.val(n.step)
        if t == "Delete": return '"' + E.lst(n.targets)
        if t == "Lambda": return "." + E.node(n.args) + E.node(n.body)
        if t == "Assert": return "-" + E.node(n.test) + E.val(n.msg)
        if t == "Raise": return "+" + E.val(n.exc) + E.val(n.cause)
        return E.generic(n)

def gcl1_encode(src):
    tree = ast.parse(src)
    D = Dict()
    stream = Enc(D).node(tree)
    header = json.dumps({"v": 2, "d": D.r}, separators=(",", ":"))
    return header + "\n" + stream

class Dec:
    def __init__(self, T, s):
        self.T = T; self.s = s; self.p = 0
    def ch(self):
        c = self.s[self.p]; self.p += 1; return c
    def run(self):
        s = self.p
        while self.s[self.p] in IDCH: self.p += 1
        return self.s[s:self.p]
    def S(self):
        assert self.s[self.p] == "d"; self.p += 1
        return self.T[pid(self.run())]
    def num(self):
        if self.s[self.p] == "#": self.p += 1
        s = self.p
        while self.s[self.p] != ";": self.p += 1
        v = ast.literal_eval(self.s[s:self.p]); self.p += 1
        return v
    def sng(self):
        self.p += 1  # &
        return getattr(ast, SINGLETONS[pid(self.run())])()
    def const(self, c):
        if c == "!": self.p += 0; return [None, True, False, Ellipsis][int(self.ch())]
        if c == "#": return self.num()
        if c == "d": return self.T[pid(self.run())]
        if c == '"': return ast.literal_eval(self.T[pid(self.run())])
        raise ValueError(c)
    def val(self):
        if self.s[self.p] == "!": self.p += 2; return None
        return self.node(self.ch())
    def lst(self):
        self.p += 1  # (
        n = pid(self.run())
        return [self.item() for _ in range(n)]
    def item(self):
        c = self.s[self.p]
        if c == "!": self.p += 2; return None
        if c == "d": return self.S()
        return self.node(self.ch())
    def strs(self):
        self.p += 1  # (
        n = pid(self.run())
        return [self.S() for _ in range(n)]
    def generic(self):
        cls = getattr(ast, self.S())
        node = cls()
        for f in cls._fields:
            c = self.s[self.p]
            if c == "(": v = self.lst()
            elif c == "!": self.p += 2; v = None
            elif c == "d": v = self.S()
            elif c == "#": v = self.num()
            elif c == "&": v = self.sng()
            else: v = self.node(self.ch())
            setattr(node, f, v)
        return node
    def node(self, c):
        if c == "M": return ast.Module(body=self.lst(), type_ignores=[])
        if c == "F":
            name = self.T[pid(self.run())]; args = self.node(self.ch()); body = self.lst()
            dec = self.lst(); ret = self.val()
            return ast.FunctionDef(name=name, args=args, body=body,
                                   decorator_list=dec, returns=ret, type_comment=None)
        if c == "C": return ast.ClassDef(self.T[pid(self.run())], self.lst(), self.lst(), self.lst(), self.lst())
        if c == "a": return ast.Assign(self.lst(), self.node(self.ch()))
        if c == "u": return ast.AugAssign(target=self.node(self.ch()), op=self.sng(), value=self.node(self.ch()))
        if c == "v": return ast.AnnAssign(target=self.node(self.ch()), annotation=self.node(self.ch()), value=self.val(), simple=self.num())
        if c == "r": return ast.Return(self.val())
        if c == "e": return ast.Expr(self.node(self.ch()))
        if c == "c": return ast.Call(func=self.node(self.ch()), args=self.lst(), keywords=self.lst())
        if c == "k":
            a = None
            if self.s[self.p] == "!": self.p += 2
            else: a = self.T[pid(self.run())]
            return ast.keyword(arg=a, value=self.node(self.ch()))
        if c == "n": return ast.Name(id=self.T[pid(self.run())], ctx=ast.Load())
        if c == "m": return ast.Name(id=self.T[pid(self.run())], ctx=ast.Store())
        if c == "t": return ast.Attribute(value=self.node(self.ch()), attr=self.S(), ctx=self.sng())
        if c == "x": return ast.Subscript(value=self.node(self.ch()), slice=self.node(self.ch()), ctx=self.sng())
        if c == "o": return ast.Constant(self.const(self.ch()))
        if c == "i": return ast.If(self.node(self.ch()), self.lst(), self.lst())
        if c == "/": return ast.IfExp(test=self.node(self.ch()), body=self.node(self.ch()), orelse=self.node(self.ch()))
        if c == ")": return ast.NamedExpr(target=self.node(self.ch()), value=self.node(self.ch()))
        if c == "f": return ast.For(self.node(self.ch()), self.node(self.ch()), self.lst(), self.lst(), None)
        if c == "w": return ast.While(self.node(self.ch()), self.lst(), self.lst())
        if c == "z": return ast.Compare(left=self.node(self.ch()), ops=self.lst(), comparators=self.lst())
        if c == "q": return ast.BinOp(left=self.node(self.ch()), op=self.sng(), right=self.node(self.ch()))
        if c == "l": return ast.BoolOp(op=self.sng(), values=self.lst())
        if c == "y": return ast.UnaryOp(op=self.sng(), operand=self.node(self.ch()))
        if c == "j": return ast.Tuple(elts=self.lst(), ctx=self.sng())
        if c == "g": return ast.List(elts=self.lst(), ctx=self.sng())
        if c == "h":
            elts = self.lst()
            if self.s[self.p] == "&": ctx = self.sng()
            else: self.p += 2; ctx = None
            return ast.Set(elts=elts, ctx=ctx)
        if c == "s": return ast.Dict(keys=self.lst(), values=self.lst())
        if c == "p": return ast.JoinedStr(self.lst())
        if c == "b": return ast.FormattedValue(value=self.node(self.ch()), conversion=self.num(), format_spec=self.val())
        if c == "|": return ast.arguments(self.lst(), self.lst(), self.val(), self.lst(), self.lst(), self.val(), self.lst())
        if c == "%": return ast.arg(arg=self.T[pid(self.run())], annotation=self.val(), type_comment=None)
        if c == "$": return ast.Import(self.lst())
        if c == "?":
            m = None
            if self.s[self.p] == "!": self.p += 2
            else: m = self.T[pid(self.run())]
            names = self.lst(); lvl = self.num()
            return ast.ImportFrom(module=m, names=names, level=lvl)
        if c == "@":
            nm = self.S()
            an = None
            if self.s[self.p] == "!": self.p += 2
            else: an = self.S()
            return ast.alias(name=nm, asname=an)
        if c == ":": return ast.Pass()
        if c == ";": return ast.Break()
        if c == "^": return ast.Continue()
        if c == "~": return ast.Global(self.strs())
        if c == "\\": return ast.Nonlocal(self.strs())
        if c == "[": return ast.Try(self.lst(), self.lst(), self.lst(), self.lst())
        if c == "]":
            ty = self.val()
            nm = None
            if self.s[self.p] == "!": self.p += 2
            else: nm = self.S()
            return ast.ExceptHandler(type=ty, name=nm, body=self.lst())
        if c == "{": return ast.With(self.lst(), self.lst())
        if c == "}": return ast.withitem(context_expr=self.node(self.ch()), optional_vars=self.val())
        if c == "*": return ast.comprehension(target=self.node(self.ch()), iter=self.node(self.ch()), ifs=self.lst(), is_async=self.num())
        if c == "<": return ast.ListComp(self.node(self.ch()), self.lst())
        if c == ",": return ast.SetComp(self.node(self.ch()), self.lst())
        if c == ">": return ast.DictComp(self.node(self.ch()), self.node(self.ch()), self.lst())
        if c == "=": return ast.GeneratorExp(self.node(self.ch()), self.lst())
        if c == "_": return ast.Starred(value=self.node(self.ch()), ctx=self.sng())
        if c == "'": return ast.Await(self.node(self.ch()))
        if c == "`": return ast.Slice(lower=self.val(), upper=self.val(), step=self.val())
        if c == '"': return ast.Delete(self.lst())
        if c == ".": return ast.Lambda(self.node(self.ch()), self.node(self.ch()))
        if c == "-": return ast.Assert(self.node(self.ch()), self.val())
        if c == "+": return ast.Raise(self.val(), self.val())
        if c == "\u00b5": return self.generic()
        raise ValueError("unknown op: " + c)

def gcl1_decode(data):
    header, stream = data.split("\n", 1)
    d = Dec(json.loads(header)["d"], stream + "\x00")
    return d.node(d.ch())


NODE_TABLE = set(SINGLETONS) | set("Module FunctionDef ClassDef Assign AugAssign AnnAssign Return Expr Call keyword Name Attribute Subscript Constant If IfExp NamedExpr For While Compare BinOp BoolOp UnaryOp Tuple List Set Dict JoinedStr FormattedValue arguments arg Import ImportFrom alias Pass Break Continue Global Nonlocal Try ExceptHandler With withitem comprehension ListComp SetComp DictComp GeneratorExp Starred Await Slice Delete Lambda Assert Raise".split())

if __name__ == "__main__":
    root = "/app/.agents/skills"
    files = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in {"__pycache__", ".git", "data", "vault", "evals", "node_modules", "references", "assets"}]
        for f in fn:
            if f.endswith(".py"): files.append(os.path.join(dp, f))
    raw = enc = ok = 0
    t_enc = t_dec = t_parse = 0.0
    fails, fallbacks = [], set()
    for p in files:
        src = open(p, encoding="utf-8", errors="replace").read()
        if not src.strip(): continue
        tree = ast.parse(src)
        t0 = time.perf_counter(); data = gcl1_encode(src); t1 = time.perf_counter()
        rebuilt = gcl1_decode(data); t2 = time.perf_counter()
        same = ast.dump(rebuilt) == ast.dump(tree); t3 = time.perf_counter()
        ok += same; t_enc += t1 - t0; t_dec += t2 - t1; t_parse += t3 - t2
        if not same: fails.append(os.path.basename(p))
        raw += len(src.encode()); enc += len(data.encode())
        for n in ast.walk(tree):
            if type(n).__name__ not in NODE_TABLE: fallbacks.add(type(n).__name__)
    print(f"round-trip AST-equal: {ok}/{len(files)} .py files verified")
    if fails: print("FAILS:", fails)
    print(f"raw:   {raw:>9,} B")
    print(f"GCL-1: {enc:>9,} B  = {100*enc/raw:.1f}% of raw")
    print(f"generic-fallback node types used: {sorted(fallbacks) or 'none'}")
    print(f"timing: encode {t_enc:.2f}s | decode {t_dec:.2f}s | ast.parse {t_parse:.2f}s")
    data = gcl1_encode("issues = find_issues(staging, files)")
    print("\nexample python: issues = find_issues(staging, files)")
    print("example GCL-1: ", data)
