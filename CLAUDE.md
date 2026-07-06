# southern-company-hacs — Claude Code Context

## Project Summary

HACS custom integration for Home Assistant that pulls utility data from Southern Company (Alabama Power, Georgia Power, Mississippi Power) and exposes it as HA sensor entities. Installs via HACS. Uses the `southern_company_api` Python library. Deployed to the ScheibTribe HA instance at 10.10.1.20.

## Environment

- **Host**: Ubuntu VM at 10.10.1.19 (dev); HA host at 10.10.1.20 (deployed)
- **Project root**: `~/projects/southern-company-hacs/`
- **Language**: Python
- **HA custom component**: `custom_components/southern_company/`
- **GitHub**: https://github.com/tempeduck/southern-company-hacs (public)

## Deployment

```bash
# Copy component to HA host
scp -r custom_components/southern_company root@10.10.1.20:/config/custom_components/
# Then restart HA or reload via Developer Tools
```

## Rules

- HA credentials are never stored in this repo — configured via HA UI
- Use `pre-commit` and `ruff` for linting before commits
- Test changes on the ScheibTribe HA instance before pushing
- Refer to `.devcontainer/` for the VS Code dev container setup

## Agent Collaboration Rules

- **Read History First**: At the start of every session, the agent MUST run `git status` and `git log -n 5` to understand recent changes, and read the `## Active Handoff` section in this file.
- **Commit with Context**: Every commit message must explain the *why* behind a change, not just the *what*.
- **The Handoff Journal**: Before concluding a session or completing a major task, the active agent MUST update the `## Active Handoff` section at the bottom of this file.
- **Interactive Dry Runs**: The agent must always perform a dry run and list planned changes for user approval before modifying code, databases, or configuration files.
- **Explicit Task Tracking**: Maintain a shared checklist of tasks in `task.md` or `CLAUDE.md`. Mark tasks as `[x]` for complete, `[/]` for in-progress, and `[ ]` for pending.

## Active Handoff

- [2026-06-06 (Claude Code)]: Added agent collaboration rules and initialized handoff log.
