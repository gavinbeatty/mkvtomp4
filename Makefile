prefix=/usr/local

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

