readme.html : readme.rst
	rst2html readme.rst readme.html

clean :
	rm -f readme.html

format :
	black try_decodings.py

test :
	python3 try_decodings.py --selftest
