from hitchstory import StoryCollection, BaseEngine
from hitchstory import no_stacktrace_for, validate, HitchStoryException
from hitchstory import GivenDefinition, GivenProperty, InfoDefinition, InfoProperty
from hitchrun import expected
from strictyaml import Str, MapPattern, Optional, Float
from pathquery import pathquery
from commandlib import run, Command
from commandlib import python
from hitchrun import hitch_maintenance
from hitchrun import DIR
from hitchrunpy import ExamplePythonCode, ExpectedExceptionMessageWasDifferent
from templex import Templex
import hitchpylibrarytoolkit


git = Command("git").in_dir(DIR.project)


class Engine(BaseEngine):
    """Python engine for running tests."""
    given_definition = GivenDefinition(
        setup=GivenProperty(Str()),
        code=GivenProperty(Str()),
        files=GivenProperty(MapPattern(Str(), Str())),
        pyenv_version=GivenProperty(Str())
    )

    def __init__(self, paths, settings):
        self.path = paths
        self.settings = settings

    def set_up(self):
        """Set up your applications and the test environment."""
        self.path.cachestate = self.path.gen.joinpath("cachestate")
        self.path.state = self.path.gen.joinpath("state")
        self.path.working_dir = self.path.gen.joinpath("working")
        self.path.build_path = self.path.gen.joinpath("build_path")

        if self.path.state.exists():
            self.path.state.rmtree(ignore_errors=True)
        self.path.state.mkdir()

        if self.path.build_path.exists():
            self.path.build_path.rmtree(ignore_errors=True)
        self.path.build_path.mkdir()

        if not self.path.cachestate.exists():
            self.path.cachestate.mkdir()

        for filename, contents in self.given.get('files', {}).items():
            filepath = self.path.state.joinpath(filename)
            if not filepath.dirname().exists():
                filepath.dirname().makedirs()
            filepath.write_text(contents)

        if self.path.working_dir.exists():
            self.path.working_dir.rmtree(ignore_errors=True)
        self.path.working_dir.mkdir()

        self.python = hitchpylibrarytoolkit.project_build(
            "hitchbuildpy",
            self.path,
            "3.5.0",
        ).bin.python

        self.example_py_code = ExamplePythonCode(self.python, self.path.state)\
            .with_setup_code(self.given.get('setup', ''))\
            .with_terminal_size(160, 100)\
            .with_long_strings(
                pyenv_version=self.given.get("pyenv_version"),
                share=str(self.path.cachestate),
                build_path=str(self.path.build_path),
            )

    def run(self, code):
        self.example_py_code.with_code(code).run()

    @no_stacktrace_for(AssertionError)
    def output_ends_with(self, contents):
        Templex(contents).assert_match(self.result.output.split('\n')[-1])

    def write_file(self, filename, contents):
        self.path.state.joinpath(filename).write_text(contents)

    def raises_exception(self, message=None, exception_type=None):
        try:
            result = self.example_python_code.expect_exceptions().run(self.path.state, self.python)
            result.exception_was_raised(exception_type, message.strip())
        except ExpectedExceptionMessageWasDifferent as error:
            if self.settings.get("rewrite"):
                self.current_step.update(message=error.actual_message)
            else:
                raise

    def file_contains(self, filename, contents):
        assert self.path.working_dir.joinpath(filename).bytes().decode('utf8') == contents

    @validate(duration=Float())
    def sleep(self, duration):
        import time
        time.sleep(duration)

    def pause(self, message="Pause"):
        import IPython
        IPython.embed()


@expected(HitchStoryException)
def bdd(*words):
    """
    Run story with words.
    """
    StoryCollection(
        pathquery(DIR.key).ext("story"), Engine(DIR, {"rewrite": True})
    ).shortcut(*words).play()


@expected(HitchStoryException)
def testfile(filename):
    """
    Run all stories in filename 'filename'.
    """
    StoryCollection(
        pathquery(DIR.key).ext("story"), Engine(DIR, {"rewrite": True})
    ).in_filename(filename).ordered_by_name().play()


