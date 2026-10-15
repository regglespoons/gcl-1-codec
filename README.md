# GCL-1: A Single-Character Opcode Codec for Python ASTs

Phase 1 prototype of the **GCL project** — research toward a universal,
character-minimal code representation: one single-character opcode per
dominant operation, minimum bytes on disk and wire, decodable to a
fully-formed AST without a parser.

## What it does

`gcl1.py` losslessly converts Python source into a character-dense stream:

- **45 single-character ASCII opcodes** over the ~45 dominant AST node types
  (`a` assign, `c` call, `n` name-load, `i` if, `f` for, `t` attribute, ...)
- **Base-33 id alphabet** — dictionary-encoded identifiers/strings with a
  self-describing JSON header per file (no shared registry needed)
- **`&` singleton table** for all operators/contexts (Add, In, Store, ...)
- **Count-coded lists**, no delimiters for single elements
- **Self-delimiting stream — no separators at all** (a space-per-token scheme
  would add ~38% more bytes; the opcode grammar subsumes separators)
- **µ-prefixed generic fallback** for rare node types (Match, async, ...),
  so the codec covers 100% of Python syntax

```python
from gcl1 import gcl1_encode, gcl1_decode
data = gcl1_encode("issues = find_issues(staging, files)")
#  {"v":2,"d":["issues","find_issues","staging","files"]}
#  M(1a(1m0cn1(2n2n3(0
tree = gcl1_decode(data)   # AST-equal to ast.parse(source)
```

Run the self-test over a whole codebase: `python3 gcl1.py`

## Measured results (55-file corpus, 401,229 bytes, already minified)

| metric | result |
|---|---|
| Round-trip fidelity | 55/55 files `ast.dump`-equal (100% lossless) |
| Size vs minified source | 87.3% (350,154 B) |
| Size vs minified source + self | 88.2% over 59-file library incl. this codec |
| Decode vs parse time | 0.13 s vs 0.30 s (2.3x faster load) |

## Honest findings (the interesting part)

1. **Naive structural tokenization made code BIGGER** (122.5% of source):
   per-field type tags cost more than they save. Implied arity — the opcode
   determines what follows — is what makes single-character encoding compress.
2. **New characters are unnecessary at the byte level**: a new Unicode
   codepoint costs 3 bytes in UTF-8 vs 1 for an ASCII opcode. We removed
   three letters from the id alphabet instead of adding characters.
   (Unicode PUA, ~137k codepoints, remains available for display/extension.)
3. **Semantic text encoding loses to generic compression when stacked**:
   GCL-1+gzip = 143.8 KB vs source+gzip = 124.0 KB. The stream destroys the
   textual redundancy gzip feeds on. The honest next 2x requires pairing the
   opcode stream with a dedicated entropy coder — the same reason production
   systems ship wasm/brotli rather than "compressed source".

## Roadmap

- **Phase 2**: frequency-ordered opcode packing (Huffman over measured op
  histograms) targeting < 60% of source before entropy coding
- **Phase 3**: frontends beyond Python (TypeScript, Rust) onto the same
  opcode discipline; round-trip fuzzing
- Related venues we are engaging: W3C WebAssembly CG (character-dense wasm
  serialization), LLVM community, ISO/IEC JTC1/SC22

## Seeking

Suggestions, prior art, corrections, and recommendations — please open an
issue or discussion. Particularly interested in: prior work on
character-minimal IR serializations we should build on.

*No license attached yet; all rights reserved pending review. — Raynewal Christos Soulclaw*
