"""
Nox sessions for Tesla-level reproducible local CI on any OS.
Run any session with: nox -s <session>
Run the full gate with: nox
"""

import nox

nox.options.sessions = ["lint", "typecheck", "security", "tests", "frontend"]


@nox.session(python=["3.12"])
def ci(session: nox.Session) -> None:
    """Backend-only CI gate (no Node dependency)."""
    session.notify("lint")
    session.notify("typecheck")
    session.notify("security")
    session.notify("tests")


@nox.session(python=["3.12"])
def lint(session: nox.Session) -> None:
    """Run ruff on all Python sources."""
    session.install("ruff")
    session.run("ruff", "check", "src/", "app.py", "tests/", "noxfile.py")


@nox.session(python=["3.12"])
def typecheck(session: nox.Session) -> None:
    """Run mypy on the source package."""
    session.install("-r", "requirements.txt")
    session.run("mypy", "src/")


@nox.session(python=["3.12"])
def security(session: nox.Session) -> None:
    """Run bandit, pip-audit, and detect-secrets."""
    session.install("bandit", "pip-audit", "detect-secrets")
    session.run("bandit", "-r", "src/", "-ll", "-ii")
    session.run("pip-audit", "--requirement", "requirements.txt")
    session.run("detect-secrets", "scan", "--baseline", ".secrets.baseline")


@nox.session(python=["3.12"])
def tests(session: nox.Session) -> None:
    """Run the test suite with pytest-cov."""
    session.install("-r", "requirements.txt")
    session.run(
        "pytest", "tests/", "-q", "--cov=src", "--cov-report=term", "--cov-fail-under=90"
    )


@nox.session(python=["3.12"])
def mutation(session: nox.Session) -> None:
    """Run mutation testing with mutmut."""
    session.install("-r", "requirements.txt")
    session.run("mutmut", "run", "--paths-to-mutate", "src/", "--runner", "python -m pytest tests/ -q")


@nox.session
def frontend(session: nox.Session) -> None:
    """Typecheck and build the frontend."""
    session.run("npm", "ci", external=True, cwd="frontend")
    session.run("npx", "tsc", "--noEmit", external=True, cwd="frontend")
    session.run("npm", "run", "build", external=True, cwd="frontend")


@nox.session(python=["3.12"])
def docker(session: nox.Session) -> None:
    """Build Docker images."""
    session.run("docker", "compose", "build", external=True)
