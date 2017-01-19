readme.html : readme.rst
	rst2html readme.rst readme.html

clean :
	rm -f readme.html

test :
	python3 try_decodings.py --selftest
