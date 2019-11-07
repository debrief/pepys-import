import os
import csv


def import_from_csv(data_store, path, files):
    for file in sorted(files):
        # split file into filename and extension
        table_name, _ = os.path.splitext(file)
        possible_method = "add_to_" + table_name.lower().replace(" ", "_")
        method_to_call = getattr(data_store, possible_method, None)
        if method_to_call:
            with open(os.path.join(path, file), "r") as f:
                reader = csv.reader(f)
                # skip header
                _ = next(reader)
                with data_store.session_scope() as session:
                    for row in reader:
                        method_to_call(*row)
        else:
            print(f"Method({possible_method}) not found!")
