# How to generate TAF documentation:

## Requirements:

1. doxygen 1.8.6 or higher
2. doxypy

> Note:

> TAF Docker container contains doxygen and doxypy dependencies.

How to install doxygen and doxypy on Ubuntu 14.04 or Ubuntu 16.04:
```
$ apt-get install doxygen doxygen-latex
$ pip install doxypy
```

## Generating documentation

### 1. Generate documentation using python script

* Generate HTML and RTF documentation
```
$ cd <taf_root>/taf/utils
$ python generate_documentation.py --rtf --html
```
* Generate HTML with current date in documentation instead of Git tag
```
$ python  generate_documentation.py --html --version=$(date +%D/%T)
```
* Option descriptions
```
$ python generate_documentation.py -h
```

> NOTE:

> Doxygen combines the RTF output to a single file called refman.rtf. This file is optimized for importing into the Microsoft Word. Certain information is encoded using so called fields. To show the actual value you need: `select all->right click->Update Field`.

### 2. Generate documentation using doxygen utility

* Generate HTML documentation
```
$ cd <taf_root>/docs
$ (cat Doxyfile.in; echo "LAYOUT_FILE=DoxygenLayout.xml") | doxygen -
```
* Generate RTF documentation
```
$ cd <taf_root>/docs
$ (cat Doxyfile.in; echo "GENERATE_HTML=NO"; echo "GENERATE_RTF=YES"; echo "RTF_HYPERLINKS=YES"; \
   echo "EXCLUDE_PATTERNS=._* */.git/* */taf/tests/* */unittests/* __init__.py") | doxygen -
```
* Change version
```
$ (cat Doxyfile.in ; echo PROJECT_NUMBER=2.0) | doxygen -
```
or
* Get the most recent version tag from GIT
```
$ (cat Doxyfile.in ; echo PROJECT_NUMBER=$(git describe --abbrev=0)) | doxygen -
```