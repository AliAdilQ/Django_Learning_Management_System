# Contributing

Contributions are welcome. Keep changes focused and explain the behavior they improve.

1. Fork the repository and create a branch for your change.
2. Follow the setup steps in the README and install `requirements-dev.txt`.
3. Run `python manage.py migrate` and `python manage.py seed_data` for local sample content.
4. Make your change. If a model changes, generate and commit its migration.
5. Add meaningful tests for changed workflows or permission boundaries.
6. Run the checks below before opening a pull request.

```bash
ruff check .
ruff format --check .
djlint templates --check --quiet
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Use named URLs, Django forms, ORM queries, and the shared template includes. Retrieve instructor-owned objects through a scoped query, and check student enrollment before showing protected learning activities. Never accept a role, course owner, score, or grade from a public student form.

For interface changes, inspect desktop, tablet, and mobile layouts. The optional Playwright workflow in the README refreshes real screenshots. Avoid committing databases, uploaded files, secrets, virtual environments, or generated test output.

In your pull request, describe the user-facing change, the reason for it, and how it was verified. Report security-sensitive issues privately using the guidance in [SECURITY.md](SECURITY.md).
