def table_summary(session, table_name):
    number_of_rows = session.query(table_name).count()
    last_row = (
        session.query(table_name).order_by(table_name.created_date.desc()).first()
    )
    created_date = "-"
    if last_row:
        created_date = str(last_row.created_date)
    return number_of_rows, created_date


# TODO: not implemented yet
class TableSummarySet(object):
    def report(self):
        pass

    def compare_to(self, other: "TableSummarySet"):
        pass
