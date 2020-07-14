from commandlib import CommandPath, Command
from distutils.version import LooseVersion
from path import Path
import hitchbuild


class PyenvBuild(hitchbuild.HitchBuild):
    def __init__(self, build_path, version):
        self.build_path = Path(build_path).abspath()
        self.version = version
        self.fingerprint_path = self.build_path / "fingerprint.txt"

    @property
    def bin(self):
        return CommandPath(self.build_path / "bin")

    def clean(self):
        self.build_path.rmtree(ignore_errors=True)

    def build(self):
        if self.incomplete():
            self.build_path.rmtree(ignore_errors=True)
            self.build_path.mkdir()

            Command(
                Path(__file__).dirname().abspath().joinpath("bin", "python-build")
            )(self.version, self.build_path).run()

            if LooseVersion(self.version) < LooseVersion("3.6.0"):
                self.bin.easy_install("--upgrade", "setuptools").run()
                self.bin.easy_install("--upgrade", "pip").run()
            else:
                self.bin.pip("install", "pip", "--upgrade").run()
            self.bin.pip("install", "virtualenv", "--upgrade")\
                    .without_env("PIP_REQUIRE_VIRTUALENV").run()
            self.verify()
            self.refingerprint()

    def verify(self):
        version_to_check = self.version.replace("-dev", "")
        assert version_to_check in self.bin.python("--version").output(), \
            "'{0}' expected to be found in python --version, got:\n{1}".format(
                self.version,
                self.bin.python("--version").output(),
            )
