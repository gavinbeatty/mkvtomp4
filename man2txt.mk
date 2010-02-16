ifndef ROFF
ROFF = groff
endif
ifndef COL
COL = col
endif

man2txt = \
	$(ROFF) -t -e -P -c -mandoc -Tutf8 $(1) | $(COL) -bx > $(2)

