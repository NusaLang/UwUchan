#!/usr/bin/env python3
# Generate _pb_skema() (proto/pb.ns) dari source .proto whatsmeow.
#
# Pakai:
#   python3 gen_pb_schema.py <path/ke/whatsmeow/proto> [output_dir]
#
# <path/ke/whatsmeow/proto> itu folder "proto" di dalam checkout/module
# whatsmeow (go.mau.fi/whatsmeow), isinya waE2E/, waCommon/, dan 53 folder
# proto lain. Kalau pake Go module cache: cari lewat
#   go list -m -f '{{.Dir}}' go.mau.fi/whatsmeow
# lalu tambahin "/proto" di belakangnya.
#
# output_dir (default: cwd) bakal diisi skema.ns.txt (skema pb, tempel ke
# _pb_skema() di pb.ns) dan enums.ns.txt (tabel enum, tempel di atasnya).

import re, sys, glob, os

if len(sys.argv) < 2:
    print(__doc__, file=sys.stderr)
    sys.exit(1)

PROTO_ROOT = sys.argv[1]
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else "."
E2E = f"{PROTO_ROOT}/waE2E/WAWebProtobufsE2E.proto"
COMMON = f"{PROTO_ROOT}/waCommon/WACommon.proto"

if not os.path.isfile(E2E) or not os.path.isfile(COMMON):
    print(f"gak nemu {E2E} / {COMMON} -- cek path proto_root", file=sys.stderr)
    sys.exit(1)

# semua .proto lain di tree whatsmeow. Nama dir jadi prefix chain biar gak
# tabrakan flatkey sama E2E/COMMON (yang sengaja TANPA prefix demi
# backward-compat -- banyak kode .ns manggil pb_enkode_bernama(x, "Message")
# polos tanpa prefix) dan gak tabrakan sesama file lain juga.
OTHER_PROTOS = sorted(
    p for p in glob.glob(f"{PROTO_ROOT}/*/*.proto")
    if os.path.abspath(p) not in (os.path.abspath(E2E), os.path.abspath(COMMON))
)

SCALAR_TYPES = {
    "int32","int64","uint32","uint64","sint32","sint64",
    "fixed32","fixed64","sfixed32","sfixed64","float","double",
}

def strip_comments(text):
    return re.sub(r'//[^\n]*', '', text)

def tokenize_body(text):
    tokens = []
    i = 0
    n = len(text)
    while i < n:
        m = re.match(r'\s*', text[i:])
        i += m.end()
        if i >= n:
            break
        rest = text[i:]
        mm = re.match(r'(message|enum|oneof)\s+([A-Za-z0-9_]+)\s*\{', rest)
        if mm:
            kind, name = mm.group(1), mm.group(2)
            start = i + mm.end()
            depth = 1
            j = start
            while depth > 0 and j < n:
                if text[j] == '{': depth += 1
                elif text[j] == '}': depth -= 1
                j += 1
            body = text[start:j-1]
            tokens.append((kind, name, body))
            i = j
            continue
        semi = rest.find(';')
        brace = rest.find('{')
        if semi == -1 and brace == -1:
            break
        if brace != -1 and (semi == -1 or brace < semi):
            depth = 1
            j = i + brace + 1
            while depth > 0 and j < n:
                if text[j] == '{': depth += 1
                elif text[j] == '}': depth -= 1
                j += 1
            i = j
            continue
        line = rest[:semi].strip()
        tokens.append(('line', line, None))
        i += semi + 1
    return tokens

FIELD_RE = re.compile(
    r'^(?:optional|repeated|required)\s+([A-Za-z0-9_.]+)\s+([A-Za-z0-9_]+)\s*=\s*(\d+)'
)
ONEOF_FIELD_RE = re.compile(
    r'^([A-Za-z0-9_.]+)\s+([A-Za-z0-9_]+)\s*=\s*(\d+)'
)
ENUM_VALUE_RE = re.compile(r'^([A-Za-z0-9_]+)\s*=\s*(-?\d+)')

class Msg:
    __slots__ = ("qualname", "flatkey", "fields", "nested_names")
    def __init__(self, qualname, flatkey):
        self.qualname = qualname
        self.flatkey = flatkey
        self.fields = []
        self.nested_names = set()

all_msgs = {}
by_qualname = {}
enum_defs = {}          # qualname tuple -> {num:int -> name:str}
enum_local_names = set()

def flatten(name_chain):
    return "_".join(name_chain)

def parse_enum_body(tokens):
    values = {}
    for kind, a, b in tokens:
        if kind != 'line':
            continue
        mm = ENUM_VALUE_RE.match(a)
        if mm:
            vname, vnum = mm.groups()
            values[int(vnum)] = vname
    return values

def walk(tokens, name_chain):
    msg = by_qualname.get(name_chain)
    for kind, a, b in tokens:
        if kind == 'message':
            child_chain = name_chain + (a,)
            child = Msg(child_chain, flatten(child_chain))
            by_qualname[child_chain] = child
            all_msgs[child.flatkey] = child
            if msg is not None:
                msg.nested_names.add(a)
            walk(tokenize_body(b), child_chain)
        elif kind == 'enum':
            enum_local_names.add(a)
            enum_defs[name_chain + (a,)] = parse_enum_body(tokenize_body(b))
            if msg is not None:
                msg.nested_names.add(a)
        elif kind == 'oneof':
            walk_lines_into(tokenize_body(b), msg, oneof=True)
        elif kind == 'line':
            walk_lines_into([(kind, a, b)], msg)

