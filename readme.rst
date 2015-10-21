This tries some common binary-to-ascii encodings
and a few ascii-to-ascii encodings.

Use it like this on a file::

    python3 try_decodings.py temp.txt

or like this in a pipe::

    $ printf 'ZXhhbXBsZSB0ZXh0' | python3 try_decodings.py -
    Base64 : b'example text'
    Base32 failed.
    Base16 failed.
    Ascii85 : b'\xb3d\xdb\xf7\xac^\xdb\xf5g@\x05\xef'
    Base85 : b'n ,\xbfg\x1a.\xc1"=\x9a\x86'
    Uuencoding failed.
    BinHex failed.
    ROT13 : b'MKuuoKOfMFO0MKu0'
    MIME quoted-printable : b'ZXhhbXBsZSB0ZXh0'
    Percent-encoding : b'ZXhhbXBsZSB0ZXh0'
    HTML : b'ZXhhbXBsZSB0ZXh0'
