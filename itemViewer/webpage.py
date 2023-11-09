from flask import Flask, current_app, render_template, request, redirect, g, jsonify, url_for, session
import sqlite3
import requests
import os
import traceback
from colour import Color
import logging

# absFilePath = os.path.abspath(__file__)
# os.chdir( os.path.dirname(absFilePath) )

# Configuration
DATABASE = 'items.db'
icon_folder = 'itemViewer/static/icons/'

# Basic Variables
def color_setup():
    global color_list
    global color_dic

    color_worst = Color("red")
    color_best = Color("green")
    color_list = list(color_worst.range_to(color_best,11))

    color_dic = {}
    for i in range(len(color_list)):
        color_dic[f"item-value-color-{i}"] = str(color_list[i])

def init_app():
    # This will run once before the first request to the app.
    # Initialize the table structure
    create_table()
    # Initialize the colors
    color_setup()

# TODO: Include the stat groups as a seperate table in the SQL with a column for "include"? Also "stat_type" = Main, reputation, etc.
# Might be better than putting them all here?
stat_group = {
    "Watchful":"owlsmall.png",
    "Shadowy":"bearsmall.png",
    "Dangerous":"catsmall.png",
    "Persuasive":"foxsmall.png",
    "Bizarre":"sidebarbizarresmall.png",
    "Dreaded":"sidebardreadedsmall.png",
    "Respectable":"sidebarrespectablesmall.png",
    "A_Player_of_Chess":"chesspiecesmall.png",
    "Artisan_of_the_Red_Science":"dawnmachinesmall.png",
    "Glasswork":"mirrorsmall.png",
    "Kataleptic_Toxicology":"honeyjarsmall.png",
    "Mithridacy":"snakehead2small.png",
    "Monstrous_Anatomy":"tentaclesmall.png",
    "Shapeling_Arts":"amber2.png",
    "Zeefaring":"captainhatsmall.png",
    "Neathproofed":"snowflakesmall.png",
    "Steward_of_the_Discordance":"blacksmall.png",
    "Nightmares":"sidebarnightmaressmall.png",
    "Scandal":"sidebarscandalsmall.png",
    "Suspicion":"sidebarsuspicionsmall.png",
    "Wounds":"sidebarscandalsmall.png",
    "Savage":"sidebarsavagesmall.png",
    "Elusive":"sidebarelusivesmall.png",
    "Baroque":"sidebarbaroquesmall.png",
    "Cat_Upon_Your_Person":"placeholder2small.png"
}
# totals = {stat: 0 for stat in stat_group}

# main_stats = ["Watchful", "Shadowy", "Dangerous", "Persuasive"]
# rep_stats = ["Bizarre", "Dreaded", "Respectable"]
# advanced_stats= ["A_Player_of_Chess", "Artisan_of_the_Red_Science", "Glasswork", "Kataleptic_Toxicology", "Mithridacy", "Monstrous_Anatomy", "Shapeling_Arts", "Zeefaring", "Neathproofed", "Steward_of_the_Discordance"]
menace_stats= ["Nightmares", "Scandal", "Suspicion", "Wounds"]
old_stats=["Savage", "Elusive", "Baroque", "Cat_Upon_Your_Person"]

# # 25 groups in total
# stat_list = main_stats + rep_stats + advanced_stats + menace_stats + old_stats

for key in old_stats: # + menace_stats
    if key in stat_group:
        del stat_group[key]


# icon_group = main_icons + rep_icons + advanced_icons + menace_icons + old_icons

changeable_categories = ["Hat","Clothing","Gloves","Weapon","Boots","Companion","Affiliation","Transport","Home_Comfort"]
static_categories = ["Spouse","Treasure","Destiny","Tools_of_the_Trade","Ship","Club"]
all_categories = changeable_categories + static_categories

table_item_type = ["have_item","compare_item"]

# table_dictionary[top_category][category][stat]["have_item"]["value"]
# table_dictionary[]
table_dictionary = {
    "Changeable": {},
    "Static":{}
}