def walk_lines_into(tokens, msg, oneof=False):
    if msg is None:
        return
    for kind, a, b in tokens:
        if kind != 'line':
            continue
        mm = (ONEOF_FIELD_RE if oneof else FIELD_RE).match(a)
        if mm:
            typename, fname, tag = mm.groups()
            msg.fields.append((int(tag), fname, typename))

package_to_prefix = {}

def parse_file(path, top_chain_prefix=()):
    raw = open(path).read()
    pkg_m = re.search(r'^\s*package\s+([A-Za-z0-9_.]+)\s*;', raw, re.MULTILINE)
    if pkg_m:
        package_to_prefix[pkg_m.group(1)] = top_chain_prefix
    text = strip_comments(raw)
    tokens = tokenize_body(text)
    for kind, a, b in tokens:
        if kind == 'message':
            chain = top_chain_prefix + (a,)
            m = Msg(chain, flatten(chain))
            by_qualname[chain] = m
            all_msgs[m.flatkey] = m
            walk(tokenize_body(b), chain)
        elif kind == 'enum':
            enum_local_names.add(a)
            enum_defs[top_chain_prefix + (a,)] = parse_enum_body(tokenize_body(b))

parse_file(E2E)
parse_file(COMMON)

parse_errors = []
for p in OTHER_PROTOS:
    prefix = os.path.basename(os.path.dirname(p))
    try:
        parse_file(p, top_chain_prefix=(prefix,))
    except Exception as e:
        parse_errors.append((p, str(e)))
for p, e in parse_errors:
    print(f"[SKIP] gagal parse {p}: {e}", file=sys.stderr)

def resolve_in_registry(registry, typename, from_chain):
    # qualified cross-package ref (mis. "WACommonParameterised.SubProtocol"
    # atau "WACert.NoiseCertificate.Details") -- resolve package-nya ke
    # prefix direktori file itu (dari package_to_prefix, hasil parse
    # "package X;" tiap .proto), baru cari sisa chain-nya di situ. Ini
    # yang bikin referensi antar file non-E2E/COMMON ikut ke-resolve.
    parts = typename.split('.')
    if len(parts) > 1 and parts[0] in package_to_prefix:
        cand = package_to_prefix[parts[0]] + tuple(parts[1:])
        if cand in registry:
            return cand

    local = parts[-1]
    chain = from_chain
    while True:
        cand = chain + (local,)
        if cand in registry:
            return cand
        if not chain:
            break
        chain = chain[:-1]
    if (local,) in registry:
        return (local,)
    return None

def resolve_type(typename, from_chain):
    if typename in SCALAR_TYPES or typename in ("string", "bytes", "bool"):
        return None
    return resolve_in_registry(by_qualname, typename, from_chain)

def resolve_enum(typename, from_chain):
    return resolve_in_registry(enum_defs, typename, from_chain)

def field_kind(typename, from_chain):
    if typename == "bool":
        return "bool"
    if typename == "bytes":
        return "bin"
    if typename == "string" or typename in SCALAR_TYPES:
        return "scalar"
    sub = resolve_type(typename, from_chain)
    if sub:
        return ("sub", by_qualname[sub].flatkey)
    enum_chain = resolve_enum(typename, from_chain)
    if enum_chain:
        return ("enum", flatten(enum_chain))
    return "scalar"  # unresolved cross-package type -> opaque fallback

# ---- emit Nusantara code ----
lines = []
seen_flatkeys = set()
for flatkey, m in all_msgs.items():
    if not m.fields:
        continue
    if flatkey in seen_flatkeys:
        continue
    seen_flatkeys.add(flatkey)
    varname = "g_" + flatkey
    lines.append(f"    buat {varname} = peta_baru();")
    for tag, fname, typename in sorted(m.fields, key=lambda t: t[0]):
        kind = field_kind(typename, m.qualname)
        if kind == "bool":
            lines.append(f'    {varname}["{tag}"] = _fldb("{fname}");')
        elif kind == "bin":
            lines.append(f'    {varname}["{tag}"] = _fldbin("{fname}");')
        elif isinstance(kind, tuple) and kind[0] == "sub":
            lines.append(f'    {varname}["{tag}"] = _flds("{fname}", "{kind[1]}");')
        elif isinstance(kind, tuple) and kind[0] == "enum":
            lines.append(f'    {varname}["{tag}"] = _flde("{fname}", _enum_{kind[1]}());')
        else:
            lines.append(f'    {varname}["{tag}"] = _fld("{fname}");')
    lines.append(f's["{flatkey}"] = {varname};')
    lines.append("")

enum_lines = []
for chain, values in enum_defs.items():
    flatkey = flatten(chain)
    enum_lines.append(f"fungsi _enum_{flatkey}() {{")
    enum_lines.append("    buat e = peta_baru();")
    for num, name in sorted(values.items()):
        enum_lines.append(f'    e["{num}"] = "{name}";')
    enum_lines.append("    hasil e;")
    enum_lines.append("}")
    enum_lines.append("")

print(f"total message types dgn field: {len(seen_flatkeys)}", file=sys.stderr)
print(f"total enum types: {len(enum_defs)}", file=sys.stderr)

os.makedirs(OUT_DIR, exist_ok=True)
with open(os.path.join(OUT_DIR, "enums.ns.txt"), "w") as f:
    f.write("\n".join(enum_lines))
with open(os.path.join(OUT_DIR, "skema.ns.txt"), "w") as f:
    f.write("\n".join(lines))

print(f"tulis {OUT_DIR}/enums.ns.txt dan {OUT_DIR}/skema.ns.txt", file=sys.stderr)
