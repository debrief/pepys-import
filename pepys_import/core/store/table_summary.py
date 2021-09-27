from tabulate import tabulate

from pepys_import.core.store import constants


class TableSummary:
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
        self.names = []
        self.table_summary()

    def table_summary(self):
        number_of_rows = self.session.query(self.table).count()
        last_row = (
            self.session.query(self.table.created_date)
            .order_by(self.table.created_date.desc())
            .first()
        )
        created_date = "-"
        if last_row:
            created_date = str(last_row.created_date)
        self.number_of_rows = number_of_rows
        self.created_date = created_date
        if self.table_name in [constants.SENSOR, constants.PLATFORM]:
            if self.created_date == "-":
                self.names = []
            else:
                self.names = [
                    result[0] for result in self.session.query(getattr(self.table, "name")).all()
                ]


class TableSummarySet:
    """A collection of TableSummary elements."""

    def __init__(self, table_summaries):
        self.table_summaries = table_summaries
        self.headers = ["Table name", "Number of rows", "Last item added"]
        self.metadata_headers = ["Table name", "Names"]

    def report(self):
        """Produce a pretty-printed report of the contents of the summary.

        :return: String of text
        """
        res = tabulate(
            [
                (table.table_name, table.number_of_rows, table.created_date)
                for table in self.table_summaries
                if table.number_of_rows != 0
            ],
            headers=self.headers,
            tablefmt="grid",
        )
        res += "\n"
        return res

    def report_metadata_names(self, differences):
        """Produce a pretty-printed report of the contents of the summary of metadata tables.

        :return: String of text
        """
        res = tabulate(
            [(table_name, ",".join(sorted(names))) for table_name, names in differences if names],
            headers=self.metadata_headers,
            tablefmt="grid",
        )
        res += "\n"
        return res

    @staticmethod
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

    def show_delta_of_rows_added(self, other: "TableSummarySet"):
        """Produce an pretty-printed report of the contents of the summary.

        :param other: A TableSummarySet object to compare
        :type other: TableSummarySet
        :return: A string that includes report of the contents of the summary
        """
        differences = self.table_delta(self.table_summaries, other.table_summaries)
        for table, diff in zip(self.table_summaries, differences):
            table.number_of_rows = diff
        return self.report()

    @staticmethod
    def table_delta_metadata(first_summary, second_summary):
        """
        A listing of changes between two TableSummarySet objects.

        :param first_summary: First TableSummarySet object
        :param second_summary: Second TableSummarySet object
        :return: A list of tuples that have table name and entity names
        """
        differences = []
        show_number_of_rows = False
        for first, second in zip(first_summary, second_summary):
            diff = list(set(first.names) - set(second.names))
            if len(diff) > 6:  # If there are more than 6 names, show normal report
                show_number_of_rows = True
            differences.append((first.table_name, diff))
        return differences, show_number_of_rows

    def show_delta_of_rows_added_metadata(self, other: "TableSummarySet"):
        """Produce an pretty-printed report of the contents of the summary.

        :param other: A TableSummarySet object to compare
        :type other: TableSummarySet
        :return: A string that includes report of the contents of the summary
        """
        differences, show_number_of_rows = self.table_delta_metadata(
            self.table_summaries, other.table_summaries
        )
        if show_number_of_rows:
            return self.show_delta_of_rows_added(other)

        return self.report_metadata_names(differences)
