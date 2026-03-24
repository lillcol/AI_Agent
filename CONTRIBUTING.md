# Contributing Guide

This repository is a learning-first scaffold for AI Agent development.
Please keep all contributions minimal, modular, and easy to evolve.

## Core Principles

- Keep architecture clean: avoid coupling core modules to specific frameworks.
- Add small, focused changes: one concept per pull request.
- Prefer abstractions first: interface/protocol before concrete implementation.
- Avoid business-specific logic: this repo is for generic learning patterns.

## Project Conventions

- Source code lives under `src/ai_agent/`.
- Configuration stays centralized in `src/ai_agent/config/`.
- Shared helpers belong in `src/ai_agent/utils/`.
- Framework-specific code goes to `src/ai_agent/frameworks/`.
- Keep dependencies minimal and record them in `requirements.txt`.

## Coding Style

- Follow rules defined in `pyproject.toml` and `.editorconfig`.
- Use clear module names with single responsibility.
- Add concise comments only where logic is not self-explanatory.

## Commit Guidelines

- Use short, meaningful commit messages focused on intent.
- Keep commits atomic and easy to review.
- Avoid mixing refactor + feature + docs in one commit.

## Pull Request Checklist

- Architecture remains modular and expandable.
- No secrets are committed (`.env`, keys, tokens).
- README is updated when structure or workflow changes.
- New files are placed in the correct layer.

## Scope Reminder

Do not add concrete production agents directly.
Prefer building reusable foundations for:

- LLM wrappers
- tool protocols and execution
- memory modules
- RAG pipeline components
- orchestration patterns
