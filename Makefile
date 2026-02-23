## Generate Targets
generate: generate-agent-files ## Run all generate targets
.PHONY: generate

generate-agent-files: ## Build merged AI agent instruction files
	@bash scripts/generate-agent-files.sh
.PHONY: generate-agent-files

## Symlink Targets
symlinks: symlink-agents symlink-skills symlink-subagents symlink-commands ## Run all symlink configuration targets
.PHONY: symlinks

symlink-agents: ## Create symlinks for AI agent configuration files
	@bash scripts/symlink-agents.sh
.PHONY: symlink-agents

symlink-skills: ## Create symlinks for AI skills configuration files
	@bash scripts/symlink-skills.sh
.PHONY: symlink-skills

symlink-subagents: ## Create symlinks for AI subagents configuration files
	@bash scripts/symlink-subagents.sh
.PHONY: symlink-subagents

symlink-commands: ## Create symlinks for AI commands configuration files
	@bash scripts/symlink-commands.sh
.PHONY: symlink-commands

## General

all: generate symlinks ## Runs all target groups (generate and symlinks)
.PHONY: all

help: ## Shows this help message
	@awk 'BEGIN     { FS = ":.*##"; target="";printf "\nUsage:\n  make $(BLUE)<target>\033[33m\n\nTargets:$(END)\n" } \
		/^[.a-zA-Z_0-9-]+:.*?##/ { target=$$1; printf "  $(BLUE)%-$(TARGETLEN)s$(END) %s\n", $$1, $$2 } \
		/^([.a-zA-Z_0-9-]+):/ { match($$0, "(.*):"); target=substr($$0,RSTART,RLENGTH) } \
		/^\t## (.*)/ { match($$0, "[^\t#:\\\\]+"); txt=substr($$0,RSTART,RLENGTH); printf "  $(BLUE)%-$(TARGETLEN)s$(END) %s\n", target, txt; target="" } \
		/^## (.*)/ { match($$0, "[^\t#\\\\]+"); txt=substr($$0,RSTART,RLENGTH); printf "\n$(YELLOW)%-$(TARGETLEN)s$(END)\n", txt; target="" } \
	' $(MAKEFILE_LIST)
	@# https://gist.github.com/gfranxman/73b5dc6369dc684db6848198290330c7#file-makefile 05/09/2024


.DEFAULT_GOAL := help
