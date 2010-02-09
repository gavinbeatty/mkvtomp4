prefix=/usr/local
TMPDIR=/tmp
version=1.1a
srcdir=$(abspath .)

all: doc

doc/mkvtomp4.1: doc/mkvtomp4.1.txt
	a2x -f manpage -L doc/mkvtomp4.1.txt

doc/mkvtomp4.1.html: doc/mkvtomp4.1.txt
	asciidoc doc/mkvtomp4.1.txt

doc: doc/mkvtomp4.1 doc/mkvtomp4.1.html

clean:
	rm -f doc/mkvtomp4.1 doc/mkvtomp4.1.html

install-docs: doc/mkvtomp4.1 doc/mkvtomp4.1.html
	install -d -m 0755 $(DESTDIR)$(prefix)/share/man/man1
	install -m 0644 doc/mkvtomp4.1 $(DESTDIR)$(prefix)/share/man/man1/
	install -m 0644 doc/mkvtomp4.1.html $(DESTDIR)$(prefix)/share/man/man1/

install-doc: install-docs

easy_install_doc: doc/mkvtomp4.1 doc/mkvtomp4.1.html doc/mkvtomp4.1.txt
	rm -f mkvtomp4-$(version)-doc.zip
	install -d -m 0755 $(TMPDIR)/mkvtomp4-$(version)-doc
	install -m 0644 doc/mkvtomp4.1.html $(TMPDIR)/mkvtomp4-$(version)-doc/index.html
	(cd $(TMPDIR)/mkvtomp4-$(version)-doc ; \
	7za a -tzip -mx9 $(srcdir)/mkvtomp4-$(version)-doc.zip index.html ; )
	rm -r $(TMPDIR)/mkvtomp4-$(version)-doc

upload-html: doc/mkvtomp4.1.html
	rsync -av --chmod u=rw,g=r,o=r doc/mkvtomp4.1.html stokes:~/www/

