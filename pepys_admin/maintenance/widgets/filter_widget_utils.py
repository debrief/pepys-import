import operator
from typing import List

from pepys_import.core.store.data_store import DataStore
from pepys_import.utils.table_name_utils import table_name_to_class_name

operator_dict = {
    "=": operator.eq,
    "!=": not operator.eq,
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
}
and_or_dict = {
    "AND": operator.and_,
    "OR": operator.or_,
}


def filter_widget_output_to_query(outputs: List[List], table_name: str, data_store: DataStore):
    # Example: [["name", "=", "HMS Floaty"], ["AND"], ["Nationality.name", "=", "name here"]], Platforms
    class_name = table_name_to_class_name(table_name)
    class_obj = getattr(data_store.db_classes, class_name)
    queries = list()
    for idx, output in outputs:
        if len(output) == 3:
            column, ops, value = output
            if "." in column:
                column = column.lower().replace(".", "_")

            try:  # Try to get table field
                col = getattr(class_obj, column)
            except AttributeError:
                pass
            try:  # Try to create relationship, raise only if this attempt fails, too
                ...
            except AttributeError:
                raise AttributeError(f"Column not found! Error in {idx}: '{column}'")

            if ops == "LIKE":
                queries.append(col.like(f"%{value}%"))
            elif ops in operator_dict:
                queries.append(operator_dict[ops](col, value))
            else:
                raise ValueError(f"Operator Error in {idx}: '{ops}'!")
        elif len(output) == 1:
            if output[0] in and_or_dict:
                queries.append(and_or_dict[output[0]])
            else:
                raise ValueError(f"Operator Error in {idx}: '{output}'!")
        else:
            raise ValueError(
                f"There should be one or three variables in each filter. Error in {idx}: '{output}'!"
            )
    # TODO: iterate over queries list, and merge them according to "and" or "or" between two elements
