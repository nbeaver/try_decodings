This tries to decode bytes to some `binary-to-ascii encodings`_
as well as percent encoding, HTML entity encoding, and a few others.
It was inspired by a `StackExchange post`_.

.. _StackExchange post: http://softwarerecs.stackexchange.com/questions/18615/convert-an-enigmatic-string-using-many-common-decoding-algorithms-to-check-whic

.. _binary-to-ascii encodings: https://en.wikipedia.org/wiki/Binary-to-text_encoding

Use it like this on a file::

    python3 try_decodings.py temp.txt

or like this in a pipe::

    $ printf 'example text' | base64 | try_decodings.py
    Base64  : example text
    Ascii85 : b'\xb3d\xdb\xf7\xac^\xdb\xf5g@\x05\xef'
    Base85  : b'n ,\xbfg\x1a.\xc1"=\x9a\x86'
    ROT13   : MKuuoKOfMFO0MKu0
    Failed to decode: Base32, Base16, Uuencoding, BinHex
    Output same as input: MIME quoted-printable, Percent-encoding, HTML

For a demonstration, run the self-test::

    $ python3 try_decodings.py --selftest | less
