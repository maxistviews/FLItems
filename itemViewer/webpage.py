from flask import Flask, current_app, render_template, request, redirect, g, jsonify, url_for, session
import sqlite3
import requests
import os
import traceback
from colour import Color

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
# https://images.fallenlondon.com/icons/owlsmall.png
icon_folder = "itemViewer/static/icons/"

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
# old_stats=["Savage", "Elusive", "Baroque", "Cat_Upon_Your_Person"]

# # 25 groups in total
# stat_group = main_stats + rep_stats + advanced_stats + menace_stats + old_stats
# icon_group = main_icons + rep_icons + advanced_icons + menace_icons + old_icons

changeable_categories = ["Hat","Clothing","Gloves","Weapon","Boots","Companion","Affiliation","Transport","Home_Comfort"]
static_categories = ["Spouse","Treasure","Destiny","Tools_of_the_Trade","Ship","Club"]
all_categories = changeable_categories + static_categories

item_type = ["have_item","free_item","all_item"]

# table_dictionary[top_category][category][stat]["have_item"]["value"]
# table_dictionary[]
table_dictionary = {
    "Changeable": {},
    "Static":{}
}

# Color block
red = Color("red")
color_list = list(red.range_to(Color("green"),11))

color_dic = {}
for i in range(len(color_list)):
    color_dic[f"item-value-color-{i}"] = str(color_list[i])

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

def smallify_icons(icon):
    # This function takes the icon name and adds small before.png ex: owl.png and makes it owlsmall.png
    # Split the filename from its extension
    base_name, extension = icon.rsplit('.', 1)
    
    # Append 'small' to the base_name
    smallified_name = f"{base_name}small.{extension}"

    return smallified_name

def set_colors(fate_value=None):
    for category in all_categories:
            for stat in stat_group:
                if fate_value == 0:
                    item_key = "free_item"
                else:
                    item_key = "all_item"

                stat_shortcut = table_dictionary["Changeable" if category in changeable_categories else "Static"][category][stat]
                compare_value = stat_shortcut[item_key]["value"]
                have_value = stat_shortcut["have_item"]["value"]
                # if have_value == 0:
                #     have_value =1
                # Divide the have_value by the compare value. This will give you a %. The closer to 100% (1.0), the closer to green you are.
                if compare_value == 0:
                    have_vs_compare = 10
                else:
                    have_vs_compare = round(have_value / compare_value * 10)
                    if have_vs_compare >=11:
                        have_vs_compare = 10

                    # have_vs_compare = have_value % compare_value

                stat_shortcut["have_item"]["color"] = f"item-value-color-{have_vs_compare}"

                print(f"For {category} with: '{stat}' {have_value} / {compare_value} = {have_vs_compare}")
                print(f"Assigned colour {str(color_list[have_vs_compare])} to it. {have_vs_compare}th color.")


def download_icon(icon):
    # First open /static/icons and check if the file already exists there, if not, download the icon from: https://images.fallenlondon.com/icons/{icon}
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

def populate_dictionary(category, stat, have_value, fate_value, title, value, origin, icon):
    """
    Populates the table dictionary based on the category, stat, have_value, and fate_value.
    TODO: Adjust this to only have a compare_item entry. Probaly replace the fate_value key also thats being passed.
    update the functions to be "refresh_table" instead of create_table ?
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

def create_table(totals,have_value=None, fate_value=None, compare_table=None):
    """"""

    """"""
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
                    icon = smallify_icons(icon)
                    if not value or value <= 0:
                        icon = "blanksmall.png"
                        title = "----"
                        origin = ""
                        value = 0
                    #Now that it is iconsmall.png, lets download it:
                    download_icon(icon)
                    if have_value is not None:
                        totals[stat] += value
                    populate_dictionary(category, stat, have_value, fate_value, title, value, origin, icon)

                if not result:
                    icon = "blanksmall.png"
                    title = "----"
                    origin = ""
                    value = 0
                    #Now that it is iconsmall.png, lets download it:
                    download_icon(icon)
                    populate_dictionary(category, stat, have_value, fate_value, title, value, origin, icon)

    except sqlite3.Error as e:
        print(f"SQL error: {e}")
    finally:
        conn.close()

@app.route('/')
def show_items():
    totals = {stat: 0 for stat in stat_group}
    try:
        # download_icon("owlsmall.png")
        for stat, icon in stat_group.items():
            download_icon(icon)

        for category in changeable_categories + static_categories:
            if category in static_categories:
                table_dictionary["Static"][category] = {}
                table_top_category = table_dictionary["Static"][category]
                #print(f"{category} is in Static")
            else:
                table_dictionary["Changeable"][category] = {}
                table_top_category  = table_dictionary["Changeable"][category]
                #print(f"{category} is in Changeable")
            
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
        # Populate the dictionaries
        create_table(totals)  # For all_items
        create_table(totals,have_value=1)  # For have_item
        create_table(totals,fate_value=0)  # For free_item
        # print(table_dictionary)

        set_colors(fate_value=0)

        # TODO: Update the Flask template to render data from the dictionary instead of the table list.
        return render_template('fl_items.html', 
                                table_dictionary=table_dictionary,
                                all_categories=all_categories,
                                icon_folder=icon_folder,
                                stat_group=stat_group,
                                totals=totals)
    except Exception as e:
        print(f"Error in show_items: {e}")
        print(traceback.format_exc())
        return "An error occurred while processing your request."
    
@app.route('/set_comparison', methods=['POST'])
def set_comparison():
    comparison_type = request.form.get('comparison_type')
    session['comparison_type'] = comparison_type
    return redirect(url_for('show_items'))

if __name__ == '__main__':
    app.run(debug=True)
