import nacl.public
import os
import pyonionreq.junk
from const import *



if os.path.exists(Environment.PRIVKEY_FILE):
    with open(Environment.PRIVKEY_FILE, "r") as f:
        key = f.read()
        if key[-1] == '\n':
            key = key[:-1]
        if len(key) != 64:
            raise RuntimeError(
                "Invalid key_x25519: expected 64 bytes, not {} bytes".format(len(key))
            )
    server_privkey_bytes = bytes.fromhex(key)
    privkey = nacl.public.PrivateKey(server_privkey_bytes)
else:
    raise Exception('Could not find privkey file')

_junk_parser = pyonionreq.junk.Parser(privkey=privkey.encode(), pubkey=privkey.public_key.encode())
print(privkey.public_key.encode().hex())
parse_junk = _junk_parser.parse_junk

