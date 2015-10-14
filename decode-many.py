#! /usr/bin/env python3

import base64
import binascii
import sys

if len(sys.argv) == 1:
    in_string = sys.stdin.read()
else:
    in_string = open(sys.argv[1]).read()

decode_funcs = {
    'Base64' : base64.standard_b64decode,
    'Base32': base64.b32decode,
    'Base16': base64.b16decode,
}

for func_name, func in decode_funcs.items():
    decoded = None
    try:
        decoded = func(in_string)
    except binascii.Error:
        print(func_name, 'failed.')
        pass

    if decoded:
        print(func_name, ':' , decoded)

