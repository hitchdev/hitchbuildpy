Project virtualenv:
  description: |
    Build a project based virtualenv for something like Django.
  based on: build python
  given:
    files:
      reqs.txt: |
        python-slugify==1.2.2
    setup: |
      import hitchbuildpy

      pyenv = hitchbuildpy.PyenvBuild("3.5.0").with_build_path(".")

      virtualenv = hitchbuildpy.VirtualenvBuild(pyenv, name="venv")\
                               .with_requirementstxt("reqs.txt")\
                               .with_build_path(".")
      virtualenv.ensure_built()
  steps:
  - Run: |
      assert "1.2.2" in virtualenv.bin.python(
          "-c",
          "import slugify ; print(slugify.__version__)"
      ).output()

      assert "test-me" in virtualenv.bin.python(
          "-c",
          "import slugify ; print(slugify.slugify('TEST me'))"
      ).output()

  - Write file:
      filename: reqs.txt
      contents: python-slugify==1.2.3

  - Run: |
      version = virtualenv.bin.python(
          "-c",
          "import slugify ; print(slugify.__version__)"
      ).output()
      assert "1.2.3" in version, "version was actually {0}".format(version)
