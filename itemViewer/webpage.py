from flask import Flask, render_template, g, jsonify
import sqlite3
import os
import traceback

# absFilePath = os.path.abspath(__file__)
# os.chdir( os.path.dirname(absFilePath) )

# Configuration
DATABASE = 'items.db'

# stats_group = [
#     ["Watchful", "Shadowy", "Dangerous", "Persuasive"],
#     ["Bizarre", "Dreaded", "Respectable"],
#     ["A_Player_of_Chess", "Artisan_of_the_Red_Science", "Glasswork", "Kataleptic_Toxicology", "Mithridacy", "Monstrous_Anatomy", "Shapeling_Arts", "Zeefaring", "Neathproofed", "Steward_of_the_Discordance"]
# ]

# Basic Variables
main_stats = ["Watchful", "Shadowy", "Dangerous", "Persuasive"]
rep_stats = ["Bizarre", "Dreaded", "Respectable"]
advanced_stats= ["A_Player_of_Chess", "Artisan_of_the_Red_Science", "Glasswork", "Kataleptic_Toxicology", "Mithridacy", "Monstrous_Anatomy", "Shapeling_Arts", "Zeefaring", "Neathproofed", "Steward_of_the_Discordance"]
menace_stats= ["Nightmares", "Scandal", "Suspicion", "Wounds"]
old_stats=["Savage", "Elusive", "Baroque", "Cat_Upon_Your_Person"]
# 25 groups in total
stat_group = main_stats + rep_stats + advanced_stats + menace_stats + old_stats

changeable_categories = ["Hat","Clothing","Gloves","Weapon","Boots","Companion","Affiliation","Transport","Home_Comfort"]
static_categories = ["Spouse","Treasure","Destiny","Tools_of_the_Trade","Ship","Club"]
all_categories = changeable_categories + static_categories

item_type = ["have_item","free_item","all_item"]

table_dictionary = {
    "Changeable": {},
    "Static":{}
}

app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
    try:
        return sqlite3.connect(DATABASE)
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        # Here, you can also return a custom error page to the user
        return None


@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()


def populate_dictionary(category, stat, have_value, fate_value, title, value, origin, icon):
    """
    Populates the table dictionary based on the category, stat, have_value, and fate_value.
    """
    #This is the basic item dictionary shared between all items.
    item_dict = {
        "item_name": title,
        "value": value,
        "origin": origin,
        "icon": icon
        }
    
    if have_value == 1:
        item_key = "have_item"
        item_dict["color"] = ""  # This will be updated later when comparing values
    elif fate_value == 0:
        item_key = "free_item"
    else:
        item_key = "all_item"
        
    # Now, populate the table_dictionary
    table_dictionary["Changeable" if category in changeable_categories else "Static"][category][stat][item_key] = item_dict

def create_table(have_value=None, fate_value=None, compare_table=None):
    # Connect to the database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        for category in all_categories:
            for stat in stat_group:
                query = f"SELECT title, \"{stat}\", origin, icon FROM items WHERE category = '{category}'"
                if have_value is not None:
                    query += f" AND have = {have_value}"
                elif fate_value is not None:
                    query += f" AND fate = {fate_value}"
                query += f" ORDER BY \"{stat}\" DESC LIMIT 1"

                try:
                    cursor.execute(query)
                except sqlite3.Error as e:
                    print(f"SQL error: {e}")
                    # Handle the error appropriately. Maybe continue to the next iteration or exit the function.

                result = cursor.fetchone()

                if result:
                    title, value, origin, icon = result
                    if not value and have_value:
                        title = "----"
                        value = 0
                    populate_dictionary(category, stat, have_value, fate_value, title, value, origin, icon)
    except sqlite3.Error as e:
        print(f"SQL error: {e}")
    finally:
        conn.close()

@app.route('/')
def show_items():
    try:
        for category in changeable_categories + static_categories:
            if category in static_categories:
                table_dictionary["Static"][category] = {}
                table_top_category = table_dictionary["Static"][category]
                print(f"{category} is in Static")
            else:
                table_dictionary["Changeable"][category] = {}
                table_top_category  = table_dictionary["Changeable"][category]
                print(f"{category} is in Changeable")
            
            # table_umbrella[category] = {}
            for stat in (stat_group):
                table_top_category[stat] = {}
                for item in item_type:
                    table_top_category[stat][item] = {
                        "item_name" : "",
                        "value" : 0,
                        "origin" : "",
                        "icon" : ""
                    }
                table_top_category[stat]["have_item"]["color"] = ""


        # TODO: Add logic to compare tables and update the 'color' value in the dictionary
        # Populate the dictionary
        create_table()  # For all_items
        create_table(have_value=1)  # For have_item
        create_table(fate_value=0)  # For free_item
        # print(table_dictionary)

        # TODO: Update the Flask template to render data from the dictionary instead of the table list.
        return render_template('fl_items.html', 
                                table_dictionary=table_dictionary,
                                all_categories=all_categories,
                                stat_group=stat_group)
    except Exception as e:
        print(f"Error in show_items: {e}")
        print(traceback.format_exc())
        return "An error occurred while processing your request."

if __name__ == '__main__':
    app.run(debug=True)
