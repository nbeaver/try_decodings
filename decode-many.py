#! /usr/bin/env python3

import binascii
import base64
import binhex
import uu
import sys
import io
import string

def wrap_file_func(file_func):
    """
    Convert a function like
    f(in, out)
    to
    out = f(in)
    """
    def local_func(in_bytes):
        in_file = io.BytesIO(in_bytes)
        out_file = io.BytesIO()
        file_func(in_file, out_file)
        return out_file.read()
    return local_func

decode_string_funcs = {
    'Base64' : base64.standard_b64decode,
    'Base32': base64.b32decode,
    'Base16': base64.b16decode,
    'Ascii85' : base64.a85decode,
    'Base85' : base64.b85decode,
    'Uuencoding' : wrap_file_func(uu.decode),
    'BinHex': wrap_file_func(binhex.hexbin),
}

def decode_many(unknown_string):
    for func_name, func in decode_string_funcs.items():
        decoded = None
        try:
            decoded = func(unknown_string)
        except binascii.Error:
            print(func_name, 'failed.')
            pass
        except binhex.Error:
            print(func_name, 'failed.')
            pass

        if decoded:
            print(func_name, ':' , decoded)

def self_test():
    test_bytes = string.printable.encode('utf8')
    base64_bytes = base64.standard_b64encode(test_bytes)
    decode_many(base64_bytes)

if len(sys.argv) > 1:
    if sys.argv[1] == '-':
        decode_many(sys.stdin.read())
    else:
        decode_many(sys.argv[1].read())
else:
    self_test()

