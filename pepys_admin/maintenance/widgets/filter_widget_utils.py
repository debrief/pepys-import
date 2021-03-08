import operator
from typing import List

import sqlalchemy
from sqlalchemy.sql.expression import cast

from pepys_import.core.store.data_store import DataStore
from pepys_import.utils.sqlalchemy_utils import UUIDType
from pepys_import.utils.table_name_utils import table_name_to_class_name

operator_dict = {
    "=": operator.eq,
    "!=": operator.ne,
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
    class_name = table_name_to_class_name(table_name)
    class_obj = getattr(data_store.db_classes, class_name)
    queries = list()
    and_or_list = list()
    for idx, output in enumerate(outputs):
        if len(output) == 3:
            column, ops, value = output
            try:  # Try to get table field
                col = getattr(class_obj, column)
            except AttributeError:
                raise AttributeError(f"Column not found! Error in {idx}: '{column}'")

            # If we're trying to filter on a relationship column, then look for the
            # relevant ID column to filter on instead
            # This will either be the local column for the foreign key relationship
            # or the manually-defined local column in the relationship's info
            # dict, if it is a secondary relationship
            try:
                if isinstance(col.prop, sqlalchemy.orm.relationships.RelationshipProperty):
                    if "local_column" in col.prop.info:
                        id_col_name = col.prop.info["local_column"]
                    else:
                        id_col_name = list(col.prop.local_columns)[0].key
                    col = getattr(class_obj, id_col_name)
            except Exception:
                pass

            if ops == "LIKE":
                if isinstance(col.type, UUIDType):
                    queries.append(cast(col, sqlalchemy.String).like(f"%{value}%"))
                else:
                    queries.append(col.like(f"%{value}%"))
            elif ops in operator_dict:
                queries.append(operator_dict[ops](col, value))
            else:
                raise ValueError(f"Operator Error in {idx}: '{ops}'!")
        elif len(output) == 1:
            if output[0] in and_or_dict:
                and_or_list.append(and_or_dict[output[0]])
            else:
                raise ValueError(f"Operator Error in {idx}: '{output}'!")
        else:
            raise ValueError(
                f"There should be one or three variables in each filter. Error in {idx}: '{output}'!"
            )

    if len(queries) == 0:
        return None

    i, j = 1, 0
    query = queries[0]
    while i < len(queries) and j < len(and_or_list):
        query = and_or_list[j](query, queries[i])
        i += 1
        j += 1
    return query
