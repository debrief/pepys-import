# TODO: it doesn't return creation date of last item added.
def table_summary(session, table_name):
    number_of_rows = session.query(table_name).count()
    return number_of_rows


# TODO: not implemented yet
class TableSummarySet(object):
    def report(self):
        pass

    def compare_to(self, other: "TableSummarySet"):
        pass
