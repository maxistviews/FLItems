from flask import Flask, render_template, g
import sqlite3
import os

# absFilePath = os.path.abspath(__file__)
# os.chdir( os.path.dirname(absFilePath) )

# Configuration
DATABASE = 'items.db'

app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

@app.route('/')
def show_items():
    stats_group = [
    ["Watchful", "Shadowy", "Dangerous", "Persuasive"],
    ["Bizarre", "Dreaded", "Respectable"],
    ["A_Player_of_Chess", "Artisan_of_the_Red_Science", "Glasswork", "Kataleptic_Toxicology", "Mithridacy", "Monstrous_Anatomy", "Shapeling_Arts", "Zeefaring", "Neathproofed", "Steward_of_the_Discordance"]
    ]


    categories = ["Hat","Clothing","Gloves","Weapon","Boots","Companion","Affiliation","Transport","Home_Comfort"]

    def create_table(have_value):
        table_data = []
        for category in categories:
            row = [category]
            for stat_group in stats_group:
                for stat in stat_group:
                    query = f"SELECT title, \"{stat}\" FROM items WHERE have = {have_value} AND category = '{category}' ORDER BY \"{stat}\" DESC LIMIT 1"
                    cursor.execute(query)
                    result = cursor.fetchone()
                    if result:
                        title, value = result
                        print(f"Original title: {title}, Original value: {value}")  # Print original values
                        if not value or value < 0: # Check if value is 0 or less than 0
                            title = "-----"
                            value = "0"
                        row.extend([title or "", value or "0"])  # Use empty string or 0 if None
                    else:
                        row.extend(["None", "None"])
            table_data.append(row)
        return table_data
    

    # Connect to the database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create tables
    table_have_1 = create_table(have_value=1)
    table_have_0 = create_table(have_value=0)

    conn.close()

    return render_template('fl_items.html',
                            table_have_1=table_have_1, 
                            table_have_0=table_have_0, 
                            stats_group=stats_group)

# def show_items():

#     # base_stats = ["Watchful", "Shadowy", "Dangerous", "Persuasive"]
#     # bdr_stats = ["Bizarre", "Dreaded", "Respectable"]
#     # magcats_stats= ["A Player of Chess", "Artisan of the Red Science", "Glasswork", "Kataleptic Toxicology", "Mithridacy", "Monstrous Anatomy", "Shapeling Arts", "Zeefaring", "Neathproofed", "Steward of the Discordance"]
#     # menace_stats= ["Nightmares", "Scandal", "Suspicion", "Wounds"]
#     # old_stats=["Savage!", "Elusive!", "Baroque!", "Cat Upon Your Person"]

#     # all_stats = [base_stats, bdr_stats, magcats_stats, menace_stats, old_stats]

#     categories = ["Hat","Clothing","Gloves","Weapon","Boots","Companion","Affiliation","Transport","Home_Comfort"]
#     # unchangeable_categories = ["Spouse","Treasure","Destiny","Tools_of_the_Trade","Ship","Club"]

#     # all_categories = [categories, unchangeable_categories]

#     data_have = {}
#     data_fate_0 = {}
#     data_fate_1 = {}

#     data = {}

#     for stats_group in stats_groups:
#         for stat in stats_group:
#             for category in categories:
#                 # Query for have=1
#                 query_have = f"SELECT title, MAX(\"{stat}\") FROM items WHERE have = 1 AND category = '{category}'"
#                 result_have = g.db.execute(query_have).fetchone()
#                 data_have.setdefault(stat, []).append(result_have)

#                 # Query for fate=0
#                 query_fate_0 = f"SELECT title, MAX(\"{stat}\") FROM items WHERE fate = 0 AND category = '{category}'"
#                 result_fate_0 = g.db.execute(query_fate_0).fetchone()
#                 data_fate_0.setdefault(stat, []).append(result_fate_0)

#                 # Query for fate=1
#                 query_fate_1 = f"SELECT title, MAX(\"{stat}\") FROM items WHERE fate = 1 AND category = '{category}'"
#                 result_fate_1 = g.db.execute(query_fate_1).fetchone()
#                 data_fate_1.setdefault(stat, []).append(result_fate_1)


#     return render_template(
#         'fl_items.html',
#         all_stats=stats_groups,
#         # all_categories=all_categories,
#         data_have=data_have,
#         data_fate_0=data_fate_0,
#         data_fate_1=data_fate_1,
#         zip=zip
#     )

if __name__ == '__main__':
    app.run(debug=True)
