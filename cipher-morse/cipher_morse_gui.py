"""
CipherMorse - Secure Message Converter
========================================

Chains strong, password-based authenticated encryption with Morse code.

ENCRYPT direction:
    Plaintext
      -> PBKDF2-HMAC-SHA256 key derivation (random 16-byte salt, 600,000 rounds)
      -> Fernet (AES-128-CBC + HMAC-SHA256) authenticated encryption
      -> hex encoding
      -> Morse code

DECRYPT direction (exact reverse):
    Morse code -> hex -> ciphertext bytes -> Fernet decryption -> Plaintext

Dependency:
    pip install cryptography

Run:
    python cipher_morse_gui.py
"""

import base64
import binascii
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError:
    print("Missing dependency. Install it with:\n\n    pip install cryptography\n")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Crypto + Morse core (pure functions, no GUI dependency -- unit-testable)
# ---------------------------------------------------------------------------

SALT_SIZE = 16
KDF_ITERATIONS = 600_000  # meets current OWASP guidance for PBKDF2-HMAC-SHA256

MORSE_TABLE = {
    '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
    'A': '.-',    'B': '-...',  'C': '-.-.',  'D': '-..',   'E': '.',
    'F': '..-.',
}
MORSE_TABLE_REV = {code: hexchar for hexchar, code in MORSE_TABLE.items()}


def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 32-byte Fernet key from a password + salt via PBKDF2-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))


def encrypt_to_morse(plaintext: str, password: str) -> str:
    """Encrypt plaintext with a password, return the ciphertext as Morse code."""
    if not plaintext:
        raise ValueError("Enter a message to encrypt.")
    if not password:
        raise ValueError("Enter a password.")

    salt = os.urandom(SALT_SIZE)
    key = _derive_key(password, salt)
    token = Fernet(key).encrypt(plaintext.encode('utf-8'))

    payload = salt + token
    hex_str = binascii.hexlify(payload).decode('ascii').upper()
    return ' '.join(MORSE_TABLE[ch] for ch in hex_str)


def decrypt_from_morse(morse: str, password: str) -> str:
    """Reverse of encrypt_to_morse: Morse code + password -> plaintext."""
    if not morse.strip():
        raise ValueError("Enter a Morse code message to decrypt.")
    if not password:
        raise ValueError("Enter a password.")

    tokens = morse.split()
    try:
        hex_str = ''.join(MORSE_TABLE_REV[t] for t in tokens)
    except KeyError as bad:
        raise ValueError(f"'{bad.args[0]}' is not a recognized Morse symbol.")

    try:
        payload = binascii.unhexlify(hex_str)
    except (binascii.Error, ValueError):
        raise ValueError("Morse code is incomplete or corrupted.")

    if len(payload) <= SALT_SIZE:
        raise ValueError("Morse code is incomplete or corrupted.")

    salt, token = payload[:SALT_SIZE], payload[SALT_SIZE:]
    key = _derive_key(password, salt)

    try:
        plaintext = Fernet(key).decrypt(token)
    except InvalidToken:
        raise ValueError("Wrong password, or the message was corrupted.")
    except Exception:
        raise ValueError("Could not decrypt this message.")

    return plaintext.decode('utf-8')


# ---------------------------------------------------------------------------
# A little easter egg, hidden using the exact same pipeline as every message
# in this app. Press Ctrl+Shift+I while the app is running to reveal it, or
# decrypt it by hand:  decrypt_from_morse(SIGNATURE, SIGNATURE_KEY)
# ---------------------------------------------------------------------------
SIGNATURE_KEY = "cipher-morse"
SIGNATURE = (
    "....- .- ----- ...-- ...-- ---.. -... ---.. -.. --... ..--- ..... .---- "
    "--... ..... -.... ....- ..... ---.. .- -.-. -.... ..-. . -.... .- -.-. "
    "----- -.... .---- ---.. ..... -.... --... ....- .---- ....- .---- ....- "
    ".---- ....- .---- ....- .---- ....- ..--- --... .---- ..... ---.. ...-- "
    "----- -.... ---.. --... --... ..... ---.. ....- -.-. ....- -... ....- "
    "....- ...-- ....- ..... ....- ...-- ---.. -.... . ...-- ...-- ..... "
    "----. ....- ..... ....- ...-- ....- ..... ....- . ...-- .---- -.... "
    "..-. --... .- --... ---.. ....- .---- ....- ----. ...-- ---.. ...-- "
    "----- ..... --... ...-- ...-- ....- .---- ....- ....- -.... --... ...-- "
    ".---- ....- --... ....- . ....- ..... -.... ...-- ..... ..--- -.... "
    "...-- -.... -.... ....- ..--- ....- ---.. ....- -... --... .---- ....- "
    "-.-. ..... .- --... ----- ....- ..--- ..... ---.. --... ...-- ...-- "
    "----- ..... ---.. ....- .- -.... . ....- -.-. ...-- ....- ....- .- --... "
    "....- -.... ..-. ....- ..... ...-- ..... ..... ---.. ..... ---.. ...-- "
    "----- ..... ..... -.... ----. -.... ----. ....- ..--- ...-- --... -.... "
    ".- -.... ---.. --... -.... --... ..... ...-- --... ..... ----. ....- "
    "-.... --... .- ....- ---.. ..... ----. ....- -.. ....- ----. -.... ...-- "
    "--... ----. --... ----. -.... -.... --... --... ..... .- --... ....- "
    "-.... ..--- ...-- ----- ....- .---- ...-- -.. ...-- -.."
)
# ^ currently decodes to a placeholder name -- see the chat for how to swap in your own.


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