def connect_db():
    try:
        return sqlite3.connect(DATABASE)
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        # Here, you can also return a custom error page to the user
        return None

def smallify_icons(icon):
    # This function takes the icon name and adds small before.png ex: owl.png and makes it owlsmall.png
    # Split the filename from its extension
    base_name, extension = icon.rsplit('.', 1)    
    # Append 'small' to the base_name
    smallified_name = f"{base_name}small.{extension}"

    return smallified_name

def set_colors():
    # For each item category in all item categories, check each stat and compare it to the compare value.
    for category in all_categories:
            for stat in stat_group:
                stat_shortcut = table_dictionary["Changeable" if category in changeable_categories else "Static"][category][stat]
                have_value = stat_shortcut["have_item"]["value"]
                compare_value = stat_shortcut["compare_item"]["value"]

                # Divide the have_value by the compare value. This will give you a %. The closer to 100% (1.0), the closer to green you are.
                if compare_value == 0:
                    have_vs_compare = 10
                else:
                    have_vs_compare = round(have_value / compare_value * 10)
                    if have_vs_compare >=11:
                        have_vs_compare = 10

                stat_shortcut["have_item"]["color"] = color_dic[f'item-value-color-{have_vs_compare}']

                # print(f"For {category} with: '{stat}' {have_value} / {compare_value} = {have_vs_compare}")
                # print(f"Assigned colour {str(color_list[have_vs_compare])} to it. {have_vs_compare}th color.")

def download_icon(icon):
    """
    First open /static/icons and check if the file already exists there, if not, download the icon from: https://images.fallenlondon.com/icons/{icon}
    Example: https://images.fallenlondon.com/icons/owlsmall.png
    """
    icon_path = icon_folder + icon
    
    # Check if the icon already exists
    if not os.path.exists(icon_path):
        # If not, download the icon
        print(f"Downloading {icon}")
        icon_url = f"https://images.fallenlondon.com/icons/{icon}"
        response = requests.get(icon_url)
        
        # Check if the request was successful
        if response.status_code == 200:
            with open(icon_path, 'wb') as f:
                f.write(response.content)
        else:
            print(f"Failed to download {icon_url}. Status code: {response.status_code}")

def create_table():
    """
    Initializes the table that will be used. All values are empty.
    At the end of this, you get only have_item and compare_item as the two item types inside the table.
    """
    # Find what group the category belongs to an add it to the dictionary.
    for category in changeable_categories + static_categories:

        # Is this a permanent item or a changeable item?
        category_key = "Changeable" if category in changeable_categories else "Static"

        #Create the item category
        table_dictionary[category_key][category] = {}
        
        # Shortcut to the category
        category_shortcut = table_dictionary[category_key][category]
        
        # table_umbrella[category] = {}
        # Now that we have the category, lets add the stats to it.
        for stat in (stat_group):
            category_shortcut[stat] = {}
            for item in table_item_type:
                category_shortcut[stat][item] = {
                    "item_name" : "",
                    "value" : 0,
                    "origin" : "",
                    "icon" : ""
                }
            category_shortcut[stat]["have_item"]["color"] = ""

