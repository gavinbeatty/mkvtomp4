RM = rm -f
PANDOC = pandoc
FIND = find
PEP8 = pep8
PYCODESTYLE = pycodestyle
PYFLAKES = pyflakes

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
	$(FIND) . -name '*.pyc' -print0 | xargs -0 $(RM)
	$(FIND) . -name '__pycache__' -prune -print0 | xargs -0 $(RM) -r
.PHONY: clean-pyc
clean: clean-doc clean-pyc
.PHONY: clean

pep8:
	@$(FIND) . -name '*.py' -print0 | xargs -0 $(PEP8)
pycodestyle:
	@$(FIND) . -name '*.py' -print0 | xargs -0 $(PYCODESTYLE)
pyflakes:
	@$(FIND) . -name '*.py' -print0 | xargs -0 $(PYFLAKES)
.PHONY: pep8 pyflakes
