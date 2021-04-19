from datetime import datetime

from pepys_admin.maintenance.widgets.masked_input_widget import MaskedInputWidget
from pepys_admin.maintenance.widgets.utils import datetime_validator, int_validator


class DatetimeWidget(MaskedInputWidget):
    def __init__(self, datetime_value=None, on_change=None, no_seconds=False):
        """Widget for entering datetime values in ISO-standard format. Based on the MaskedInputWidget.

        :param datetime_value: Value to set the widget entries to, defaults to None
        :type datetime_value: datetime, optional
        :param on_change: Function to call when value changes, defaults to None
        :type on_change: function, optional
        :param no_seconds: If True, don't show the box for entering seconds, and just show YYYY-MM-DD HH:MM, defaults to False
        :type no_seconds: bool, optional
        """
        self.no_seconds = no_seconds

        if self.no_seconds:
            prompt_format_list = ["yyyy", "!-", "mm", "!-", "dd", "! ", "HH", "!:", "MM"]
        else:
            prompt_format_list = [
                "yyyy",
                "!-",
                "mm",
                "!-",
                "dd",
                "! ",
                "HH",
                "!:",
                "MM",
                "!:",
                "SS",
            ]

        if isinstance(datetime_value, datetime):
            dt_list = datetime.strftime(datetime_value, "%Y-%m-%d-%H-%M-%S").split("-")
            if self.no_seconds:
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
                ]
            else:
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
        if (
            self.text == "yyyy-mm-dd HH:MM:SS"
            or self.text == "yyyy-mm-dd HH:MM"
            or self.text == "    -  -     :  :  "
            or self.text == "-- ::"
            or self.text == "    -  -     :  "
            or self.text == "-- :"
        ):
            return None
        else:
            if self.no_seconds:
                result = datetime.strptime(self.text, "%Y-%m-%d %H:%M")
            else:
                result = datetime.strptime(self.text, "%Y-%m-%d %H:%M:%S")
            return result
