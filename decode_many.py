#! /usr/bin/env python3

import binascii
import base64
import binhex
import uu
import io # for uuencode
import sys
import codecs # for ROT13
import urllib.parse # for percent-encoding.
import quopri
import html
import collections

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
        f(in_filename, out_filename)
    to
        out_bytes = f(in_bytes)
    """
    def new_func(in_bytes):
        in_filename = 'binhex.in'
        with open(in_filename, 'wb') as in_file:
            in_file.write(in_bytes)
        out_filename = 'binhex.out'
        # We can't use tempfiles because hexbin() calls close().
        func(in_filename, out_filename)
        with open(out_filename, 'rb') as out_file:
            out_bytes = out_file.read()
        return out_bytes

    return new_func

def wrap_rot13(func):
    # We can't use functools.partial
    # because codecs.encode takes no keyword arguments.
    def new_func(in_bytes):
        # I'm not sure this is correct,
        # but 'rot-13' is str-to-str only.
        in_str = in_bytes.decode()
        out_str = func(in_str, 'rot-13')
        return out_str.encode()
    return new_func

def wrap_html(func):
    def new_func(in_bytes):
        in_str = in_bytes.decode()
        out_str = func(in_str)
        return out_str.encode()
    return new_func

def wrap_percent_encode(in_string):
    return urllib.parse.quote_from_bytes(in_string).encode()

decode_string_funcs = collections.OrderedDict()
decode_string_funcs['Base64'] = base64.standard_b64decode
decode_string_funcs['Base32'] = base64.b32decode
decode_string_funcs['Base16'] = base64.b16decode
decode_string_funcs['Ascii85'] = base64.a85decode
decode_string_funcs['Base85'] = base64.b85decode
decode_string_funcs['Uuencoding'] = wrap_uu(uu.decode)
decode_string_funcs['BinHex'] = wrap_binhex(binhex.hexbin)
decode_string_funcs['ROT13'] = wrap_rot13(codecs.decode)
decode_string_funcs['Percent-encoding'] = urllib.parse.unquote_to_bytes
decode_string_funcs['MIME quoted-printable'] = quopri.decodestring
decode_string_funcs['HTML'] = wrap_html(html.unescape)

encode_string_funcs = collections.OrderedDict()
encode_string_funcs['Base64'] = base64.standard_b64encode
encode_string_funcs['Base32'] = base64.b32encode
encode_string_funcs['Base16'] = base64.b16encode
encode_string_funcs['Ascii85'] = base64.a85encode
encode_string_funcs['Base85'] = base64.b85encode
encode_string_funcs['Uuencoding'] = wrap_uu(uu.encode)
encode_string_funcs['BinHex'] = wrap_binhex(binhex.binhex)
encode_string_funcs['ROT13'] = wrap_rot13(codecs.encode)
encode_string_funcs['Percent-encoding'] = wrap_percent_encode
encode_string_funcs['MIME quoted-printable'] = quopri.encodestring
encode_string_funcs['HTML'] = wrap_html(html.escape)

def decode_bytes(unknown_bytes, func, encoding):
    assert isinstance(unknown_bytes, bytes), "{0} is type {1} not an instance of 'bytes' in encoding {2}".format(repr(unknown_bytes), type(unknown_bytes), encoding)
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
    import string
    test_string = string.printable
    test_bytes = test_string.encode()
    print("Encoding and decoding this string: "+repr(test_string))
    for encoding, func in encode_string_funcs.items():
        print("======== " + encoding + " ========")
        encoded_bytes = func(test_bytes)
        print(encoded_bytes)
        decode_and_print(encoded_bytes)
        assert decode_bytes(encoded_bytes, decode_string_funcs[encoding], encoding) == test_bytes, 'Round-tripping printable ASCII characters failed.'

if len(sys.argv) > 1:
    if sys.argv[1] == '-':
        # Use default encoding.
        decode_and_print(sys.stdin.read().encode())
    else:
        decode_and_print(open(sys.argv[1], 'rb').read())
elif __name__ == "__main__":
    self_test()
