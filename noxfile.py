"""
Nox sessions for Tesla-level reproducible local CI on any OS.
Run any session with: nox -s <session>
Run the full gate with: nox
"""

import nox

nox.options.sessions = ["lint", "typecheck", "security", "tests", "frontend"]


@nox.session(python=["3.12"])
def lint(session: nox.Session) -> None:
    """Run ruff on all Python sources."""
    session.install("ruff")
    session.run("ruff", "check", "src/", "app.py", "tests/")


@nox.session(python=["3.12"])
def typecheck(session: nox.Session) -> None:
    """Run mypy on the source package."""
    session.install("-r", "requirements.txt")
    session.run("mypy", "src/")


@nox.session(python=["3.12"])
def security(session: nox.Session) -> None:
    """Run bandit and pip-audit."""
    session.install("bandit", "pip-audit")
    session.run("bandit", "-r", "src/", "-ll", "-ii")
    session.run("pip-audit", "--requirement", "requirements.txt")


@nox.session(python=["3.12"])
def tests(session: nox.Session) -> None:
    """Run the test suite with pytest-cov."""
    session.install("-r", "requirements.txt")
    session.run(
        "pytest", "tests/", "-q", "--cov=src", "--cov-report=term", "--cov-fail-under=85"
    )


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
