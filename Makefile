RM = rm -f
PANDOC = pandoc
FIND = find
PEP8 = pep8
PYCODESTYLE = pycodestyle
PYFLAKES = pyflakes
PYTHON = python3
TAR = bsdtar
RM = rm
MKDIR = mkdir

PROJECT = mkvtomp4
SOURCES = LICENSE README.md mkvtomp4.py setup.py simplemkv/tomp4.py simplemkv/info.py simplemkv/__init__.py simplemkv/version.py
PYZMAIN = simplemkv.tomp4:main
PYDIST = dist
PYZDIST = $(PYDIST)/pyz

default: doc pyz
.PHONY: default

simplemkv/version.py:
	$(PYTHON) -q setup.py check

doc: doc/$(PROJECT).1 doc/$(PROJECT).1.html doc/$(PROJECT).txt
.PHONY: doc

doc/$(PROJECT).1: doc/$(PROJECT).1.txt
	$(PANDOC) -s -w man -o $@ doc/$(PROJECT).1.txt
doc/$(PROJECT).1.html: doc/$(PROJECT).1.txt
	$(PANDOC) -s -w html -o $@ doc/$(PROJECT).1.txt
doc/$(PROJECT).txt: doc/$(PROJECT).1.txt
	$(PANDOC) -s -w plain -o $@ doc/$(PROJECT).1.txt
clean-doc:
	$(RM) doc/$(PROJECT).1 doc/$(PROJECT).1.html doc/$(PROJECT).txt
.PHONY: clean-doc
clean-pyc:
	$(FIND) . -name '*.pyc' -print0 | xargs -0 $(RM)
	$(FIND) . -name '__pycache__' -prune -print0 | xargs -0 $(RM) -r
.PHONY: clean-pyc
clean-dist:
	$(RM) -rf dist
.PHONY: clean-dist
clean-build:
	$(RM) -rf build
.PHONY: clean-build
clean-egg-info:
	$(RM) -rf $(PROJECT).egg-info
.PHONY: clean-egg-info
clean: clean-doc clean-pyc clean-dist clean-build clean-egg-info
.PHONY: clean

$(PYDIST)/$(PROJECT).pyz: $(SOURCES)
	@$(RM) -rf $(PYZDIST)
	$(PYTHON) -q setup.py sdist -d $(PYZDIST) --formats tar
	@$(MKDIR) -p $(PYZDIST)/untar
	$(TAR) -xf $(PYZDIST)/*.tar -C $(PYZDIST)/untar
	$(PYTHON) -m zipapp $(PYZDIST)/untar/*/ -m $(PYZMAIN) -o $@

pyz: $(PYDIST)/$(PROJECT).pyz
.PHONY: pyz

pep8:
	@$(FIND) . -name '*.py' -print0 | xargs -0 $(PEP8)
pycodestyle:
	@$(FIND) . -name '*.py' -print0 | xargs -0 $(PYCODESTYLE)
pyflakes:
	@$(FIND) . -name '*.py' -print0 | xargs -0 $(PYFLAKES)
.PHONY: pep8 pycodestyle pyflakes
