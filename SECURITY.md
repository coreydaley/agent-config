# Security Policy

## Scope

This repository contains AI agent configuration files, skills, commands, and scripts. Security considerations include:

- Shell scripts that execute on your local machine
- AI agent instructions that influence agent behavior
- Symlinks created in your home directory

## Reporting a Vulnerability

If you discover a security issue — such as a script that could cause unintended file system modifications, an agent instruction that could be used to manipulate agent behavior maliciously, or any other vulnerability — please **do not open a public issue**.

Instead, report it privately by emailing the maintainer or using [GitHub's private vulnerability reporting](https://github.com/coreydaley/agent-config/security/advisories/new).

Please include:

- A description of the vulnerability
- Steps to reproduce or a proof-of-concept
- The potential impact
- Any suggested mitigations

You can expect an acknowledgment within 5 business days and a resolution or status update within 30 days.

## AI-Generated Content Warning

Content in this repository is likely generated using AI language models. Review all scripts and agent instructions before running them in sensitive environments. Never use agent configurations from this repository (or any source) in production AI systems without thorough review.

## Safe Usage Practices

- Review scripts in `scripts/` before executing them
- Inspect symlink targets before running `make symlinks`
- Do not store secrets or credentials in agent configuration files
- Treat agent instructions as code — review them before deploying
