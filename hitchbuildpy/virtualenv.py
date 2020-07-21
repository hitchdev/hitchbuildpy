from commandlib import CommandPath
from pathquery import pathquery
from path import Path
from copy import copy
import hitchbuild


class VirtualenvBuild(hitchbuild.HitchBuild):
    def __init__(self, build_path, base_python):
        self.build_path = Path(build_path).abspath()
        self.fingerprint_path = self.build_path / "fingerprint.txt"
        self.base_python = self.dependency(base_python)
        self._requirementstxt = None
        self._extra_packages = None

    @property
    def bin(self):
        return CommandPath(self.build_path / "bin")

    def with_packages(self, *packages):
        new_venv = copy(self)
        # TODO: Prevent accidental use of self instead of new_venv
        new_venv._extra_packages = new_venv.variable("extra_packages", list(packages))
        return new_venv

    def with_requirementstxt(self, *paths):
        new_venv = copy(self)
        # TODO: Prevent accidental use of self instead of new_venv
        new_venv._requirementstxt = new_venv.source(
            "requirementstxt",
            [Path(path).abspath() for path in paths]
        )
        return new_venv

    def clean(self):
        self.build_path.rmtree(ignore_errors=True)

    def build(self):
        if self.incomplete():
            self.build_path.rmtree(ignore_errors=True)
            self.build_path.mkdir()
            self.base_python.build.ensure_built()
            self.base_python.build.bin.virtualenv(self.build_path).run()

            if self._requirementstxt is not None:
                for filename in self._requirementstxt._filenames:
                    self.bin.pip("install", "-r", filename).run()

            if self._extra_packages is not None:
                for package in self._extra_packages.value:
                    self.bin.pip("install", package).run()

            self.verify()
            self.refingerprint()
        else:
            if self._requirementstxt is not None:
                if self._requirementstxt.changed:
                    for filename in self._requirementstxt._filenames:
                        self.bin.pip("install", "-r", filename).run()
                    self.refingerprint()

            if self._extra_packages is not None:
                if self._extra_packages.changed:
                    for package in self._extra_packages.value:
                        self.bin.pip("install", package).run()
                    self.refingerprint()

    def verify(self):
        assert self.base_python.build.version.replace("-dev", "") in self.bin.python(
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
