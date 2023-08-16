import sqlite3
from prettytable import PrettyTable

# Connect to the database
DATABASE = 'itemViewer/items.db'
conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()
import sqlite3
from prettytable import PrettyTable

def print_table(have_value):
    # Create table header
    header = ["Category"]
    for stat in stats_group:
        header.extend([f"{stat}", "+"])
    table = PrettyTable(header)

    # Query and add rows to the table
    for category in categories:
        row = [category]
        for stat in stats_group:
            query = f"SELECT title, \"{stat}\" FROM items WHERE have = {have_value} AND category = '{category}' ORDER BY \"{stat}\" DESC LIMIT 1"
            cursor.execute(query)
            result = cursor.fetchone()
            if result:
                row.extend(result)
            else:
                row.extend(["None", "None"])
        table.add_row(row)

    print(f"\nItems with have={have_value}:")
    print(table)

# Connect to the database
DATABASE = 'itemViewer/items.db'
conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

stats_group = ["Watchful", "Shadowy", "Dangerous", "Persuasive"]
categories = ["Hat", "Clothing", "Gloves", "Weapon", "Boots", "Companion", "Affiliation", "Transport", "Home_Comfort"]

# Print tables for have=1 and have=0
print_table(have_value=1)
print_table(have_value=0)

conn.close()


