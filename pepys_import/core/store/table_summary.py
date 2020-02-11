from tabulate import tabulate


class TableSummary(object):
    """
    A summary of the contents of a table.

    :param session: Bounded session for querying table
    :param table_name: Name of the table
    :return: Number of rows and creation date of last item added
    """

    def __init__(self, session, table_name):
        self.session = session
        self.table_name = table_name
        self.number_of_rows = None
        self.created_date = None

    def table_summary(self):
        number_of_rows = self.session.query(self.table_name).count()
        last_row = (
            self.session.query(self.table_name)
            .order_by(self.table_name.created_date.desc())
            .first()
        )
        created_date = "-"
        if last_row:
            created_date = str(last_row.created_date)
        self.number_of_rows = number_of_rows
        self.created_date = created_date


# TODO: not implemented yet
def table_delta(first_table, second_table):
    """
    A listing of changes between two TableSummarySet objects.

    :param first_table: First TableSummarySet object
    :param second_table: Second TableSummarySet object
    :return: Change in number of rows
    """
    pass


# TODO: not implemented yet
class TableSummarySet(object):
    """A collection of TableSummary elements."""

    def __init__(self, table_summaries):
        self.table_summaries = table_summaries
        self.headers = ["Table name", "Number of rows", "Last item added"]

    def report(self):
        """Produce an HTML pretty-printed report of the contents of the summary."""

        return tabulate(
            [(k,) + v for k, v in self.table_summaries.items()],
            headers=self.headers,
            tablefmt="pretty",
        )

    def compare_to(self, other: "TableSummarySet"):
        """Produce an HTML pretty-printed report of the contents of the summary."""
        pass
