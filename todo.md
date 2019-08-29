
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

# Bugs #

- [x] Does not handle case when all input either fails or is unchanged,
      e.g. `printf '\u9090' | try_decodings.py`

- [ ] Does not properly handle output of control characters,
      e.g. Ascii85 output for `echo '%40' | try_decodings.py`
      or `echo %7D | try_decodings.py`
