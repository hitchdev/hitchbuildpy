from commandlib import run, Command
import hitchpython
from hitchstory import StoryCollection, StorySchema, BaseEngine, expected_exception, validate, HitchStoryException
from hitchrun import expected
from strictyaml import Str, Map, MapPattern, Optional, Float
from pathquery import pathq
import hitchtest
import hitchdoc
from commandlib import python
from hitchrun import hitch_maintenance
from hitchrun import DIR
from hitchrunpy import ExamplePythonCode, ExpectedExceptionMessageWasDifferent
from templex import Templex, NonMatching


class Engine(BaseEngine):
    """Python engine for running tests."""

    schema = StorySchema(
        given={
            Optional("runner python version"): Str(),
            Optional("working python version"): Str(),
            Optional("setup"): Str(),
            Optional("code"): Str(),
            Optional("files"): MapPattern(Str(), Str()),
        },
    )

    def __init__(self, paths, settings):
        self.path = paths
        self.settings = settings

    def set_up(self):
        """Set up your applications and the test environment."""
        self.path.state = self.path.gen.joinpath("state")
        self.path.working_dir = self.path.gen.joinpath("working")

        if self.path.state.exists():
            self.path.state.rmtree(ignore_errors=True)
        self.path.state.mkdir()
        
        for filename, contents in self.given.get('files', {}).items():
            self.path.state.joinpath(filename).write_text(contents)

        if self.path.working_dir.exists():
            self.path.working_dir.rmtree(ignore_errors=True)
        self.path.working_dir.mkdir()

        self.python_package = hitchpython.PythonPackage(
            self.given.get('python_version', '3.5.0')
        )
        self.python_package.build()

        self.pip = self.python_package.cmd.pip
        self.python = self.python_package.cmd.python

        # Install debugging packages
        with hitchtest.monitor([self.path.key.joinpath("debugrequirements.txt")]) as changed:
            if changed:
                run(self.pip("install", "-r", "debugrequirements.txt").in_dir(self.path.key))

        # Uninstall and reinstall
        with hitchtest.monitor(pathq(self.path.project.joinpath("hitchbuildpy"))) as changed:
            if changed:
                self.pip("uninstall", "hitchbuildpy", "-y").ignore_errors().run()
                self.pip("install", ".").in_dir(self.path.project).run()

        self.example_python_code = ExamplePythonCode(
            self.given.get('code', '')
        ).with_setup_code(
            self.given.get('setup')
        )

    def run_code(self):
        self.result = self.example_python_code.run(self.path.state, self.python)

    @expected_exception(NonMatching)
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

    #def on_success(self):
        #if self.settings.get("rewrite"):
            #self.new_story.save()


@expected(HitchStoryException)
def bdd(*words):
    """
    Run story with words.
    """
    StoryCollection(
        pathq(DIR.key).ext("story"), Engine(DIR, {"rewrite": True})
    ).shortcut(*words).play()


@expected(HitchStoryException)
def testfile(filename):
    """
    Run all stories in filename 'filename'.
    """
    StoryCollection(
        pathq(DIR.key).ext("story"), Engine(DIR, {"rewrite": True})
    ).in_filename(filename).ordered_by_name().play()


def regression():
    """
    Regression test - run all tests and linter.
    """
    lint()
    results = StoryCollection(
        pathq(DIR.key).ext("story"), Engine(DIR, {})
    ).ordered_by_name().play()
    print(results.report())


def rewriteall():
    """
    Run regression tests with story rewriting on.
    """
    print(
        StoryCollection(
            pathq(DIR.key).ext("story"), Engine(DIR, {"rewrite": True})
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


def hitch(*args):
    """
    Use 'h hitch --help' to get help on these commands.
    """
    hitch_maintenance(*args)


def deploy(version):
    """
    Deploy to pypi as specified version.
    """
    NAME = "hitchbuildpy"
    git = Command("git").in_dir(DIR.project)
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
