"""Print a PBKDF2 hash suitable for DOCASSIST_ADMIN_PASSWORD_HASH."""
import getpass
import hashlib
import secrets

password = getpass.getpass("Admin password: ")
salt = secrets.token_bytes(16)
print(salt.hex() + ":" + hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 250_000).hex())
