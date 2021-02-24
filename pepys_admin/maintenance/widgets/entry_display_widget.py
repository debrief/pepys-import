from prompt_toolkit.layout.containers import HSplit, VSplit
from prompt_toolkit.layout.scrollable_pane import ScrollablePane
from prompt_toolkit.widgets import Label


class EntryDisplayWidget:
    def __init__(self, edit_data, entries):
        self.edit_data = edit_data
        self.entries = entries

        self.widgets = self.generate_widgets()

        self.container = ScrollablePane(content=HSplit(self.widgets, padding=1))

    def generate_widgets(self):
        rows = []

        max_width = max([len(key) for key in self.edit_data.keys()])

        for key, value in self.edit_data.items():
            values_list = [str(getattr(entry, value["system_name"])) for entry in self.entries]
            values_list = list(set(values_list))
            value = ", ".join(values_list)
            rows.append(VSplit([Label(key, width=max_width), Label(" = ", width=3), Label(value)]))

        return rows

    def __pt_container__(self):
        return self.container
