Project virtualenv:
  based on: build python
  about: |
    Build a project based virtualenv to run something like Django.
  given:
    pyenv_version: 3.7.0
    files:
      reqs1.txt: |
        python-slugify==1.2.2
      reqs2.txt: |
        humanize==0.5.0
    setup: |
      from path import Path
      import hitchbuildpy

      pyenv = hitchbuildpy.PyenvBuild(Path(share) / "python-{}".format(pyenv_version), pyenv_version)

      virtualenv = hitchbuildpy.VirtualenvBuild(Path(build_path) / "venv", pyenv)\
                               .with_requirementstxt("../reqs1.txt", "../reqs2.txt")
  variations:
    Just from files:
      steps:
      - Run: |
          virtualenv.ensure_built()

          assert "1.2.2" in virtualenv.bin.python(
              "-c",
              "import slugify ; print(slugify.__version__)"
          ).output()

          assert "test-me" in virtualenv.bin.python(
              "-c",
              "import slugify ; print(slugify.slugify('TEST me'))"
          ).output()

          assert "12.3 billion" in virtualenv.bin.python(
              "-c",
              "import humanize ; print(humanize.intword(12345591313))"
          ).output()

      - Write file:
          filename: reqs1.txt
          contents: python-slugify==1.2.3

      - Run: |
          virtualenv.ensure_built()
          
          version = virtualenv.bin.python(
              "-c",
              "import slugify ; print(slugify.__version__)"
          ).output()
          assert "1.2.3" in version, "version was actually {0}".format(version)

    Also from directly specified libraries:
      about: |
        As well as specifying requirements.txt files to install
        packages from, you can also specify individual packages.
        
        Individual package versions will always be installed *after*
        the requirements.txt files.
      steps:
      - Run: |
          venv = virtualenv.with_packages("python-slugify==1.2.3")

          venv.ensure_built()
          
          assert "1.2.3" in venv.bin.python(
              "-c",
              "import slugify ; print(slugify.__version__)"
          ).output()

      - Run: |
          venv = virtualenv.with_packages("python-slugify==1.2.4")
          venv.ensure_built()

          assert "1.2.4" in venv.bin.python(
              "-c",
              "import slugify ; print(slugify.__version__)"
          ).output()
