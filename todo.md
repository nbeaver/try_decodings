
# Enhancements #

- [x] [Align output in columns.](https://github.com/nbeaver/try-decodings/issues/1)

- [x] [Move list of failed encodings to the end.](https://github.com/nbeaver/try-decodings/issues/1)

- [x] [Suppress output that is unchanged.](https://github.com/nbeaver/try-decodings/issues/2)

- [x] Use `argparse` package for better command-line parsing.

- [ ] Terse mode so that it can be piped unchanged to other text filters.

- [ ] Output in JSON format for sending to other programs.

- [ ] Output null-delimited format for processing with e.g. `xargs --null`

- [ ] Check how this handles very large input files.

- [ ] Check how this handles /dev/null.

- [ ] Check how this handles /dev/zero.

- [ ] Create example files for automated testing of command line functionality.

- [ ] Create automated tests for stdin.

# Bugs #

- [x] Fix missing uu library by copying the source code https://docs.python.org/3.12/library/uu.html https://github.com/python/cpython/blob/3.12/Lib/uu.py

- [x] Fix missing binhex library by copying the source code https://docs.python.org/3.10/library/binhex.html https://github.com/python/cpython/blob/3.10/Lib/binhex.py

- [x] Does not handle case when all input either fails or is unchanged,
      e.g. `printf '\u9090' | try_decodings.py`

- [ ] Does not properly handle output of control characters,
      e.g. Ascii85 output for `echo '%40' | try_decodings.py`
      or `echo %7D | try_decodings.py`
