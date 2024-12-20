#! /usr/bin/env python3

import argparse
import base64
import binascii
import codecs  # for ROT13
import collections
import html
import io
import logging
import os
import quopri
import struct
import sys
import tempfile
import urllib.parse  # for percent-encoding.

"""
Include the latest binhex source release before deprecation.
https://github.com/python/cpython/blob/3.10/Lib/binhex.py
"""
"""Macintosh binhex compression/decompression.

easy interface:
binhex(inputfilename, outputfilename)
hexbin(inputfilename, outputfilename)
"""

#
# Jack Jansen, CWI, August 1995.
#
# The module is supposed to be as compatible as possible. Especially the
# easy interface should work "as expected" on any platform.
# XXXX Note: currently, textfiles appear in mac-form on all platforms.
# We seem to lack a simple character-translate in python.
# (we should probably use ISO-Latin-1 on all but the mac platform).
# XXXX The simple routines are too simple: they expect to hold the complete
# files in-core. Should be fixed.
# XXXX It would be nice to handle AppleDouble format on unix
# (for servers serving macs).
# XXXX I don't understand what happens when you get 0x90 times the same byte on
# input. The resulting code (xx 90 90) would appear to be interpreted as an
# escaped *value* of 0x90. All coders I've seen appear to ignore this nicety...
#

class BinHexError(Exception):
    pass

# States (what have we written)
_DID_HEADER = 0
_DID_DATA = 1

# Various constants
REASONABLY_LARGE = 32768  # Minimal amount we pass the rle-coder
LINELEN = 64
RUNCHAR = b"\x90"

#
# This code is no longer byte-order dependent


class FInfo:
    def __init__(self):
        self.Type = '????'
        self.Creator = '????'
        self.Flags = 0

def getfileinfo(name):
    finfo = FInfo()
    with io.open(name, 'rb') as fp:
        # Quick check for textfile
        data = fp.read(512)
        if 0 not in data:
            finfo.Type = 'TEXT'
        fp.seek(0, 2)
        dsize = fp.tell()
    dir, file = os.path.split(name)
    file = file.replace(':', '-', 1)
    return file, finfo, dsize, 0

class openrsrc:
    def __init__(self, *args):
        pass

    def read(self, *args):
        return b''

    def write(self, *args):
        pass

    def close(self):
        pass

