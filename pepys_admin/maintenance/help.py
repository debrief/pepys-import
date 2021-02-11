INTRO_HELP_TEXT = """# Maintenance Interface Documentation
You can use the maintenance interface to build custom queries and
do specific actions such as merging assets, exporting data, etc.

The interface is composed of 4 panels:

## First panel: Select data type F2
You can select the data table you want to query data from.
(Platform table is the only one available for now)

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

HELP_TEXT = """# First panel: Select data type (F2)
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
Merge Platforms is the only available action for now.

The action applies to the platforms you selected in the preview
list if any. When merging, you will be prompted to select the
target platform in a popup. Select the platform and press Enter.
Once the platforms are merged, press Enter and the Preview List
will be updated.
"""
