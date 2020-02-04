def table_summary(session, table_name):
    number_of_rows = session.query(table_name).count()
    return number_of_rows


class TableSummarySet(object):
    def report(self):
        pass

    def compare_to(self, other: "TableSummarySet"):
        pass
