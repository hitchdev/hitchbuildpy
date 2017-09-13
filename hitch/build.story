Build Python:
  preconditions:
    setup: |
      import hitchbuildpy
      import hitchbuild

      bundle = hitchbuild.BuildBundle(
          hitchbuild.BuildPath(build="."),
          "db.sqlite"
      )

      bundle['py3.5.0'] = hitchbuildpy.PythonBuild("3.5.0")
      bundle['venv3.5.0'] = hitchbuildpy.VirtualenvBuild(bundle['py3.5.0'])

    code: |
      bundle.ensure_built()
  scenario:
  - Run code
