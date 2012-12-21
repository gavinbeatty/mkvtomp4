TMPDIR=/tmp

RM = rm -f
A2X = a2x
ASCIIDOC = asciidoc
INSTALL = install

default: doc
.PHONY: default

PROJECT = mkvtomp4
include man2txt.mk

doc: doc/$(PROJECT).1 doc/$(PROJECT).1.html doc/$(PROJECT).txt
.PHONY: doc

doc/$(PROJECT).1: doc/$(PROJECT).1.txt
	$(A2X) -f manpage -L doc/$(PROJECT).1.txt
doc/$(PROJECT).1.html: doc/$(PROJECT).1.txt
	$(ASCIIDOC) doc/$(PROJECT).1.txt
doc/$(PROJECT).txt: doc/$(PROJECT).1
	$(call man2txt,doc/$(PROJECT).1,doc/$(PROJECT).txt)
clean:
	$(RM) doc/$(PROJECT).1 doc/$(PROJECT).1.html doc/$(PROJECT).txt
.PHONY: clean
#easy_install_doc: doc/$(PROJECT).1 doc/$(PROJECT).1.html doc/$(PROJECT).1.txt
#	@$(RM) $(DISTNAME)-doc.zip
#	@mkdir -p $(DISTNAME)-doc
#	@$(INSTALL) -m 0644 doc/$(PROJECT).1.html $(DISTNAME)-doc/index.html
#	$(ZIP) $(DISTNAME)-doc.zip $(DISTNAME)-doc/index.html >/dev/null
#	@$(RM) -r $(DISTNAME)-doc
#.PHONY: easy_install_doc

pep8:
	@find . -name '*.py' -print0 | xargs -0 pep8
pyflakes:
	@find . -name '*.py' -print0 | xargs -0 pyflakes
.PHONY: pep8 pyflakes
