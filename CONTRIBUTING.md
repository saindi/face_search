# Contributing to Face Search

Thanks for your interest in contributing! Contributions of all kinds are
welcome — bug reports, feature requests, documentation and code.

## Reporting issues

- Search [existing issues](https://github.com/saindi/face_search/issues)
  before opening a new one.
- Include steps to reproduce, expected vs. actual behaviour, and your
  environment (OS, Python version, how you run the project — local or Docker).

## Development setup

1. Fork and clone the repository.
2. Create a `.env.dev` file (see [`.env.example`](.env.example)).
3. Install dependencies: `pip install -r requirements.txt`
   (note: `dlib` requires CMake and a C++ toolchain).
4. Apply migrations: `python manage.py migrate`
5. Run the development server: `python manage.py runserver`

## Making changes

- Create a feature branch off `master`:
  `git checkout -b feature/my-change`.
- Keep changes focused; one logical change per pull request.
- Follow the existing code style (PEP 8, descriptive names, docstrings on
  public classes and methods).
- Add or update tests for any behaviour you change.

## Running tests

```shell
python manage.py test
```

All tests must pass and CI must be green before a pull request is merged.

## Submitting a pull request

1. Push your branch and open a pull request against `master`.
2. Describe **what** changed and **why**.
3. Make sure the CI workflow passes.

## Code of conduct

Please be respectful and constructive in all interactions. This project
deals with biometric and personal data — only contribute features and use
the software in ways that are lawful and respect people's privacy.
