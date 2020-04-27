import csv
import os


def import_from_csv(data_store, path, files, change_id):
    for file in sorted(files):
        # split file into filename and extension
        table_name, _ = os.path.splitext(file)
        possible_method = "add_to_" + table_name.lower().replace(" ", "_")
        method_to_call = getattr(data_store, possible_method, None)
        if method_to_call:
            with open(os.path.join(path, file), "r") as file_object:
                reader = csv.reader(file_object)
                # extract header
                header = next(reader)
                for row in reader:
                    keyword_arguments = dict(zip(header, row))
                    method_to_call(**keyword_arguments, change_id=change_id)
        else:
            print(f"Method({possible_method}) not found!")


def cache_results_if_not_none(cache_attribute):
    def real_decorator(f):
        def helper(self, name):
            cache = eval("self." + cache_attribute)
            print(f"Looking in cache for {name}")
            if name not in cache:
                print("Not found in cache")
                result = f(self, name)
                if result:
                    self.session.expunge(result)
                    cache[name] = result
                return result
            else:
                print(f"Found in cache, returning {cache[name]}")
                return cache[name]

        return helper

    return real_decorator
