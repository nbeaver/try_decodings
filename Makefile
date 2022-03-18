readme.html : readme.rst
	rst2html readme.rst readme.html

clean :
	rm -f readme.html

format :
	# PEP8
	black --line-length 80 try_decodings.py

test :
	python3 try_decodings.py --self-test
