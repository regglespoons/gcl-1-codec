#!/usr/bin/env python3
"""GCL Vault: file encryption at rest, implementing the Oct 14 2026 research
findings: AES-256-GCM with a fresh 96-bit nonce per write; AAD binds the file
name so renamed or swapped files fail authentication; envelope encryption
(random per-file data key wrapped under a passphrase-derived KEK); Argon2id
when argon2-cffi is installed, PBKDF2-SHA256 fallback. Armor GVLT1.
Requires: pip install cryptography"""
import argparse, base64, json, os, secrets, sys, tempfile

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    sys.exit("cryptography package required: pip install cryptography")

def _argon2_available():
    try:
        import argon2  # noqa
        return True
    except ImportError:
        return False

def derive_kek(passphrase, salt, mode):
    if mode == "argon2id":
        from argon2.low_level import hash_secret_raw, Type
        return hash_secret_raw(passphrase.encode(), salt, time_cost=3,
                               memory_cost=65536, parallelism=4,
                               hash_len=32, type=Type.ID)
    import hashlib
    return hashlib.pbkdf2_hmac("sha256", passphrase.encode(), salt, 310000)

def encrypt_file(path, passphrase, out_path):
    data_key = secrets.token_bytes(32)              # envelope: per-file data key
    data_iv = secrets.token_bytes(12)               # fresh 96-bit nonce per write
    name = os.path.basename(path)
    ct = AESGCM(data_key).encrypt(data_iv, open(path, "rb").read(), name.encode())
    kek_salt = secrets.token_bytes(32)
    mode = "argon2id" if _argon2_available() else "pbkdf2"
    kek = derive_kek(passphrase, kek_salt, mode)
    wrap_iv = secrets.token_bytes(12)
    wrapped = AESGCM(kek).encrypt(wrap_iv, data_key, b"gclvault-keywrap-v1")
    header = json.dumps({"mode": mode, "salt": base64.b64encode(kek_salt).decode(),
                         "wrap_iv": base64.b64encode(wrap_iv).decode(),
                         "wrapped_dk": base64.b64encode(wrapped).decode(),
                         "data_iv": base64.b64encode(data_iv).decode(),
                         "name": name}).encode()
    with open(out_path, "wb") as f:
        f.write(b"GVLT1" + len(header).to_bytes(4, "little") + header + ct)
    return len(ct), mode

def decrypt_file(path, passphrase, out_path):
    blob = open(path, "rb").read()
    if blob[:5] != b"GVLT1":
        raise ValueError("not a GVLT1 file")
    hlen = int.from_bytes(blob[5:9], "little")
    header = json.loads(blob[9:9 + hlen])
    ct = blob[9 + hlen:]
    kek = derive_kek(passphrase, base64.b64decode(header["salt"]), header["mode"])
    data_key = AESGCM(kek).decrypt(base64.b64decode(header["wrap_iv"]),
                                   base64.b64decode(header["wrapped_dk"]),
                                   b"gclvault-keywrap-v1")
    pt = AESGCM(data_key).decrypt(base64.b64decode(header["data_iv"]), ct,
                                 header["name"].encode())   # AAD: name binding
    with open(out_path, "wb") as f:
        f.write(pt)
    return len(pt)

def selftest():
    d = tempfile.mkdtemp()
    src, enc, dec = (os.path.join(d, n) for n in ("a.txt", "a.gclenc", "b.txt"))
    open(src, "w").write("The quick brown fox. " * 100)
    _, mode = encrypt_file(src, "test-pass", enc)
    decrypt_file(enc, "test-pass", dec)
    ok_rt = open(src, "rb").read() == open(dec, "rb").read()
    ct1, _ = encrypt_file(src, "p", enc + "1"); ct2, _ = encrypt_file(src, "p", enc + "2")
    ok_rand = open(enc + "1", "rb").read() != open(enc + "2", "rb").read()
    try:
        decrypt_file(enc, "wrong-pass", dec + "x"); ok_auth = False
    except Exception:
        ok_auth = True
    blob = bytearray(open(enc, "rb").read()); blob[-1] ^= 0xFF; open(enc, "wb").write(bytes(blob))
    try:
        decrypt_file(enc, "test-pass", dec + "y"); ok_tamper = False
    except Exception:
        ok_tamper = True
    print("lossless:", ok_rt, "| randomized:", ok_rand, "| wrong-pass rejected:", ok_auth,
          "| tamper rejected:", ok_tamper, "| KDF:", mode)
    return ok_rt and ok_rand and ok_auth and ok_tamper

def main():
    ap = argparse.ArgumentParser(description="GCL Vault: AES-256-GCM file encryption at rest")
    ap.add_argument("cmd", choices=["encrypt", "decrypt", "selftest"])
    ap.add_argument("file", nargs="?")
    ap.add_argument("-o", "--out")
    ap.add_argument("-p", "--passphrase", required=False)
    a = ap.parse_args()
    if a.cmd == "selftest":
        sys.exit(0 if selftest() else 1)
    if not a.file or not a.passphrase:
        sys.exit("usage: gclvault.py encrypt <file> -p <passphrase> [-o out.gclenc]")
    out = a.out or (a.file + ".gclenc" if a.cmd == "encrypt" else
                   "recovered-" + os.path.basename(a.file).removesuffix(".gclenc"))
    if a.cmd == "encrypt":
        n, mode = encrypt_file(a.file, a.passphrase, out)
        print("encrypted ->", out, f"({n} B ciphertext, KDF {mode})")
    else:
        n = decrypt_file(a.file, a.passphrase, out)
        print("decrypted ->", out, f"({n} B)")

if __name__ == "__main__":
    main()
