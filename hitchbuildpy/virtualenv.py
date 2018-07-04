from commandlib import CommandPath
from pathquery import pathquery
from path import Path
from copy import copy
import hitchbuild


class VirtualenvBuild(hitchbuild.HitchBuild):
    def __init__(self, base_python, name=None):
        self.base_python = self.as_dependency(base_python)
        self._name = name
        self._requirementstxt = None
        self._packages = None
        self._package_monitor = None

    @property
    def name(self):
        return self._name

    @property
    def bin(self):
        return CommandPath(self.basepath.joinpath("bin"))

    @property
    def basepath(self):
        return self.build_path.joinpath(self.name)

    def with_packages(self, *packages):
        new_venv = copy(self)
        # TODO: Prevent accidental use of self instead of new_venv
        new_venv._package_monitor = new_venv.monitored_vars(packages=packages)
        new_venv._packages = packages
        return new_venv

    def with_requirementstxt(self, *paths):
        new_venv = copy(self)
        # TODO: Prevent accidental use of self instead of new_venv
        new_venv._requirementstxt = new_venv.from_source(
            "requirementstxt",
            [Path(path).abspath() for path in paths]
        )
        new_venv._reqstxt = [Path(path).abspath() for path in paths]
        return new_venv

    def clean(self):
        if self.basepath.exists():
            self.basepath.rmtree(ignore_errors=True)

    def fingerprint(self):
        if hasattr(self, '_packages'):
            packages = self._packages if self._packages is not None else []
        else:
            packages = []
        if hasattr(self, '_reqstxt'):
            reqstxt = self._reqstxt if self._reqstxt is not None else []
        else:
            reqstxt = []
        return {"packages": packages, "reqstxt": reqstxt}

    @property
    def requirements_changed(self):
        if self._requirementstxt is not None:
            if self._requirementstxt.changes:
                return True
        if self._package_monitor is not None:
            if self._package_monitor.changes:
                return True
        else:
            return False

    def build(self):
        if self.last_run_had_exception:
            self.basepath.rmtree(ignore_errors=True)

        if not self.basepath.exists():
            self.basepath.mkdir()
            self.base_python.bin.virtualenv(self.basepath).run()
            self.verify()

        if self.requirements_changed:
            if self._requirementstxt is not None:
                for requirementstxt in self._reqstxt:
                    self.bin.pip("install", "-r", requirementstxt).run()
            if self._packages is not None:
                for package in self._packages:
                    self.bin.pip("install", package).run()

    def verify(self):
        assert self.base_python.version.replace("-dev", "") in self.bin.python(
            "-c", "import sys ; sys.stdout.write(sys.version)"
        ).output()


class PyLibrary(VirtualenvBuild):
    def __init__(self, name, base_python, module_name, library_src):
        self.base_python = self.as_dependency(base_python)
        self._module_name = module_name
        self._library_src_path = Path(library_src).abspath()
        self._library_src = self.from_source(
            "library",
            list(pathquery(self._library_src_path.joinpath(module_name))) +
            [self._library_src_path.joinpath("setup.py"), ]
        )
        self._name = name
        self._packages = []
        self._requirementstxt = None
        self._package_monitor = None

    def build(self):
        super(PyLibrary, self).build()
        if self._library_src.changes:
            self.bin.pip("uninstall", "-y", self._module_name).ignore_errors().run()
            self.bin.pip("install", ".").in_dir(self._library_src_path).run()