def update_table(totals, item_type = "have_item"):
    """""
    This function will update the table_dictionary with the values from the database.
    The possible values are "have_item", "all_item" or "free_item"
    """""
    # Connect to the database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    print(f"UPDATE_TABLE: Updating table with {item_type} items.")

    try:
        for category in all_categories:
            for stat in stat_group:
                query = f"SELECT title, \"{stat}\", origin, icon FROM items WHERE category = '{category}'"
                if item_type == "have_item":
                    query += f" AND have = 1"
                elif item_type == "free_item":
                    query += f" AND fate = 0"
                elif item_type == "all_item":
                    # No additional conditions for all items
                    pass

                query += f" ORDER BY \"{stat}\" DESC LIMIT 1"

                try:
                    cursor.execute(query)
                except sqlite3.Error as e:
                    print(f"SQL error: {e}")
                    # Handle the error appropriately. Maybe continue to the next iteration or exit the function.

                result = cursor.fetchone()

                if result:
                    title, value, origin, icon = result
                    icon = smallify_icons(icon)
                    if not value or value <= 0:
                        icon = "blanksmall.png"
                        title = "----"
                        origin = ""
                        value = 0
                    #Now that it is iconsmall.png, lets download it:
                    download_icon(icon)

                    if item_type == "have_item":
                        totals[stat] += value

                    populate_dictionary(category, stat, item_type, title, value, origin, icon)
                    # populate_dictionary(category, stat, have_value, fate_value, title, value, origin, icon)
                else:
                    # Is this needed at all?
                    icon = "blanksmall.png"
                    title = "----"
                    origin = ""
                    value = 0
                    #Now that it is iconsmall.png, lets download it:
                    download_icon(icon)
                    populate_dictionary(category, stat, item_type, title, value, origin, icon)
                    # populate_dictionary_old(category, stat, have_value, fate_value, title, value, origin, icon)

    except sqlite3.Error as e:
        print(f"SQL error: {e}")
    finally:
        conn.close()

def populate_dictionary(category, stat, item_type, title, value, origin, icon):
    """
    Populates the table dictionary based on the item_type given.
    """

    #This is the basic item dictionary shared between all items.
    item_dict = {
        "item_name": title,
        "value": value,
        "origin": origin,
        "icon": icon
        }
    
    if item_type == "have_item":
        item_key = "have_item"
    else:
        item_key = "compare_item"
    
    # Now, populate the table_dictionary
    table_dictionary["Changeable" if category in changeable_categories else "Static"][category][stat][item_key] = item_dict


#####################################################################################################################
############## Flask App ############################################################################################
#####################################################################################################################

app = Flask(__name__)
app.secret_key = 'super_secret_key'
app.config.from_object(__name__)

# Initialize the table structure
create_table()
# Initialize the colors
color_setup()

@app.route('/')
def show_items():
    totals = {stat: 0 for stat in stat_group}
    try:
        for stat, icon in stat_group.items():
            download_icon(icon)

        # TODO: Add logic to compare tables and update the 'color' value in the dictionary
        # Determine the type of items for comparison based on user's choice
        current_compare_table = session.get('comparison_type', 'all_items')  # Default to all_items

        # Populate the dictionaries
        # update_table_old(totals)  # For all_items
        update_table(totals, item_type="have_item")  # For have_item
        update_table(totals, item_type=current_compare_table)  # For comparison

        # Set colors based on comparison results
        set_colors()
        # set_colors(fate_value=0 if compare_table == 'free_items' else None)

        # Show have_item and compare_item for Watchful Companion
        # print(table_dictionary["Changeable"]["Companion"]["Watchful"])
        # print(f'Best Watchful Companion: {table_dictionary["Changeable"]["Companion"]["Watchful"]["compare_item"]["item_name"]} = {table_dictionary["Changeable"]["Companion"]["Watchful"]["compare_item"]["value"]}')
        # print(f'Your Watchful Companion: {table_dictionary["Changeable"]["Companion"]["Watchful"]["have_item"]["item_name"]} = {table_dictionary["Changeable"]["Companion"]["Watchful"]["have_item"]["value"]}')

        # TODO: Update the Flask template to render data from the dictionary instead of the table list.
        return render_template('fl_items.html', 
                                table_dictionary=table_dictionary,
                                all_categories=all_categories,
                                icon_folder=icon_folder,
                                stat_group=stat_group,
                                totals=totals,
                                comparison_type=current_compare_table)
    except Exception as e:
        print(f"Error in show_items: {e}")
        print(traceback.format_exc())
        return "An error occurred while processing your request."
    
@app.route('/set_comparison', methods=['POST'])
def set_comparison():
    comparison_type = request.form.get('comparison_type')
    session['comparison_type'] = comparison_type
    # update_table(totals, item_type=compare_table)
    # set_colors()
    return redirect(url_for('show_items'))

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()


if __name__ == '__main__':
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(debug=True)