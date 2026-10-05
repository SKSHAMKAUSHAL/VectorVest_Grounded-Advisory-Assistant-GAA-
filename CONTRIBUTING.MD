# Contributing to Grounded Advisory Assistant

Thank you for contributing to the Grounded Advisory Assistant (GAA) project.

This guide provides a simple workflow for making changes safely and consistently.

## 1. Before You Start

Before working on an issue or feature:

1. Read the main `README.md`.
2. Review the relevant documentation under `docs/`.
3. Check existing issues and pull requests.
4. Avoid duplicating work already in progress.

## 2. Repository Structure

The project is divided into several major areas:

- `backend/` — FastAPI backend and application services
- `frontend/` — Next.js frontend
- `docs/` — Architecture, security, testing, and deployment documentation
- `prompts/` — System prompts used by the application
- `backend/tests/` — Backend test suite
- `frontend/src/__tests__/` — Frontend unit tests
- `frontend/e2e/` — End-to-end tests
- `.github/workflows/` — CI workflows

## 3. Branching

Create a separate branch for each change.

Recommended naming:

```text
feature/<short-description>
fix/<short-description>
docs/<short-description>
test/<short-description>
chore/<short-description>