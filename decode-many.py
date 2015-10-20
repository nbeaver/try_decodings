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
    def new_func(in_bytes):
        in_file = io.BytesIO(in_bytes)
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

def decode_bytes(unknown_bytes, func, encoding):
        decoded_bytes = None
        try:
            decoded_bytes = func(unknown_bytes)
        except binascii.Error:
            print(encoding, 'failed.')
            pass
        except binhex.Error:
            print(encoding, 'failed.')
            pass
        except uu.Error:
            print(encoding, 'failed.')
            pass
        except ValueError:
            print(encoding, 'failed with ValueError.')
            pass
        return decoded_bytes

def decode_and_print(unknown_bytes):
    for name, func in decode_string_funcs.items():
        decoded = decode_bytes(unknown_bytes, func, name)
        if decoded:
            print(name, ':' , decoded)

def self_test():
    test_string = string.printable
    test_bytes = test_string.encode()
    print("Encoding and decoding this string: "+repr(test_string))
    for encoding, func in encode_string_funcs.items():
        print("======== " + encoding + " ========")
        encoded_bytes = func(test_bytes)
        decode_and_print(encoded_bytes)
        assert(decode_bytes(encoded_bytes, decode_string_funcs[encoding], encoding) == test_bytes) 

        # TODO: assert decoded_bytes == test_bytes

if len(sys.argv) > 1:
    if sys.argv[1] == '-':
        # Use default encoding.
        decode_and_print(sys.stdin.read().encode())
    else:
        decode_and_print(open(sys.argv[1], 'rb').read())
else:
    self_test()
