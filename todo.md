
# Enhancements #

- [x] [Align output in columns.](https://github.com/nbeaver/try-decodings/issues/1)
- [x] [Move list of failed encodings to the end.](https://github.com/nbeaver/try-decodings/issues/1)
- [x] [Suppress output that is unchanged.](https://github.com/nbeaver/try-decodings/issues/2)
- [ ] Terse mode so that it can be piped unchanged to other text filters.

# Bugs #

- [x] Does not handle case when all input either fails or is unchanged, e.g. `printf '\u9090' | try_decodings.py`
- [ ] Does not properly handle output of control characters, e.g. Ascii85 output for `echo '%40' | try_decodings.py`
