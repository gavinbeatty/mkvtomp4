RM = rm -f
PANDOC = pandoc

default: doc
.PHONY: default

PROJECT = mkvtomp4

doc: doc/$(PROJECT).1 doc/$(PROJECT).1.html doc/$(PROJECT).txt
.PHONY: doc

doc/$(PROJECT).1: doc/$(PROJECT).1.txt
	$(PANDOC) -s -w man -o doc/$(PROJECT).1 doc/$(PROJECT).1.txt
doc/$(PROJECT).1.html: doc/$(PROJECT).1.txt
	$(PANDOC) -s -w html -o doc/$(PROJECT).1.html doc/$(PROJECT).1.txt
doc/$(PROJECT).txt: doc/$(PROJECT).1.txt
	$(PANDOC) -s -w plain -o doc/$(PROJECT).txt doc/$(PROJECT).1.txt
clean-doc:
	$(RM) doc/$(PROJECT).1 doc/$(PROJECT).1.html doc/$(PROJECT).txt
.PHONY: clean-doc
clean-pyc:
	find . -name '*.pyc' -print0 | xargs -0 rm -f
.PHONY: clean-pyc
clean: clean-doc clean-pyc
.PHONY: clean

pep8:
	@find . -name '*.py' -print0 | xargs -0 pep8
pyflakes:
	@find . -name '*.py' -print0 | xargs -0 pyflakes
.PHONY: pep8 pyflakes
