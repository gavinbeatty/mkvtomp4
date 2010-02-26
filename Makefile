prefix=/usr/local
TMPDIR=/tmp

RM = rm -f
A2X = a2x
ASCIIDOC = asciidoc
INSTALL = install
SED = sed
RSYNC = rsync

default: all
.PHONY: all

PROJECT = mkvtomp4
include gen-version.mk
include dist.mk
include man2txt.mk

all: bin doc
bin: setup.py $(PROJECT)
doc: doc/$(PROJECT).1 doc/$(PROJECT).1.html doc/$(PROJECT).txt
clean: clean-bin clean-doc
.PHONY: all bin doc clean

$(PROJECT): $(PROJECT).py $(VERSION_DEP)
	$(SED) -e "s/^# @VERSION@/__version__ = '$(VERSION)'/" \
	$(PROJECT).py > $(PROJECT)
	@chmod +x $(PROJECT)
setup.py: setup.py.in
	$(SED) -e "s/^# @VERSION@/      version='$(VERSION)',/" setup.py.in \
	> setup.py
clean-bin:
	$(RM) $(PROJECT) setup.py
install-bin:
	@echo 'make install-doc to install documentation.'
	@echo 'To install the script, see README.markdown.'
install: install-bin
.PHONY: clean-bin install install-bin

doc/$(PROJECT).1: doc/$(PROJECT).1.txt
	$(A2X) -f manpage -L doc/$(PROJECT).1.txt
doc/$(PROJECT).1.html: doc/$(PROJECT).1.txt
	$(ASCIIDOC) doc/$(PROJECT).1.txt
doc/$(PROJECT).txt: doc/$(PROJECT).1
	$(call man2txt,doc/$(PROJECT).1,doc/$(PROJECT).txt)
clean-doc:
	$(RM) doc/$(PROJECT).1 doc/$(PROJECT).1.html doc/$(PROJECT).txt
install-doc: doc/$(PROJECT).1 doc/$(PROJECT).1.html
	$(INSTALL) -d -m 0755 $(DESTDIR)$(prefix)/share/man/man1
	$(INSTALL) -m 0644 doc/$(PROJECT).1 $(DESTDIR)$(prefix)/share/man/man1
	$(INSTALL) -m 0644 doc/$(PROJECT).1.html $(DESTDIR)$(prefix)/share/man/man1
	$(INSTALL) -d -m 0755 $(DESTDIR)$(prefix)/share/doc/$(PROJECT)
	$(INSTALL) -m 0644 README.markdown $(DESTDIR)$(prefix)/share/doc/$(PROJECT)
	$(INSTALL) -m 0644 LICENSE $(DESTDIR)$(prefix)/share/doc/$(PROJECT)
easy_install_doc: doc/$(PROJECT).1 doc/$(PROJECT).1.html doc/$(PROJECT).1.txt
	@$(RM) $(DISTNAME)-doc.zip
	@mkdir -p $(DISTNAME)-doc
	@$(INSTALL) -m 0644 doc/$(PROJECT).1.html $(DISTNAME)-doc/index.html
	$(ZIP) $(DISTNAME)-doc.zip $(DISTNAME)-doc/index.html >/dev/null
	@$(RM) -r $(DISTNAME)-doc
.PHONY: clean-doc install-doc easy_install_doc

upload-html: doc/$(PROJECT).1.html
	$(RSYNC) -av --chmod u=rw,g=r,o=r doc/$(PROJECT).1.html stokes:~/www/
.PHONY: upload-html

