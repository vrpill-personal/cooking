import json
import os
from datetime import datetime
import PySimpleGUI as sg

DATA_FILE = 'fridge.json'

# Load items from JSON file
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        try:
            ITEMS = json.load(f)
        except json.JSONDecodeError:
            ITEMS = []
else:
    ITEMS = []

# Helper to save items back to file
def save_items():
    with open(DATA_FILE, 'w') as f:
        json.dump(ITEMS, f, indent=2)

# Calculate days left from expiry date string
def calc_days_left(expiry_str):
    try:
        exp = datetime.strptime(expiry_str, '%Y-%m-%d')
        return (exp.date() - datetime.today().date()).days
    except ValueError:
        return None

# Convert items list to table data with days left
def get_table_data():
    data = []
    for item in ITEMS:
        days_left = calc_days_left(item['expiry'])
        data.append([item['name'], str(item['weight']), item['expiry'], str(days_left) if days_left is not None else '?'])
    return data

# Build the main window layout
layout = [
    [sg.Table(values=get_table_data(), headings=['Name', 'Weight (g)', 'Expiry', 'Days Left'],
              auto_size_columns=False, col_widths=[15, 10, 12, 10],
              key='-TABLE-', enable_events=True, select_mode=sg.TABLE_SELECT_MODE_BROWSE)],
    [sg.Button('Add Item'), sg.Button('Remove Selected'), sg.Button('Exit')]
]

window = sg.Window('Fridge Watchdog', layout, finalize=True)

def refresh_table():
    data = get_table_data()
    window['-TABLE-'].update(values=data)
    # Set row colors for expiring soon
    row_colors = []
    for idx, item in enumerate(ITEMS):
        days_left = calc_days_left(item['expiry'])
        if days_left is not None and days_left <= 3:
            row_colors.append((idx, 'red'))
    window['-TABLE-'].update(row_colors=row_colors)

refresh_table()

# Event loop
while True:
    event, values = window.read()
    if event in (sg.WINDOW_CLOSED, 'Exit'):
        break
    elif event == 'Add Item':
        # Modal form to add item
        form_layout = [
            [sg.Text('Name'), sg.Input(key='-NAME-')],
            [sg.Text('Weight (g)'), sg.Input(key='-WEIGHT-')],
            [sg.Text('Expiry (YYYY-MM-DD)'), sg.Input(key='-EXPIRY-')],
            [sg.Button('Add'), sg.Button('Cancel')]
        ]
        form_window = sg.Window('Add Item', form_layout, modal=True)
        while True:
            fevent, fvalues = form_window.read()
            if fevent in (sg.WINDOW_CLOSED, 'Cancel'):
                form_window.close()
                break
            if fevent == 'Add':
                name = fvalues['-NAME-'].strip()
                weight = fvalues['-WEIGHT-'].strip()
                expiry = fvalues['-EXPIRY-'].strip()
                if not name or not weight or not expiry:
                    sg.popup('All fields required')
                    continue
                try:
                    weight = float(weight)
                except ValueError:
                    sg.popup('Weight must be a number')
                    continue
                if calc_days_left(expiry) is None:
                    sg.popup('Expiry must be YYYY-MM-DD')
                    continue
                ITEMS.append({'name': name, 'weight': weight, 'expiry': expiry})
                save_items()
                refresh_table()
                form_window.close()
                break
    elif event == 'Remove Selected':
        selected = values['-TABLE-']
        if selected:
            idx = selected[0]
            del ITEMS[idx]
            save_items()
            refresh_table()

window.close()
