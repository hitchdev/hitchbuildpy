Python Library Source Virtualenv:
  based on: build python
  description: |
    Build a virtualenv that installs python library source code.
  given:
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
    setup: |
      import hitchbuildpy

      pylibrary = hitchbuildpy.PyLibrary(
          base_python=hitchbuildpy.PyenvBuild("3.5.0").with_build_path("share"),
          module_name="foo",
          library_src="."
      ).with_build_path("venvs")
  steps:
  - Run: |
      pylibrary.ensure_built()

      assert "1.0" in pylibrary.bin.python(
          "-c", "import foo ; print(foo.__version__)"
      ).output()

      assert "foo-test-me" in pylibrary.bin.python(
          "-c", "import foo ; print(foo.fooslugify('TEST me'))"
      ).output()

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
