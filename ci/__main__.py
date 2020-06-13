import click
import os
import subprocess
from subprocess import check_call


DEFAULT_PYTHON_VERSION = "3.6"
PYTHON_VERSIONS = ["3.6"]
PYFIBRE_REPO = os.path.abspath('.')

EDM_CORE_DEPS = [
    'Click==7.0-1',
    "chaco==4.8.0-2",
    "enable==4.8.1-1",
    "envisage==4.9.0-1",
    'pytables==3.5.1-1',
    'traits==5.2.0-1',
    'traitsui==6.1.3-4',
    "pyface==6.1.2-4",
    "pygments==2.2.0-1",
    "pyqt>=4.11.4-7",
    "qt>=4.8.7-10",
    "sip>=4.18.1-1",
    "pyzmq==16.0.0-7",
    "swig==3.0.11-2",
    "stevedore==1.29.0-7",
    "traits_futures==0.1.0-16"]

EDM_DEV_DEPS = ["flake8==3.7.7-1",
                "testfixtures==4.10.0-1",
                "coverage==4.3.4-1",
                "mock==2.0.0-3"]

with open('docs/requirements.txt', 'r') as infile:
    PIP_DOCS_DEPS = infile.readlines()


# We pin to a version of Traits Futures with updated GuiTestAssistant
PIP_DEPS = [
    "git+https://github.com/enthought/traits-futures.git"
    "@9f5973f330bcf5bf7d813439bb817c3e7eadd6ad"
]


def remove_dot(python_version):
    return "".join(python_version.split("."))


def get_env_name(python_version):
    return f"pyfibre-py{remove_dot(python_version)}"


def edm_run(env_name, command, cwd=None):
    return subprocess.call(
        ["edm", "run", "-e", env_name, "--"] + command, cwd=cwd)


@click.group()
def cli():
    pass


python_version_option = click.option(
    '--python-version',
    default=DEFAULT_PYTHON_VERSION,
    type=click.Choice(PYTHON_VERSIONS),
    show_default=True,
    help="Python version for environment"
)


@cli.command(
    name="build-env",
    help="Creates the edm execution environment"
)
@python_version_option
def build_env(python_version):
    env_name = get_env_name(python_version)

    check_call([
        "edm", "env", "remove", "--purge", "--force",
        "--yes", env_name]
    )
    check_call(
        ["edm", "env", "create", "--version",
         python_version, env_name]
    )

    check_call(
        ["edm", "install", "-e", env_name, "--yes"]
        + EDM_CORE_DEPS + EDM_DEV_DEPS
    )


@cli.command(
    name="install",
    help='Creates the execution binary inside the PyFibre environment'
)
@python_version_option
def install(python_version):

    env_name = get_env_name(python_version)

    edm_run(env_name, ['pip', 'install'] + PIP_DEPS + PIP_DOCS_DEPS)

    print('Installing PyFibre to edm environment')
    edm_run(env_name, ['pip', 'install', '-e', '.'])


@cli.command(help="Run flake")
@python_version_option
def flake8(python_version):
    env_name = get_env_name(python_version)

    returncode = edm_run(env_name, ["flake8", "."])
    if returncode:
        raise click.ClickException(
            "Flake8 exited with exit status {}".format(returncode)
        )


@cli.command(help="Runs the coverage")
@python_version_option
def coverage(python_version):
    env_name = get_env_name(python_version)

    returncode = edm_run(
        env_name, ["coverage", "run", "-m", "unittest", "discover"]
    )
    if returncode:
        raise click.ClickException("There were test failures.")

    edm_run(
        env_name, ["coverage", "report", "-m"]
    )

    if os.path.exists('.coverage'):
        os.remove('.coverage')


@cli.command(help="Builds the documentation")
@python_version_option
def docs(python_version):

    env_name = get_env_name(python_version)

    click.echo("Generating HTML")
    returncode = edm_run(env_name, ["make", "html"], cwd="docs")
    if returncode:
        raise click.ClickException(
            "There were errors while building HTML documentation."
        )


@cli.command(help="Run the unit tests")
@click.option(
    "--verbose/--quiet",
    default=True,
    help="Run tests in verbose mode? [default: --verbose]",
)
@python_version_option
def test(python_version, verbose):

    env_name = get_env_name(python_version)

    verbosity_args = ["--verbose"] if verbose else []

    returncode = edm_run(
        env_name, ["python", "-m", "unittest", "discover"] + verbosity_args
    )

    if returncode:
        raise click.ClickException("There were test failures.")


@cli.command(
    name="shell",
    help="Enters the edm deployment environment"
)
@python_version_option
def shell(python_version):
    env_name = get_env_name(python_version)

    check_call(["edm", "shell", "-e", env_name]
    )


if __name__ == "__main__":
    cli()
