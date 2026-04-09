BLUE   := \033[36m
YELLOW := \033[33m
END    := \033[0m
TARGETLEN := 20

## Symlink Targets
symlinks: ## Symlink all Claude configuration into ~/.claude/
	@bash scripts/symlink-claude.sh
.PHONY: symlinks

## Hook Targets
hooks: ## Install git pre-commit hooks (requires: brew install gitleaks)
	@bash scripts/setup-hooks.sh
.PHONY: hooks

## All
all: symlinks hooks ## Run all setup targets
.PHONY: all

## General
help: ## Show this help message
	@awk 'BEGIN     { FS = ":.*##"; target="";printf "\nUsage:\n  make $(BLUE)<target>\033[33m\n\nTargets:$(END)\n" } \
		/^[.a-zA-Z_0-9-]+:.*?##/ { target=$$1; printf "  $(BLUE)%-$(TARGETLEN)s$(END) %s\n", $$1, $$2 } \
		/^([.a-zA-Z_0-9-]+):/ { match($$0, "(.*):"); target=substr($$0,RSTART,RLENGTH) } \
		/^\t## (.*)/ { match($$0, "[^\t#:\\\\]+"); txt=substr($$0,RSTART,RLENGTH); printf "  $(BLUE)%-$(TARGETLEN)s$(END) %s\n", target, txt; target="" } \
		/^## (.*)/ { match($$0, "[^\t#\\\\]+"); txt=substr($$0,RSTART,RLENGTH); printf "\n$(YELLOW)%-$(TARGETLEN)s$(END)\n", txt; target="" } \
	' $(MAKEFILE_LIST)

.DEFAULT_GOAL := help
