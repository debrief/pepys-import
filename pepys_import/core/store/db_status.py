from enum import Enum


class TableTypes(Enum):
    METADATA = 1
    MEASUREMENT = 2
    REFERENCE = 3


class DBStatus:
    def __init__(self, data_store, table_types):
        self.data_store = data_store
        self.table_types = table_types
        self.status = None

    # get current table stats, store and return status
    def get_status(self):
        self.status = self.data_store.get_table_type_data(self.table_types)
        return self.status

    # print current stats, plus diff to supplied stats if passed
    def print_status(self, prev_status=None):
        max_length = len(max(self.status, key=len)) + 1
        print("{:<{}} {:<4} {:<4}".format("Table", max_length, "Num", "Diff"))
        for table in self.status:
            print(
                f"{table:<{max_length}} {self.status[table]:<4} "
                f"{self.calculate_diff(table, prev_status):<4}"
            )

    def calculate_diff(self, table, prev_status):
        if not prev_status or table not in prev_status or table not in self.status:
            return "-"
        return self.status[table] - prev_status[table]
