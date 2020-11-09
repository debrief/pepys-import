import importlib.util
import inspect
import os
import sys


def import_module_(file):
    """Import modules using file object's full path and name.

    :param file: File object, which has name and full path attributes
    :type file: File
    """
    spec = importlib.util.spec_from_file_location(file.name, file.path)
    # If spec is none, it means that it is not a module, return an empty list
    if spec is None:
        return list()
    module = importlib.util.module_from_spec(spec)
    sys.modules[file.name] = module
    spec.loader.exec_module(module)
    # extract classes with this format: (class name, class)
    classes = inspect.getmembers(sys.modules[module.__name__], inspect.isclass)
    return classes


def import_validators(path):
    """Import validators in the given path.

    :param path: Path to the directory that has validators
    :type path: String
    :return:
    """
    validators = list()
    if os.path.exists(path):
        for file in sorted(os.scandir(path), key=lambda x: x.name):
            # import file using its name and full path
            if file.is_file():
                classes = import_module_(file)
                for _, class_ in classes:
                    print(inspect.signature(class_))
                    validators.append(class_)
    return validators