def regression():
    """
    Regression test - run all tests and linter.
    """
    lint()
    results = StoryCollection(
        pathquery(DIR.key).ext("story"), Engine(DIR, {})
    ).ordered_by_name().play()
    print(results.report())


def rewriteall():
    """
    Run regression tests with story rewriting on.
    """
    print(
        StoryCollection(
            pathquery(DIR.key).ext("story"), Engine(DIR, {"rewrite": True})
        ).ordered_by_name().play().report()
    )


def lint():
    """
    Lint all code.
    """
    python("-m", "flake8")(
        DIR.project.joinpath("hitchbuildpy"),
        "--max-line-length=100",
        "--exclude=__init__.py",
    ).run()
    python("-m", "flake8")(
        DIR.key.joinpath("key.py"),
        "--max-line-length=100",
        "--exclude=__init__.py",
    ).run()
    print("Lint success!")


def cleancache():
    """
    Clean the cache state.
    """
    DIR.gen.joinpath("cachestate").rmtree(ignore_errors=True)
    print("Done")


def hitch(*args):
    """
    Use 'h hitch --help' to get help on these commands.
    """
    hitch_maintenance(*args)


def rerun(version="3.5.0"):
    """
    Rerun last example code block with specified version of python.
    """
    Command(DIR.gen.joinpath("py{0}".format(version), "bin", "python"))(
        DIR.gen.joinpath("state", "examplepythoncode.py")
    ).in_dir(DIR.gen.joinpath("state")).run()


def updatepyenv():
    """
    git clone pyenv and update.
    """
    print("Updating from git...")
    pyenv_dir = DIR.gen/"pyenv"

    if pyenv_dir.exists():
        git("pull").in_dir(pyenv_dir).run()
    else:
        git("clone", "https://github.com/pyenv/pyenv.git").in_dir(DIR.gen).run()

    print("Copying...")
    pybin = DIR.project/"hitchbuildpy"/"bin"
    pyshare = DIR.project/"hitchbuildpy"/"share"

    if pybin.exists():
        pybin.rmtree()
    pybin.mkdir()
    if pyshare.exists():
        pyshare.rmtree()

    py_build_dir = pyenv_dir/"plugins"/"python-build"
    py_build_dir.joinpath("bin", "python-build").copy(pybin/"python-build")
    py_build_dir.joinpath("share").copytree(pyshare)

    DIR.project.joinpath("hitchbuildpy", "pyenv-commit-hash").write_text(
        git("rev-parse", "HEAD").in_dir(pyenv_dir).output().rstrip()
    )


def deploy(version):
    """
    Deploy to pypi as specified version.
    """
    NAME = "hitchbuildpy"
    version_file = DIR.project.joinpath("VERSION")
    old_version = version_file.bytes().decode('utf8')
    if version_file.bytes().decode("utf8") != version:
        DIR.project.joinpath("VERSION").write_text(version)
        git("add", "VERSION").run()
        git("commit", "-m", "RELEASE: Version {0} -> {1}".format(
            old_version,
            version
        )).run()
        git("push").run()
        git("tag", "-a", version, "-m", "Version {0}".format(version)).run()
        git("push", "origin", version).run()
    else:
        git("push").run()

    # Set __version__ variable in __init__.py, build sdist and put it back
    initpy = DIR.project.joinpath(NAME, "__init__.py")
    original_initpy_contents = initpy.bytes().decode('utf8')
    initpy.write_text(
        original_initpy_contents.replace("DEVELOPMENT_VERSION", version)
    )
    python("setup.py", "sdist").in_dir(DIR.project).run()
    initpy.write_text(original_initpy_contents)

    # Upload to pypi
    python(
        "-m", "twine", "upload", "dist/{0}-{1}.tar.gz".format(NAME, version)
    ).in_dir(DIR.project).run()
