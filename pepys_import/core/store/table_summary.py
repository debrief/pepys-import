from sqlalchemy.orm import undefer
from tabulate import tabulate

from pepys_import.core.store import constants
from pepys_import.core.store.db_status import TableTypes


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
        self.table_summary()

    def table_summary(self):
        number_of_rows = self.session.query(self.table).count()
        last_row = (
            self.session.query(self.table)
            .options(
                undefer("*")
            )  # Fetch all attributes to enforce to failing if there is any mismatch
            .order_by(self.table.created_date.desc())
            .first()
        )
        created_date = "-"
        if last_row:
            created_date = str(last_row.created_date)
        self.number_of_rows = number_of_rows
        self.created_date = created_date


class TableSummarySet:
    """A collection of TableSummary elements."""

    def __init__(self, table_summaries):
        self.table_summaries = table_summaries
        self.headers = ["Table name", "Number of added rows", "Last item added"]

    def report(self, title="REPORT"):
        """Produce an pretty-printed report of the contents of the summary.

        :return: String of text
        """
        res = f"=={title}==\n"
        res += tabulate(
            [
                (table.table_name, table.number_of_rows, table.created_date)
                for table in self.table_summaries
                if table.number_of_rows != 0
            ],
            headers=self.headers,
            tablefmt="github",
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


def get_table_summaries(datastore):
    datastore.setup_table_type_mapping()
    measurement_table_objects = datastore.meta_classes[TableTypes.MEASUREMENT]
    metadata_table_objects = datastore.meta_classes[TableTypes.METADATA]
    tables = measurement_table_objects + metadata_table_objects
    exclude = [constants.LOG, constants.EXTRACTION, constants.CHANGE]
    table_summaries = [
        TableSummary(datastore.session, c) for c in tables if c.__tablename__ not in exclude
    ]

    return TableSummarySet(table_summaries)
