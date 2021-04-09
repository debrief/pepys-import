from datetime import datetime

from pepys_admin.maintenance.widgets.masked_input_widget import MaskedInputWidget
from pepys_admin.maintenance.widgets.utils import datetime_validator, int_validator


class DatetimeWidget(MaskedInputWidget):
    def __init__(self, datetime_value=None, on_change=None):
        prompt_format_list = ["yyyy", "!-", "mm", "!-", "dd", "! ", "HH", "!:", "MM", "!:", "SS"]

        if isinstance(datetime_value, datetime):
            dt_list = datetime.strftime(datetime_value, "%Y-%m-%d-%H-%M-%S").split("-")
            format_list = [
                dt_list[0],
                "!-",
                dt_list[1],
                "!-",
                dt_list[2],
                "! ",
                dt_list[3],
                "!:",
                dt_list[4],
                "!:",
                dt_list[5],
            ]
        else:
            format_list = prompt_format_list

        super().__init__(
            format_list,
            overall_validator=datetime_validator,
            part_validator=int_validator,
            on_change=on_change,
        )

    @property
    def datetime_value(self):
        if self.text == "yyyy-mm-dd HH:MM:SS":
            return None
        else:
            try:
                return datetime.strptime(self.text, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None
