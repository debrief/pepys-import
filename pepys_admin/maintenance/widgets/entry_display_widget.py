from prompt_toolkit.layout.containers import HSplit, VSplit
from prompt_toolkit.widgets import Label


class EntryDisplayWidget:
    def __init__(self, edit_data, entries):
        """
        Widget to display values from the database as multiple rows.

        :param edit_data: edit_data dictionary giving structure of columns for editing UI
        :type edit_data: dict
        :param entries: List of SQLAlchemy objects for the objects to be edited
        :type entries: list
        """
        self.edit_data = edit_data
        self.entries = entries

        self.widgets = self.generate_widgets()

        self.container = HSplit(self.widgets, padding=1)

    def generate_widgets(self):
        rows = []

        max_width = max([len(key) for key in self.edit_data.keys()])

        for key, value in self.edit_data.items():
            values_list = [str(getattr(entry, value["system_name"])) for entry in self.entries]
            # Just list the unique values
            values_list = list(set(values_list))
            value = ", ".join(values_list)
            # The widgets are just a series of Labels
            rows.append(VSplit([Label(key, width=max_width), Label(" = ", width=3), Label(value)]))

        return rows

    def __pt_container__(self):
        return self.container
