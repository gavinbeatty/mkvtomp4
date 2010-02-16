
ifndef GIT
GIT = git
endif
ifndef RM
RM = rm -f
endif
ifndef PROJECT_VERSION_VAR
PROJECT_VERSION_VAR = VERSION
endif
ifndef PROJECT_RELEASE_FILE
PROJECT_RELEASE_FILE = release
endif

-include $(PROJECT_RELEASE_FILE)
ifeq ($(strip $($(PROJECT_VERSION_VAR))),)
$(PROJECT_VERSION_VAR)_DEP=$(PROJECT_VERSION_VAR)
$(PROJECT_VERSION_VAR): gen-version.sh .git/$(shell $(GIT) symbolic-ref HEAD)
	@gen-version.sh $(PROJECT) $(PROJECT_VERSION_VAR) $(PROJECT_VERSION_VAR)
-include $(PROJECT_VERSION_VAR)
else
$(PROJECT_VERSION_VAR)_DEP=
endif
clean-version:
	$(RM) $(PROJECT_VERSION_VAR)
clean: clean-version

