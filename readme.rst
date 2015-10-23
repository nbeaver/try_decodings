This tries some common binary-to-ascii encodings
and a few ascii-to-ascii encodings.

Use it like this on a file::

    python3 try_decodings.py temp.txt

or like this in a pipe::

    $ printf 'ZXhhbXBsZSB0ZXh0' | try_decodings.py
    Base64  : example text
    Ascii85 : b'\xb3d\xdb\xf7\xac^\xdb\xf5g@\x05\xef'
    Base85  : b'n ,\xbfg\x1a.\xc1"=\x9a\x86'
    ROT13   : MKuuoKOfMFO0MKu0
    Failed to decode: Base32, Base16, Uuencoding, BinHex
    Output same as input: MIME quoted-printable, Percent-encoding, HTML

For a demonstration, run the self-test::

    $ python3 try_decodings.py --selftest | less
