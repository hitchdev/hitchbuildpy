from commandlib import CommandPath, Command
from path import Path
from copy import copy
import hitchbuild


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
