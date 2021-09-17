INTRO_HELP_TEXT = """# Maintenance Interface Documentation
You can use the maintenance interface to build custom queries and
do specific actions such as merging assets, exporting data, etc.

The interface is composed of 4 panels:

## First panel: Select data type F2
You can select the data table you want to query data from.

## Second panel: Build filters F3
You can filter the data in the table selected above based by
selecting specific fields and values for these fields. You can
combine several filters using AND or OR operators.

## Third panel: Preview list F6
The selected and filtered data is visible here.

## Fourth panel: Choose actions F8
Through this panel, you can perform several actions on the data you selected.

# Main navigation principles
You can select a specific panel by pressing the corresponding F key:
F2: Select data type
F3: Build filters
F4: Show Filter Query (TBI)
F5: Show Complete Query (TBI)
F6: Preview List
F7: Preview Graph (TBI)
F8: Choose actions

You can also press Tab to go forward or Shift + Tab to go backward.
"""

HELP_TEXT = """ # First panel: Select data type (F2)
Type the first letter(s) of the table you are looking for.

Press Enter to expand the list of available tables, use arrow
keys to select the table you want and press Enter again.

# Second panel: Build filters (F3)
Each line is either a query or a standalone operator.

You move from one line or one field to another using TAB or Shift
+ TAB

## Query line:
Each query is built in the following way:

Select column: you can select any field from the table

Operator: = is ‘equal to’ (perfect match), != is ‘not equal to’,
LIKE is ‘contains’

Enter value here: you can start typing and a list of existing
values will be filtered based on your input.

At the end of each line, there is a < Delete > button: select the
button and press Enter to delete the corresponding line.

To add a new line, select < Add a filter condition > button and
press Enter.

## Operator line:
A single dropdown allows you to choose between AND and OR.

# Third panel: Preview List (F6)
This panel displays the list of data contained on the selected
table according to the filter you selected.

In the list, you can go up and down the list using arrow keys,
select/un-select an item using Enter.

You can select the entire list by placing the cursor on the
header row.

## Selecting fields
You can customize which fields are shown in the preview using
Ctrl + F: this opens a popup, where you can add or remove fields.

To add a field: navigate to the field you want to appear using
arrow keys and press Enter to add it.

To remove a field: press TAB to change from one column to the
other, navigate using the arrows to select the field you want to
remove and press Enter.

To validate, navigate to the <  OK  >  button using TAB and press
Enter

# Fourth panel: Choose actions (F8)

## 1 - Merge
When multiple rows from a table are selected, the user is invited
to merge the rows. The merge action starts with the user
selecting the target row that that the data is to be merged into.
When merging platforms, the sensors of the platforms to be merged
are moved to the target platform. If a sensor with that name
already exists then the measurements are moved to the existing
sensor.

## 2 - Split platforms
If the data-type is Platform, and just one row is selected, the
user is able to split that platform into multiple new platform
instances. The platforms are split according to the datafiles
their measurements are imported from.

## 3 - Edit values
If one or more rows are selected then Edit Values can be used to
edit one  or more fields for those data items.

## 4 - Delete entries
If one or more rows or entries are selected then Delete Entries can
be used to delete these from the table. This is a permanent change and
cannot be reversed once confirmed.

## 5 - Add Entry
This opens a prompt box in which a new entry can be entered into the table
by simply filling out the required information about the new entry and
clicking confirm.

## 6 - View Entry
If one entry is selected from the third panel then View Entry can be
used to see further information about the selected entry.

## 7 - Export to CSV
If one or more entries are selected then Export to CSV can be used to
export the chosen information to a CSV file. The export will only
export chosen entries and columns.
The file location and name can be chosen by the user.
"""
