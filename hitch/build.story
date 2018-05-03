Build python:
  given:
    pyenv_version: 3.6.0
    setup: |
      import hitchbuildpy

      pyenv = hitchbuildpy.PyenvBuild(pyenv_version).with_build_path(".")


Build pyenv 3.6:
  based on: build python
  steps:
  - Run: |
      pyenv.ensure_built()
      assert pyenv_version in pyenv.bin.python("--version").output()

Build pyenv 3.5:
  based on: build pyenv 3.6
  given:
    pyenv_version: 3.5.0
      
Build virtualenv:
  based on: build python
  steps:
  - Run: |
      virtualenv = hitchbuildpy.VirtualenvBuild(pyenv, name="venv").with_build_path(".")
      virtualenv.ensure_built()
      assert pyenv_version in virtualenv.bin.python("--version").output()

Build virtualenv from requirements.txt:
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
