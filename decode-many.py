#! /usr/bin/env python3

import binascii
import base64
import binhex
import uu
import sys
import io
import string

def wrap_uu(func):
    """
    Convert a function
        f(in_file, out_file)
    to
        out_bytes = f(in_string)
    """
    def new_func(in_string):
        in_file = io.BytesIO(bytes(in_string))
        out_file = io.BytesIO()
        func(in_file, out_file)
        out_file.seek(0)
        return out_file.read()
    return new_func

def wrap_binhex(func):
    """
    Convert a function
        f(infilename, outfilename)
    to
        out_bytes = f(in_bytes)
    """
    raise NotImplementedError

decode_string_funcs = {
    'Base64' : base64.standard_b64decode,
    'Base32': base64.b32decode,
    'Base16': base64.b16decode,
    'Ascii85' : base64.a85decode,
    'Base85' : base64.b85decode,
    'Uuencoding' : wrap_uu(uu.decode),
    #'BinHex': wrap_binhex(binhex.hexbin),
}

encode_string_funcs = {
    'Base64' : base64.standard_b64encode,
    'Base32': base64.b32encode,
    'Base16': base64.b16encode,
    'Ascii85' : base64.a85encode,
    'Base85' : base64.b85encode,
    'Uuencoding' : wrap_uu(uu.encode),
    #'BinHex': wrap_binhex(binhex.binhex),
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
        except uu.Error:
            print(func_name, 'failed.')
            pass
        except ValueError:
            print(func_name, 'failed with ValueError.')
            pass

        if decoded:
            print(func_name, ':' , decoded)

def self_test():
    test_string = string.printable
    test_bytes = test_string.encode()
    print("Encoding and decoding this string: "+repr(test_string))
    for name, func in encode_string_funcs.items():
        print("======== " + name + " ========")
        encoded_bytes = func(test_bytes)
        decode_many(encoded_bytes)

if len(sys.argv) > 1:
    if sys.argv[1] == '-':
        # Use default encoding.
        decode_many(sys.stdin.read().encode())
    else:
        decode_many(open(sys.argv[1], 'rb').read())
else:
    self_test()

