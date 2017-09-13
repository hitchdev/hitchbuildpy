Build Python:
  preconditions:
    setup: |
      from hitchbuildpy import PythonBuild
      import hitchbuild

      bundle = hitchbuild.BuildBundle(
          hitchbuild.BuildPath(build="."),
          "db.sqlite"
      )

      bundle['thing'] = PythonBuild("3.5.0")

    code: |
      bundle.ensure_built()
  scenario:
  - Run code
