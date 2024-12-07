This Python script tries to decode bytes to plain text
using some common `binary-to-ascii encodings`_ like Base64,
percent encoding, HTML entity encoding, and a few others.
Its inspiration was a `StackExchange post`_ by `Nicolas Raoul`_.

.. _StackExchange post: http://softwarerecs.stackexchange.com/questions/18615/convert-an-enigmatic-string-using-many-common-decoding-algorithms-to-check-whic
.. _Nicolas Raoul: http://softwarerecs.stackexchange.com/users/140/nicolas-raoul
.. _binary-to-ascii encodings: https://en.wikipedia.org/wiki/Binary-to-text_encoding

Use it like this on a file::

    python3 try_decodings.py temp.txt

Use it like this in a pipe::

    $ printf 'example text' | base64 | try_decodings.py
    Base64  : example text
    Ascii85 : b'\xb3d\xdb\xf7\xac^\xdb\xf5g@\x05\xef'
    Base85  : b'n ,\xbfg\x1a.\xc1"=\x9a\x86'
    ROT13   : MKuuoKOfMFO0MKu0
    Failed to decode: Base32, Base16, Uuencoding, BinHex
    Output same as input: MIME quoted-printable, Percent-encoding, HTML

For a demonstration, run the self-test::

    $ python3 try_decodings.py --selftest | less

Nota bene: This script utilizes the binhex and uu modules that, after thirty 
years of inclusion, will be completely absent starting sometime during the 
lifespan of Python 3.  The easiest workaround for both developers and users 
is probably found in a containerized Python.  This project's makefile now 
includes a distrobox target that will install a small (<50MB) Alpine Linux 
container running Pyton 3.8, which predates the deprecation of the required 
standard library modules.  While "inside" the distrobox, one can interact with
the script exactly as described earlier without downgrading their native python
distribution.  Linux users can install Distrobox via their system tools, Windows
users can use the `Windows Subsystem for Linux`_ 

Assuming Distrobox and a container manager are installed (I recommend Podman), use
it from the project's directory like this::
    make distrobox
    distrobox enter try_decodings 

.. _Windows Subsystem for Linux: https://learn.microsoft.com/en-us/windows/wsl/install

-------
License
-------

This project is licensed under the terms of the `MIT license`_.

.. _MIT license: LICENSE.txt
