from commandlib import CommandPath, Command
from path import Path
from copy import copy
import hitchbuild


class PyenvBuild(hitchbuild.HitchBuild):
    def __init__(self, version):
        self.version = version
    
    @property
    def basepath(self):
        return self.build_path.joinpath("python{0}".format(self.version))
    
    @property
    def bin(self):
        return CommandPath(self.basepath/"bin")
    
    def trigger(self):
        return self.monitor.non_existent(self.basepath)

    def build(self):
        if self.basepath.exists():
            self.basepath.rmtree(ignore_errors=True)
        self.basepath.mkdir()
        
        Command(
            Path(__file__).dirname().abspath().joinpath("bin", "python-build")
        )(self.version, self.basepath).run()

        self.bin.easy_install("--upgrade", "setuptools").run()
        self.bin.easy_install("--upgrade", "pip").run()
        self.bin.pip("install", "virtualenv", "--upgrade").without_env("PIP_REQUIRE_VIRTUALENV").run()
        self.verify()
    
    def verify(self):
        assert self.version in self.bin.python("--version").output()


class VirtualenvBuild(hitchbuild.HitchBuild):
    def __init__(self, base_python, name=None):
        self.base_python = self.as_dependency(base_python)
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def bin(self):
        return CommandPath(self.basepath.joinpath("bin"))

    @property
    def basepath(self):
        return self.build_path.joinpath(self.name)

    def trigger(self):
        return self.monitor.non_existent(self.basepath)

    def build(self):
        if self.basepath.exists():
            self.basepath.rmtree(ignore_errors=True)
        self.basepath.mkdir()
        self.base_python.bin.virtualenv(self.basepath).run()
        self.verify()

    def verify(self):
        assert self.base_python.version in self.bin.python(
            "-c", "import sys ; sys.stdout.write(sys.version)"
        ).output()
        

__version__ = "DEVELOPMENT_VERSION"
