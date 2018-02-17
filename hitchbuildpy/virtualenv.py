from commandlib import CommandPath
from copy import copy
import hitchbuild


class VirtualenvBuild(hitchbuild.HitchBuild):
    def __init__(self, base_python, name=None):
        self.base_python = self.as_dependency(base_python)
        self._name = name
        self._requirementstxt = None
        self._packages = None

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
        trig = self.monitor.non_existent(self.basepath)
        if self._requirementstxt is not None:
            trig = trig | self.monitor.is_modified(self._requirementstxt)
        return trig

    def with_packages(self, *packages):
        new_venv = copy(self)
        new_venv._packages = packages
        return new_venv

    def with_requirementstxt(self, *paths):
        new_venv = copy(self)
        new_venv._requirementstxt = paths
        return new_venv

    def clean(self):
        if self.basepath.exists():
            self.basepath.rmtree(ignore_errors=True)

    def build(self):
        self.clean()
        self.basepath.mkdir()
        self.base_python.bin.virtualenv(self.basepath).run()
        self.verify()

        if self._requirementstxt is not None:
            for requirementstxt in self._requirementstxt:
                self.bin.pip("install", "-r", requirementstxt).run()
        if self._packages is not None:
            for package in self._packages:
                self.bin.pip("install", package).run()

    def verify(self):
        assert self.base_python.version in self.bin.python(
            "-c", "import sys ; sys.stdout.write(sys.version)"
        ).output()


class PyLibrary(VirtualenvBuild):
    def __init__(self, base_python, module_name, library_src):
        self.base_python = self.as_dependency(base_python)
        self._module_name = module_name
        self._library_src = library_src
        self._name = module_name
        self._packages = []
        self._requirementstxt = []

    def trigger(self):
        trig = self.monitor.non_existent(self.basepath)
        return trig

    def build(self):
        if not self.basepath.exists():
            self.basepath.mkdir()
            self.base_python.bin.virtualenv(self.basepath).run()
            self.verify()

        if self._requirementstxt is not None:
            if self.last_run.path_changes is None or any(
                reqstxt for reqstxt in self._requirementstxt
                if reqstxt in self.last_run.path_changes
            ):
                for requirementstxt in self._requirementstxt:
                    self.bin.pip("install", "-r", requirementstxt).run()
        if self._packages is not None:
            for package in self._packages:
                self.bin.pip("install", package).run()
        self.bin.pip("uninstall", "-y", self._module_name).ignore_errors().run()
        self.bin.pip("install", ".").in_dir(self._library_src).run()
