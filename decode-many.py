#! /usr/bin/env python3

import binascii
import base64
import binhex
import uu
import sys
import io

if len(sys.argv) == 1:
    in_string = sys.stdin.read()
else:
    in_string = open(sys.argv[1]).read()

decode_string_funcs = {
    'Base64' : base64.standard_b64decode,
    'Base32': base64.b32decode,
    'Base16': base64.b16decode,
    'Ascii85' : base64.a85decode,
    'Base85' : base64.b85decode,
}

for func_name, func in decode_string_funcs.items():
    decoded = None
    try:
        decoded = func(in_string)
    except binascii.Error:
        print(func_name, 'failed.')
        pass

    if decoded:
        print(func_name, ':' , decoded)

print(in_string, type(in_string))
if in_string.startswith('blah'):
    print 'hi'
in_file = io.StringIO(in_string)
out_file = io.StringIO()
uu.decode(in_file, out_file, mode='w')

# /usr/lib/python3.4/uu.py

decode_file_funcs = {
    'Uuencoding' : uu.decode,
    'BinHex': binhex.hexbin,
}

for func_name, func in decode_file_funcs.items():
    decoded = None
    in_file = io.StringIO(in_string)
    out_file = io.StringIO()

    try:
        func(in_file, out_file)
        decoded = out_file.read()
    except binhex.Error:
        print(func_name, 'failed.')
        pass

    if decoded:
        print(func_name, ':', decoded)
