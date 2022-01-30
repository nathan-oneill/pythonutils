# `pythonutils`
A collection of useful functions that I've developed (or found - with appropriate references), will eventually be unittested, and use semi-regularly. This also serves as a way for me to test out github automation.

## Included sub-modules
- `assorted` (`asd`)
- `builtinMethods` (`bm`)
- `intmath` (`intm`)
- `io`
- `uncertainty` (`unc`)


# Installation
To install directly from Github use (see [here](https://stackoverflow.com/questions/16584552/how-to-state-in-requirements-txt-a-direct-github-source) or [here](https://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path) for more info): 

```pip install git+git://github.com/nathan-oneill/pythonutils@main#egg=pythonutils-nathan-oneill```

If the git repo is cloned locally first, then you can use:

```pip install file:////path/to/local/repo#egg=pythonutils-nathan-oneill```


# Documentation Guide
## Do
- Follow the [Sphinx Numpy format](https://numpydoc.readthedocs.io/en/latest/format.html). With exceptions:
- Use tabs to indent rather than spaces. (Doesn't take as long to type)
- Use `'` instead of `"` except when the string contains the `'` character
- Align `=` for related variable assignments on adjacent lines
- Leave 3 empty lines between 'sections' (indicated by a line of `#`), 2 between classes, and 1 between functions.
- Use camelCase instead of snake_case
- End every function with `return`
- Use `## SUBSECTION ##` to indicate subsections in classes, and `# SUBSECTION` to indicate subsections in functions
- Sort functions alphabetically in each subsection/section (whichever is more specific)

## Do not
- go over 80 characters in a line


# TODO
- Continuous-integration unittests
- Continuous-integration code coverage with [codecov](https://github.com/apps/codecov)
- Continuous-integration pylint?
-  Replace installation `@main` with `/versions/...` once versions are started being tagged.