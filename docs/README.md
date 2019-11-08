# Pepys Import Documentation

The source for Pepys Import documentation is in this directory. Our documentation uses
[Sphinx](https://www.sphinx-doc.org/en/master/index.html) and [Sphinx's RTD Theme](https://sphinx-rtd-theme.readthedocs.io/en/stable/).

## Building the documentation

- Install requirements.txt in the top level of the project: `pip install -r requirements.txt`
- From the top level directory, `cd` into the `docs/` folder and run:
    1. `make html`

If you would like regenerate the document structure:

- `sphinx-quickstart` can be called to set up a source directory and create necessary configurations.
- Another option is using the following code: `sphinx-apidoc -F -o docs pepys_import`

