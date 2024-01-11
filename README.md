# Activity Monitor App

An app to capture time spent on different applications. A python app using a simple Tkinter UI and Nuitka to bundle into an executable.

## To run

Create a virtual environment - can't use pyenv if you want to bundle with nuitka.

Note you have to have Tkinter configured for your python environment. This can be installed with Homebrew:

```
brew install python-tk
```

```
python3.X -m venv env
source env/bin/activate
pip install --upgrade pip
pip install -r requirements
```

Run using python:

```
python activity_monitor.py
```

## To build

Nuitka is a python interpreter - it converts python files to C to create an executable.

**Note that Nuitka isn't compatible with pyenv**

To build as a standalone file use:

```
python -m nuitka --onefile --macos-create-app-bundle --enable-plugin=tk-inter activity_monitor.py
```

If successful, this will build output activity_monitor.app/Contents/MacOS/, which will contain the activity_monitor executable.

## To do

- use a objc listener for focus app changes instead of mouse input triggers
- remove pandas dependency
- get tabs/urls for other browsers
- build and release scripts
- icon/splash screen
- get active VSCode filename
- probably rewrite in swift/objective c
