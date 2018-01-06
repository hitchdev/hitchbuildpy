Build Pyenv:
  given:
    setup: |
      import hitchbuildpy

      pyenv = hitchbuildpy.PyenvBuild("3.5.0").with_build_path(".")
    code: |
      pyenv.ensure_built()
      assert "3.5.0" in pyenv.bin.python("--version").output()
  steps:
  - Run code

Build virtualenv:
  based on: build pyenv
  given:
    code: |
      virtualenv = hitchbuildpy.VirtualenvBuild(pyenv, name="venv").with_build_path(".")
      virtualenv.ensure_built()
      assert "3.5.0" in virtualenv.bin.python("--version").output()

#Install from requirements.txt:
  #preconditions:
    #setup: |
      #import hitchbuildpy
      #import hitchbuild

      #bundle = hitchbuild.BuildBundle(
          #hitchbuild.BuildPath(build=".", share="."),
      #)

      #bundle['py3.5.0'] = hitchbuildpy.PythonBuild("3.5.0")
      #bundle['venv3.5.0'] = hitchbuildpy.VirtualenvBuild(bundle['py3.5.0'])\
                                        #.with_requirementstxt("requirements1.txt")

    #code: |
      #bundle.ensure_built()
      #bundle['venv3.5.0'].bin.python("-c", "import slugify ; print(slugify.__version__)").run()
    #requirements1.txt: |
      #python-slugify==1.2.3
  #scenario:
  #- Run code
  #- Output ends with: 1.2.3
  #- Write file:
      #filename: requirements1.txt
      #contents: python-slugify==1.2.4
  #- Sleep: 1
  #- Run code
  #- Output ends with: 1.2.4
