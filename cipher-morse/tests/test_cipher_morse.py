"""Automated checks for cipher_morse_gui.py (crypto logic + GUI construction)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from cipher_morse_gui import encrypt_to_morse, decrypt_from_morse, SIGNATURE, SIGNATURE_KEY


def test_signature_decodes():
    name = decrypt_from_morse(SIGNATURE, SIGNATURE_KEY)
    assert name and isinstance(name, str)
    print(f"[OK] hidden signature decodes to: {name!r}")


def test_round_trip():
    msg = "Attack at dawn! Meet at 0600. Special chars: éü 🚀"
    pw = "correct horse battery staple"
    morse = encrypt_to_morse(msg, pw)
    assert all(c in '.- ' for c in morse), "Morse output has unexpected characters"
    plain = decrypt_from_morse(morse, pw)
    assert plain == msg, f"Round trip mismatch: {plain!r} != {msg!r}"
    print("[OK] round-trip encrypt/decrypt (incl. unicode)")


def test_different_each_time():
    # Random salt means the same message encrypts differently every time
    m1 = encrypt_to_morse("same message", "pw")
    m2 = encrypt_to_morse("same message", "pw")
    assert m1 != m2, "Ciphertext should differ each run due to random salt/IV"
    print("[OK] output is non-deterministic (random salt in use)")


def test_wrong_password():
    morse = encrypt_to_morse("secret battle plans", "rightpw")
    try:
        decrypt_from_morse(morse, "wrongpw")
        raise AssertionError("Expected ValueError for wrong password")
    except ValueError:
        print("[OK] wrong password correctly rejected")


def test_invalid_symbol():
    try:
        decrypt_from_morse("... --- ...", "any")  # SOS -- not in our hex alphabet
        raise AssertionError("Expected ValueError for invalid morse symbol")
    except ValueError:
        print("[OK] invalid morse symbol correctly rejected")


def test_empty_inputs():
    cases = [
        (encrypt_to_morse, ("", "pw")),
        (encrypt_to_morse, ("msg", "")),
        (decrypt_from_morse, ("", "pw")),
        (decrypt_from_morse, ("....", "")),
    ]
    for fn, args in cases:
        try:
            fn(*args)
            raise AssertionError(f"Expected ValueError for {args}")
        except ValueError:
            pass
    print("[OK] empty-input validation")


test_round_trip()
test_signature_decodes()
test_different_each_time()
test_wrong_password()
test_invalid_symbol()
test_empty_inputs()

# --- GUI construction + wiring smoke test (needs a display, e.g. xvfb-run) ---
import tkinter as tk
from cipher_morse_gui import CipherMorseApp

root = tk.Tk()
app = CipherMorseApp(root)
root.update()

app.enc_input.insert('1.0', "Meet me at midnight")
app.enc_password.insert(0, "hunter2-supreme")
app.do_encrypt()
root.update()
morse_out = app.enc_output.get('1.0', 'end').strip()
assert morse_out, "Encrypt tab produced no output"

app.dec_input.insert('1.0', morse_out)
app.dec_password.insert(0, "hunter2-supreme")
app.do_decrypt()
root.update()
plain_out = app.dec_output.get('1.0', 'end').strip()
assert plain_out == "Meet me at midnight", f"GUI round trip mismatch: {plain_out!r}"

root.destroy()
print("[OK] GUI build + encrypt/decrypt tabs wired correctly")
print("ALL TESTS PASSED")
