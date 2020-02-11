from tabulate import tabulate


class TableSummary(object):
    """
    A summary of the contents of a table, which sends query to DB and finds
    number of rows and creation date of last item added.

    :param session: Bounded session for querying table
    :type session: SQLAlchemy Session
    :param table_name: Name of the table
    :type table_name: String
    """

    def __init__(self, session, table_name):
        self.session = session
        self.table_name = table_name
        self.number_of_rows = None
        self.created_date = None
        self.table_summary()

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
        """Produce an HTML pretty-printed report of the contents of the summary.

        :return: String of HTML
        """

        contents = []
        for table in self.table_summaries:
            content = tabulate(
                [table.number_of_rows, table.created_date],
                # headers=self.headers,
                tablefmt="pretty",
            )
            contents.append(content)
        print(contents)
        return contents

    def compare_to(self, other: "TableSummarySet"):
        """Produce an HTML pretty-printed report of the contents of the summary.

        :param other: A TableSummarySet object to compare
        :type other: TableSummarySet
        :return: An array of TableDelta items
        """
        pass
