ifndef GIT
GIT = git
endif
ifndef ZIP
ZIP = zip
endif
ifndef BZIP2
BZIP2 = bzip2
endif
ifndef TAR
TAR = tar
endif
ifndef RM
RM = rm -f
endif
ifndef PROJECT_VERSION_VAR
PROJECT_VERSION_VAR = VERSION
endif
ifndef PROJECT_VERSION_FILE
PROJECT_VERSION_FILE = VERSION
endif
ifndef PROJECT
$(error "Must define PROJECT for use with dist.mk")
endif
ifndef DISTNAME
DISTNAME = $(PROJECT)-$($(PROJECT_VERSION_VAR))
endif

VERSION_ = $($(PROJECT_VERSION_VAR))
dist: all $(PROJECT_VERSION_FILE)
	@mkdir -p $(DISTNAME)
	@echo $(PROJECT_VERSION_VAR)=$(VERSION_) > $(DISTNAME)/release
	$(GIT) archive --format zip --prefix=$(DISTNAME)/ \
	HEAD^{tree} --output $(DISTNAME).zip
	@$(ZIP) -u $(DISTNAME).zip $(DISTNAME)/release >/dev/null
	$(GIT) archive --format tar --prefix=$(DISTNAME)/ \
	HEAD^{tree} --output $(DISTNAME).tar
	@$(TAR) rf $(DISTNAME).tar $(DISTNAME)/release
	@$(RM) -r $(DISTNAME)
	$(BZIP2) -9 $(DISTNAME).tar