MONO_FONT = ("Courier New", 11)


class CipherMorseApp:
    def __init__(self, root):
        self.root = root
        root.title("CipherMorse — Secure Message Converter")
        root.geometry("620x640")
        root.minsize(520, 560)

        style = ttk.Style()
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass
        style.configure('TNotebook.Tab', padding=(16, 8))
        style.configure('TButton', padding=8)
        style.configure('Header.TLabel', font=('Segoe UI', 15, 'bold'))

        ttk.Label(root, text="CipherMorse", style='Header.TLabel').pack(pady=(14, 4))
        ttk.Label(root, text="Password-based encryption, sent as Morse code").pack(pady=(0, 8))

        notebook = ttk.Notebook(root)
        notebook.pack(fill='both', expand=True, padx=12, pady=8)

        self.encrypt_tab = ttk.Frame(notebook)
        self.decrypt_tab = ttk.Frame(notebook)
        notebook.add(self.encrypt_tab, text="Encrypt")
        notebook.add(self.decrypt_tab, text="Decrypt")

        self._build_encrypt_tab()
        self._build_decrypt_tab()

        root.bind('<Control-Shift-I>', self._reveal_signature)
        root.bind('<Control-Shift-i>', self._reveal_signature)

    def _reveal_signature(self, event=None):
        try:
            name = decrypt_from_morse(SIGNATURE, SIGNATURE_KEY)
            messagebox.showinfo("You found it 🔍", f"Made with care by {name}")
        except Exception:
            pass

    def _build_encrypt_tab(self):
        f = self.encrypt_tab

        ttk.Label(f, text="Plaintext message").pack(anchor='w', padx=12, pady=(12, 2))
        self.enc_input = tk.Text(f, height=5, wrap='word')
        self.enc_input.pack(fill='x', padx=12)

        ttk.Label(f, text="Password").pack(anchor='w', padx=12, pady=(10, 2))
        pw_row = ttk.Frame(f)
        pw_row.pack(fill='x', padx=12)
        self.enc_password = ttk.Entry(pw_row, show='*')
        self.enc_password.pack(side='left', fill='x', expand=True)
        self.enc_show = tk.BooleanVar()
        ttk.Checkbutton(
            pw_row, text="Show", variable=self.enc_show,
            command=lambda: self.enc_password.config(show='' if self.enc_show.get() else '*')
        ).pack(side='left', padx=(8, 0))

        ttk.Button(f, text="Encrypt  →  Morse", command=self.do_encrypt).pack(pady=12)

        ttk.Label(f, text="Morse code output").pack(anchor='w', padx=12)
        self.enc_output = tk.Text(f, height=9, wrap='word', font=MONO_FONT, state='disabled')
        self.enc_output.pack(fill='both', expand=True, padx=12, pady=(2, 8))

        ttk.Button(f, text="Copy Output", command=lambda: self._copy(self.enc_output)).pack(pady=(0, 12))

    def _build_decrypt_tab(self):
        f = self.decrypt_tab

        ttk.Label(f, text="Morse code message").pack(anchor='w', padx=12, pady=(12, 2))
        self.dec_input = tk.Text(f, height=5, wrap='word', font=MONO_FONT)
        self.dec_input.pack(fill='x', padx=12)

        ttk.Label(f, text="Password").pack(anchor='w', padx=12, pady=(10, 2))
        pw_row = ttk.Frame(f)
        pw_row.pack(fill='x', padx=12)
        self.dec_password = ttk.Entry(pw_row, show='*')
        self.dec_password.pack(side='left', fill='x', expand=True)
        self.dec_show = tk.BooleanVar()
        ttk.Checkbutton(
            pw_row, text="Show", variable=self.dec_show,
            command=lambda: self.dec_password.config(show='' if self.dec_show.get() else '*')
        ).pack(side='left', padx=(8, 0))

        ttk.Button(f, text="Decrypt  →  Plaintext", command=self.do_decrypt).pack(pady=12)

        ttk.Label(f, text="Plaintext output").pack(anchor='w', padx=12)
        self.dec_output = tk.Text(f, height=9, wrap='word', state='disabled')
        self.dec_output.pack(fill='both', expand=True, padx=12, pady=(2, 8))

        ttk.Button(f, text="Copy Output", command=lambda: self._copy(self.dec_output)).pack(pady=(0, 12))

    def do_encrypt(self):
        plaintext = self.enc_input.get('1.0', 'end').strip()
        password = self.enc_password.get()
        try:
            morse = encrypt_to_morse(plaintext, password)
            self._fill(self.enc_output, morse)
        except Exception as e:
            messagebox.showerror("Encryption error", str(e))

    def do_decrypt(self):
        morse = self.dec_input.get('1.0', 'end').strip()
        password = self.dec_password.get()
        try:
            plaintext = decrypt_from_morse(morse, password)
            self._fill(self.dec_output, plaintext)
        except Exception as e:
            messagebox.showerror("Decryption error", str(e))

    @staticmethod
    def _fill(widget, text):
        widget.config(state='normal')
        widget.delete('1.0', 'end')
        widget.insert('1.0', text)
        widget.config(state='disabled')

    def _copy(self, widget):
        text = widget.get('1.0', 'end').strip()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)


def main():
    root = tk.Tk()
    CipherMorseApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
