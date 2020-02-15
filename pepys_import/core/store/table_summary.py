from tabulate import tabulate


class TableSummary(object):
    """
    A summary of the contents of a table, which sends query to DB and finds
    number of rows and creation date of last item added.

    :param session: Bounded session for querying table
    :type session: SQLAlchemy Session
    :param table: SQLAlchemy Table object
    :type table_name: SQLAlchemy Declarative Base
    """

    def __init__(self, session, table):
        self.session = session
        self.table = table
        self.table_name = self.table.__tablename__
        self.number_of_rows = None
        self.created_date = None
        self.table_summary()

    def table_summary(self):
        number_of_rows = self.session.query(self.table).count()
        last_row = (
            self.session.query(self.table)
            .order_by(self.table.created_date.desc())
            .first()
        )
        created_date = "-"
        if last_row:
            created_date = str(last_row.created_date)
        self.number_of_rows = number_of_rows
        self.created_date = created_date


def table_delta(first_summary, second_summary):
    """
    A listing of changes between two TableSummarySet objects.

    :param first_summary: First TableSummarySet object
    :param second_summary: Second TableSummarySet object
    :return: Change in number of rows
    """
    differences = []
    for first, second in zip(first_summary, second_summary):
        diff = first.number_of_rows - second.number_of_rows
        differences.append(diff)
    return differences


class TableSummarySet(object):
    """A collection of TableSummary elements."""

    def __init__(self, table_summaries):
        self.table_summaries = table_summaries
        self.headers = ["Table name", "Number of rows", "Last item added"]

    def report(self):
        """Produce an HTML pretty-printed report of the contents of the summary.

        :return: String of HTML
        """

        return tabulate(
            [
                (table.table_name, table.number_of_rows, table.created_date)
                for table in self.table_summaries
            ],
            headers=self.headers,
            tablefmt="pretty",
        )

    def compare_to(self, other: "TableSummarySet"):
        """Produce an HTML pretty-printed report of the contents of the summary.

        :param other: A TableSummarySet object to compare
        :type other: TableSummarySet
        :return: An array of TableDelta items
        """
        return table_delta(self.table_summaries, other.table_summaries)
