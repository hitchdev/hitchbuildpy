Python Library Source Virtualenv:
  description: |
    Build a virtualenv that installs python library source code.
  given:
    pyenv_version: 3.5.0
    files:
      setup.py: |
        from distutils.core import setup
        
        setup(
            name='foo',
            version='1.0',
            install_requires=["python-slugify"]
        )
      foo/__init__.py:
        from foo.dofoo import fooslugify
        
        __version__ = '1.0'
      foo/dofoo.py: |
        from slugify import slugify
      
        def fooslugify(string):
            return "foo-" + slugify(string)
      venvs/README.txt: Directory containing project virtualenvs
      share/README.txt: Directory containing shared basepythons
      debugreqs.txt: |
        # tools for debugging
        ensure==0.6.2
    setup: |
      import hitchbuildpy

      pylibrary = hitchbuildpy.PyLibrary(
          base_python=hitchbuildpy.PyenvBuild("3.5.0").with_build_path("share"),
          module_name="foo",
          library_src="."
      ).with_requirementstxt("debugreqs.txt").with_build_path("venvs")
  steps:
  - Run: |
      pylibrary.ensure_built()

      assert "1.0" in pylibrary.bin.python(
          "-c", "import foo ; print(foo.__version__)"
      ).output()

      assert "foo-test-me" in pylibrary.bin.python(
          "-c", "import foo ; print(foo.fooslugify('TEST me'))"
      ).output()
      
      assert pylibrary.bin.python(
          "-c", "import ensure ; ensure.Ensure(True).is_true()"
      ).output() == ""

  - Write file:
      filename: foo/dofoo.py
      contents: |
        from slugify import slugify
      
        def fooslugify(string):
            return "foobar-" + slugify(string)

  - Run: |
      pylibrary.ensure_built()
      
      assert "foobar-test-me" in pylibrary.bin.python(
          "-c", "import foo ; print(foo.fooslugify('TEST me'))"
      ).output()

  variations:
    with python 3:
      given:
        pyenv_version: 3.5.0
        
    with python 2:
      given:
        pyenv_version: 2.7.10