class _Hqxcoderengine:
    """Write data to the coder in 3-byte chunks"""

    def __init__(self, ofp):
        self.ofp = ofp
        self.data = b''
        self.hqxdata = b''
        self.linelen = LINELEN - 1

    def write(self, data):
        self.data = self.data + data
        datalen = len(self.data)
        todo = (datalen // 3) * 3
        data = self.data[:todo]
        self.data = self.data[todo:]
        if not data:
            return
        self.hqxdata = self.hqxdata + binascii.b2a_hqx(data)
        self._flush(0)

    def _flush(self, force):
        first = 0
        while first <= len(self.hqxdata) - self.linelen:
            last = first + self.linelen
            self.ofp.write(self.hqxdata[first:last] + b'\r')
            self.linelen = LINELEN
            first = last
        self.hqxdata = self.hqxdata[first:]
        if force:
            self.ofp.write(self.hqxdata + b':\r')

    def close(self):
        if self.data:
            self.hqxdata = self.hqxdata + binascii.b2a_hqx(self.data)
        self._flush(1)
        self.ofp.close()
        del self.ofp

class _Rlecoderengine:
    """Write data to the RLE-coder in suitably large chunks"""

    def __init__(self, ofp):
        self.ofp = ofp
        self.data = b''

    def write(self, data):
        self.data = self.data + data
        if len(self.data) < REASONABLY_LARGE:
            return
        rledata = binascii.rlecode_hqx(self.data)
        self.ofp.write(rledata)
        self.data = b''

    def close(self):
        if self.data:
            rledata = binascii.rlecode_hqx(self.data)
            self.ofp.write(rledata)
        self.ofp.close()
        del self.ofp

class BinHex:
    def __init__(self, name_finfo_dlen_rlen, ofp):
        name, finfo, dlen, rlen = name_finfo_dlen_rlen
        close_on_error = False
        if isinstance(ofp, str):
            ofname = ofp
            ofp = io.open(ofname, 'wb')
            close_on_error = True
        try:
            ofp.write(b'(This file must be converted with BinHex 4.0)\r\r:')
            hqxer = _Hqxcoderengine(ofp)
            self.ofp = _Rlecoderengine(hqxer)
            self.crc = 0
            if finfo is None:
                finfo = FInfo()
            self.dlen = dlen
            self.rlen = rlen
            self._writeinfo(name, finfo)
            self.state = _DID_HEADER
        except:
            if close_on_error:
                ofp.close()
            raise

    def _writeinfo(self, name, finfo):
        nl = len(name)
        if nl > 63:
            raise BinHexError('Filename too long')
        d = bytes([nl]) + name.encode("latin-1") + b'\0'
        tp, cr = finfo.Type, finfo.Creator
        if isinstance(tp, str):
            tp = tp.encode("latin-1")
        if isinstance(cr, str):
            cr = cr.encode("latin-1")
        d2 = tp + cr

        # Force all structs to be packed with big-endian
        d3 = struct.pack('>h', finfo.Flags)
        d4 = struct.pack('>ii', self.dlen, self.rlen)
        info = d + d2 + d3 + d4
        self._write(info)
        self._writecrc()

    def _write(self, data):
        self.crc = binascii.crc_hqx(data, self.crc)
        self.ofp.write(data)

    def _writecrc(self):
        # XXXX Should this be here??
        # self.crc = binascii.crc_hqx('\0\0', self.crc)
        if self.crc < 0:
            fmt = '>h'
        else:
            fmt = '>H'
        self.ofp.write(struct.pack(fmt, self.crc))
        self.crc = 0

    def write(self, data):
        if self.state != _DID_HEADER:
            raise BinHexError('Writing data at the wrong time')
        self.dlen = self.dlen - len(data)
        self._write(data)

    def close_data(self):
        if self.dlen != 0:
            raise BinHexError('Incorrect data size, diff=%r' % (self.rlen,))
        self._writecrc()
        self.state = _DID_DATA

    def write_rsrc(self, data):
        if self.state < _DID_DATA:
            self.close_data()
        if self.state != _DID_DATA:
            raise BinHexError('Writing resource data at the wrong time')
        self.rlen = self.rlen - len(data)
        self._write(data)

    def close(self):
        if self.state is None:
            return
        try:
            if self.state < _DID_DATA:
                self.close_data()
            if self.state != _DID_DATA:
                raise BinHexError('Close at the wrong time')
            if self.rlen != 0:
                raise BinHexError("Incorrect resource-datasize, diff=%r" % (self.rlen,))
            self._writecrc()
        finally:
            self.state = None
            ofp = self.ofp
            del self.ofp
            ofp.close()

def binhex(inp, out):
    """binhex(infilename, outfilename): create binhex-encoded copy of a file"""
    finfo = getfileinfo(inp)
    ofp = BinHex(finfo, out)

    with io.open(inp, 'rb') as ifp:
        # XXXX Do textfile translation on non-mac systems
        while True:
            d = ifp.read(128000)
            if not d: break
            ofp.write(d)
        ofp.close_data()

    ifp = openrsrc(inp, 'rb')
    while True:
        d = ifp.read(128000)
        if not d: break
        ofp.write_rsrc(d)
    ofp.close()
    ifp.close()

class _Hqxdecoderengine:
    """Read data via the decoder in 4-byte chunks"""

    def __init__(self, ifp):
        self.ifp = ifp
        self.eof = 0

    def read(self, totalwtd):
        """Read at least wtd bytes (or until EOF)"""
        decdata = b''
        wtd = totalwtd
        #
        # The loop here is convoluted, since we don't really now how
        # much to decode: there may be newlines in the incoming data.
        while wtd > 0:
            if self.eof: return decdata
            wtd = ((wtd + 2) // 3) * 4
            data = self.ifp.read(wtd)
            #
            # Next problem: there may not be a complete number of
            # bytes in what we pass to a2b. Solve by yet another
            # loop.
            #
            while True:
                try:
                    decdatacur, self.eof = binascii.a2b_hqx(data)
                    break
                except binascii.Incomplete:
                    pass
                newdata = self.ifp.read(1)
                if not newdata:
                    raise BinHexError('Premature EOF on binhex file')
                data = data + newdata
            decdata = decdata + decdatacur
            wtd = totalwtd - len(decdata)
            if not decdata and not self.eof:
                raise BinHexError('Premature EOF on binhex file')
        return decdata

    def close(self):
        self.ifp.close()

class _Rledecoderengine:
    """Read data via the RLE-coder"""

    def __init__(self, ifp):
        self.ifp = ifp
        self.pre_buffer = b''
        self.post_buffer = b''
        self.eof = 0

    def read(self, wtd):
        if wtd > len(self.post_buffer):
            self._fill(wtd - len(self.post_buffer))
        rv = self.post_buffer[:wtd]
        self.post_buffer = self.post_buffer[wtd:]
        return rv

    def _fill(self, wtd):
        self.pre_buffer = self.pre_buffer + self.ifp.read(wtd + 4)
        if self.ifp.eof:
            self.post_buffer = self.post_buffer + \
                binascii.rledecode_hqx(self.pre_buffer)
            self.pre_buffer = b''
            return

        #
        # Obfuscated code ahead. We have to take care that we don't
        # end up with an orphaned RUNCHAR later on. So, we keep a couple
        # of bytes in the buffer, depending on what the end of
        # the buffer looks like:
        # '\220\0\220' - Keep 3 bytes: repeated \220 (escaped as \220\0)
        # '?\220' - Keep 2 bytes: repeated something-else
        # '\220\0' - Escaped \220: Keep 2 bytes.
        # '?\220?' - Complete repeat sequence: decode all
        # otherwise: keep 1 byte.
        #
        mark = len(self.pre_buffer)
        if self.pre_buffer[-3:] == RUNCHAR + b'\0' + RUNCHAR:
            mark = mark - 3
        elif self.pre_buffer[-1:] == RUNCHAR:
            mark = mark - 2
        elif self.pre_buffer[-2:] == RUNCHAR + b'\0':
            mark = mark - 2
        elif self.pre_buffer[-2:-1] == RUNCHAR:
            pass # Decode all
        else:
            mark = mark - 1

        self.post_buffer = self.post_buffer + \
            binascii.rledecode_hqx(self.pre_buffer[:mark])
        self.pre_buffer = self.pre_buffer[mark:]

    def close(self):
        self.ifp.close()

class HexBin:
    def __init__(self, ifp):
        if isinstance(ifp, str):
            ifp = io.open(ifp, 'rb')
        #
        # Find initial colon.
        #
        while True:
            ch = ifp.read(1)
            if not ch:
                raise BinHexError("No binhex data found")
            # Cater for \r\n terminated lines (which show up as \n\r, hence
            # all lines start with \r)
            if ch == b'\r':
                continue
            if ch == b':':
                break

        hqxifp = _Hqxdecoderengine(ifp)
        self.ifp = _Rledecoderengine(hqxifp)
        self.crc = 0
        self._readheader()

    def _read(self, len):
        data = self.ifp.read(len)
        self.crc = binascii.crc_hqx(data, self.crc)
        return data

    def _checkcrc(self):
        filecrc = struct.unpack('>h', self.ifp.read(2))[0] & 0xffff
        #self.crc = binascii.crc_hqx('\0\0', self.crc)
        # XXXX Is this needed??
        self.crc = self.crc & 0xffff
        if filecrc != self.crc:
            raise BinHexError('CRC error, computed %x, read %x'
                        % (self.crc, filecrc))
        self.crc = 0

    def _readheader(self):
        len = self._read(1)
        fname = self._read(ord(len))
        rest = self._read(1 + 4 + 4 + 2 + 4 + 4)
        self._checkcrc()

        type = rest[1:5]
        creator = rest[5:9]
        flags = struct.unpack('>h', rest[9:11])[0]
        self.dlen = struct.unpack('>l', rest[11:15])[0]
        self.rlen = struct.unpack('>l', rest[15:19])[0]

        self.FName = fname
        self.FInfo = FInfo()
        self.FInfo.Creator = creator
        self.FInfo.Type = type
        self.FInfo.Flags = flags

        self.state = _DID_HEADER

    def read(self, *n):
        if self.state != _DID_HEADER:
            raise BinHexError('Read data at wrong time')
        if n:
            n = n[0]
            n = min(n, self.dlen)
        else:
            n = self.dlen
        rv = b''
        while len(rv) < n:
            rv = rv + self._read(n-len(rv))
        self.dlen = self.dlen - n
        return rv

    def close_data(self):
        if self.state != _DID_HEADER:
            raise BinHexError('close_data at wrong time')
        if self.dlen:
            dummy = self._read(self.dlen)
        self._checkcrc()
        self.state = _DID_DATA

    def read_rsrc(self, *n):
        if self.state == _DID_HEADER:
            self.close_data()
        if self.state != _DID_DATA:
            raise BinHexError('Read resource data at wrong time')
        if n:
            n = n[0]
            n = min(n, self.rlen)
        else:
            n = self.rlen
        self.rlen = self.rlen - n
        return self._read(n)

    def close(self):
        if self.state is None:
            return
        try:
            if self.rlen:
                dummy = self.read_rsrc(self.rlen)
            self._checkcrc()
        finally:
            self.state = None
            self.ifp.close()

def hexbin(inp, out):
    """hexbin(infilename, outfilename) - Decode binhexed file"""
    ifp = HexBin(inp)
    finfo = ifp.FInfo
    if not out:
        out = ifp.FName

    with io.open(out, 'wb') as ofp:
        # XXXX Do translation on non-mac systems
        while True:
            d = ifp.read(128000)
            if not d: break
            ofp.write(d)
    ifp.close_data()

    d = ifp.read_rsrc(128000)
    if d:
        ofp = openrsrc(out, 'wb')
        ofp.write(d)
        while True:
            d = ifp.read_rsrc(128000)
            if not d: break
            ofp.write(d)
        ofp.close()

    ifp.close()
"""
End binhex source code.
"""

"""
Include the latest uu source release before deprecation.
https://github.com/python/cpython/blob/3.12/Lib/uu.py
"""
# Copyright 1994 by Lance Ellinghouse
# Cathedral City, California Republic, United States of America.
#                        All Rights Reserved
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose and without fee is hereby granted,
# provided that the above copyright notice appear in all copies and that
# both that copyright notice and this permission notice appear in
# supporting documentation, and that the name of Lance Ellinghouse
# not be used in advertising or publicity pertaining to distribution
# of the software without specific, written prior permission.
# LANCE ELLINGHOUSE DISCLAIMS ALL WARRANTIES WITH REGARD TO
# THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS, IN NO EVENT SHALL LANCE ELLINGHOUSE CENTRUM BE LIABLE
# FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#
# Modified by Jack Jansen, CWI, July 1995:
# - Use binascii module to do the actual line-by-line conversion
#   between ascii and binary. This results in a 1000-fold speedup. The C
#   version is still 5 times faster, though.
# - Arguments more compliant with python standard

"""Implementation of the UUencode and UUdecode functions.

uuencode(in_file, out_file [,name, mode], *, backtick=False)
uudecode(in_file [, out_file, mode, quiet])
"""

class UUDecodeError(Exception):
    pass

def uuencode(in_file, out_file, name=None, mode=None, *, backtick=False):
    """Uuencode file"""
    #
    # If in_file is a pathname open it and change defaults
    #
    opened_files = []
    try:
        if in_file == '-':
            in_file = sys.stdin.buffer
        elif isinstance(in_file, str):
            if name is None:
                name = os.path.basename(in_file)
            if mode is None:
                try:
                    mode = os.stat(in_file).st_mode
                except AttributeError:
                    pass
            in_file = open(in_file, 'rb')
            opened_files.append(in_file)
        #
        # Open out_file if it is a pathname
        #
        if out_file == '-':
            out_file = sys.stdout.buffer
        elif isinstance(out_file, str):
            out_file = open(out_file, 'wb')
            opened_files.append(out_file)
        #
        # Set defaults for name and mode
        #
        if name is None:
            name = '-'
        if mode is None:
            mode = 0o666

        #
        # Remove newline chars from name
        #
        name = name.replace('\n','\\n')
        name = name.replace('\r','\\r')

        #
        # Write the data
        #
        out_file.write(('begin %o %s\n' % ((mode & 0o777), name)).encode("ascii"))
        data = in_file.read(45)
        while len(data) > 0:
            # requires version 3.7 or later.
            out_file.write(binascii.b2a_uu(data, backtick=backtick))
            data = in_file.read(45)
        if backtick:
            out_file.write(b'`\nend\n')
        else:
            out_file.write(b' \nend\n')
    finally:
        for f in opened_files:
            f.close()


def uudecode(in_file, out_file=None, mode=None, quiet=False):
    """Decode uuencoded file"""
    #
    # Open the input file, if needed.
    #
    opened_files = []
    if in_file == '-':
        in_file = sys.stdin.buffer
    elif isinstance(in_file, str):
        in_file = open(in_file, 'rb')
        opened_files.append(in_file)

    try:
        #
        # Read until a begin is encountered or we've exhausted the file
        #
        while True:
            hdr = in_file.readline()
            if not hdr:
                raise UUDecodeError('No valid begin line found in input file')
            if not hdr.startswith(b'begin'):
                continue
            hdrfields = hdr.split(b' ', 2)
            if len(hdrfields) == 3 and hdrfields[0] == b'begin':
                try:
                    int(hdrfields[1], 8)
                    break
                except ValueError:
                    pass
        if out_file is None:
            # If the filename isn't ASCII, what's up with that?!?
            out_file = hdrfields[2].rstrip(b' \t\r\n\f').decode("ascii")
            if os.path.exists(out_file):
                raise UUDecodeError(f'Cannot overwrite existing file: {out_file}')
            if (out_file.startswith(os.sep) or
                f'..{os.sep}' in out_file or (
                    os.altsep and
                    (out_file.startswith(os.altsep) or
                     f'..{os.altsep}' in out_file))
               ):
                raise UUDecodeError(f'Refusing to write to {out_file} due to directory traversal')
        if mode is None:
            mode = int(hdrfields[1], 8)
        #
        # Open the output file
        #
        if out_file == '-':
            out_file = sys.stdout.buffer
        elif isinstance(out_file, str):
            fp = open(out_file, 'wb')
            os.chmod(out_file, mode)
            out_file = fp
            opened_files.append(out_file)
        #
        # Main decoding loop
        #
        s = in_file.readline()
        while s and s.strip(b' \t\r\n\f') != b'end':
            try:
                data = binascii.a2b_uu(s)
            except binascii.Error as v:
                # Workaround for broken uuencoders by /Fredrik Lundh
                nbytes = (((s[0]-32) & 63) * 4 + 5) // 3
                data = binascii.a2b_uu(s[:nbytes])
                if not quiet:
                    sys.stderr.write("Warning: %s\n" % v)
            out_file.write(data)
            s = in_file.readline()
        if not s:
            raise UUDecodeError('Truncated input file')
    finally:
        for f in opened_files:
            f.close()


"""
End uu source code.
"""

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
        in_file = tempfile.NamedTemporaryFile()
        in_file.write(in_bytes)
        in_file.seek(0)
        out_file = tempfile.NamedTemporaryFile()
        func(in_file.name, out_file.name)
        out_file.seek(0)
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
        out_str = func(in_str, "rot-13")
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
decode_string_funcs["Base64"] = base64.standard_b64decode
decode_string_funcs["Base32"] = base64.b32decode
decode_string_funcs["Base16"] = base64.b16decode
decode_string_funcs["Ascii85"] = base64.a85decode
decode_string_funcs["Base85"] = base64.b85decode
decode_string_funcs["Uuencoding"] = wrap_uu(uudecode)
decode_string_funcs["BinHex"] = wrap_binhex(hexbin)
decode_string_funcs["ROT13"] = wrap_rot13(codecs.decode)
decode_string_funcs["MIME quoted-printable"] = quopri.decodestring
decode_string_funcs["Percent-encoding"] = urllib.parse.unquote_to_bytes
decode_string_funcs["HTML"] = wrap_html(html.unescape)

encode_string_funcs = collections.OrderedDict()
encode_string_funcs["Base64"] = base64.standard_b64encode
encode_string_funcs["Base32"] = base64.b32encode
encode_string_funcs["Base16"] = base64.b16encode
encode_string_funcs["Ascii85"] = base64.a85encode
encode_string_funcs["Base85"] = base64.b85encode
encode_string_funcs["Uuencoding"] = wrap_uu(uuencode)
encode_string_funcs["BinHex"] = wrap_binhex(binhex)
encode_string_funcs["ROT13"] = wrap_rot13(codecs.encode)
encode_string_funcs["MIME quoted-printable"] = quopri.encodestring
encode_string_funcs["Percent-encoding"] = wrap_percent_encode
encode_string_funcs["HTML"] = wrap_html(html.escape)


def decode_bytes(unknown_bytes, func, encoding):
    assert isinstance(
        unknown_bytes, bytes
    ), "{0} is type {1} not an instance of 'bytes' in encoding {2}".format(
        repr(unknown_bytes), type(unknown_bytes), encoding
    )

    decoded_bytes = None
    try:
        decoded_bytes = func(unknown_bytes)
    except binascii.Error:
        pass
    except BinHexError:
        pass
    except UUDecodeError:
        pass
    except ValueError:
        pass
    return decoded_bytes


# TODO: make this just decode and return a dict
# instead of also printing the output
# to facilitate testing.
def decode_and_print(unknown_bytes):
    if unknown_bytes == b"":
        logging.error("no input to decode")
    failed_encodings = []
    no_difference = []
    output_dict = collections.OrderedDict()
    for name, func in decode_string_funcs.items():
        decoded_bytes = decode_bytes(unknown_bytes, func, name)
        if decoded_bytes:
            if decoded_bytes == unknown_bytes:
                no_difference.append(name)
            else:
                try:
                    unicode_str = decoded_bytes.decode()
                    output_dict[name] = unicode_str
                except UnicodeDecodeError:
                    output_dict[name] = repr(decoded_bytes)
        else:
            failed_encodings.append(name)
    if output_dict:
        column_chars = max([len(name) for name in output_dict.keys()])
        for name, output in output_dict.items():
            print("{} : {}".format(name.ljust(column_chars), output))
    print("Failed to decode:", ", ".join(failed_encodings))
    print("Output same as input:", ", ".join(no_difference))


def self_test():
    import string

    test_string = string.printable
    # Todo: test unicode as well, e.g. unicodedata.lookup('snowman')
    test_bytes = test_string.encode()
    print("Encoding and decoding this string: " + repr(test_string))
    for encoding, func in encode_string_funcs.items():
        print("======== " + encoding + " ========")
        encoded_bytes = func(test_bytes)
        print(encoded_bytes)
        decode_and_print(encoded_bytes)
        assert (
            decode_bytes(encoded_bytes, decode_string_funcs[encoding], encoding)
            == test_bytes
        ), "Round-tripping printable ASCII characters failed."


if __name__ == "__main__":
    # TODO: add an --encodings flag to list encodings.
    # TODO: add a --reverse flag to encode instead of decode.
    parser = argparse.ArgumentParser(
        description="Try binary-to-ascii decodings on a given file or stdin."
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="More verbose logging",
        dest="loglevel",
        default=logging.WARNING,
        action="store_const",
        const=logging.INFO,
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="Enable debugging logs",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
    )
    parser.add_argument(
        "--self-test", help="Run a self-test", action="store_true"
    )
    # TODO: should this be a filter by default,
    # or should it require a `-' argument to function that way
    # so that --self-test and infile can be mutually exclusive arguments?
    parser.add_argument(
        "infile",
        nargs="?",
        type=argparse.FileType("rb"),
        default=sys.stdin.buffer,
        help="Input file (or stdin)",
    )
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)
    if args.self_test:
        if args.infile != sys.stdin.buffer:
            logging.warning(
                "running self-test, not processing file: '{}'".format(
                    args.infile.name
                )
            )
        self_test()
    else:
        decode_and_print(args.infile.read())
