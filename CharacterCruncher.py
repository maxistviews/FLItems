import sqlite3
import json
import os

# Put your character.json into the directory beside this file and run it.

absFilePath = os.path.abspath(__file__)
os.chdir( os.path.dirname(absFilePath) )

# Open the SQLite database
conn = sqlite3.connect('itemViewer/items.db')
cursor = conn.cursor()

# Set all the "have" values to 0
cursor.execute("UPDATE items SET have = 0")
print("Reset all 'have' values to 0.")

errorWrite = 0
dashes = "=========================================\n"

# Load the JSON data
with open('character.json') as f:
    data = json.load(f)

possessions_end = len(data['possessions'])

# Go through each item category
for i in range(47, possessions_end):
    possessions = data['possessions'][i]['possessions'] 

    # Go through each item in the category
    for item in possessions:
        item_id = item['id']
        item_name = item['name']
        # Try to decode the name using UTF-8
        item_name = item_name.encode('latin1').decode('utf-8')

        #Select the name that is in the database that has that ID.
        cursor.execute(f"SELECT title FROM items WHERE ID = {item_id}")
        #This gives you one table with one value
        check_item_name = cursor.fetchone()

        # Check to see if the item in character.json matches the item in the database item.db
        if check_item_name is not None:
            # Check if names match, or in the case of a nickname, the real name will be in brackets.
            if check_item_name[0] == item_name or f"({check_item_name[0]})" in item_name:
                # Update the corresponding row in the SQLite database
                cursor.execute(f"UPDATE items SET have = 1 WHERE ID = {item_id}")
                print("Updated ID" + str(item_id) + ": " + item_name)
            else:
                print(f"ERROR: Item {check_item_name[0]} in the database doesn't line up with Item {item_name}")
                errorWrite += 1
        else:
            cursor.execute(f"UPDATE items SET have = 1 WHERE ID = {item_id}")
            print(dashes + "ERROR: ID" + str(item_id) + ": " + item_name)
            print("ERROR: Does not match the name in the database: " + str(check_item_name) + dashes)
            errorWrite += 1

    # The `fetchone()` function returns a tuple representing a row from the SQL query results, even if that row only contains a single column. So `result[0]` is used to extract the first (and only) column from that row, which in this case is the `title` of the item from the database.
    # On the other hand, if `result` is `None` (i.e., no row was found in the database that matches the ID), we can't use indexing to extract a column from it, because `None` is not a tuple. In this case, we're converting `result` to a string to print it out, which will just print the string "None". 
    # In summary, `result[0]` is used when a matching row is found in the database and we want to extract the `title` from that row, while `str(result)` is used when no matching row is found and we want to print out "None" to indicate that no match was found.


if errorWrite > 0:
    print(f"\n\nCompleted ingesting character.json. Error(s) encountered: {errorWrite}")
else:
    print(f"\n\nCompleted ingesting character.json.")

# Commit the changes and close the connection
conn.commit()
conn.close()

