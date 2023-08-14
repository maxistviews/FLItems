from flask import Flask, render_template, g
import sqlite3
import os

# absFilePath = os.path.abspath(__file__)
# os.chdir( os.path.dirname(absFilePath) )

# Configuration
DATABASE = 'itemViewer/items.db'

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
    base_stats = ["Watchful", "Shadowy", "Dangerous", "Persuasive"]
    bdr_stats = ["Bizarre", "Dreaded", "Respectable"]
    magcats_stats= ["A Player of Chess", "Artisan of the Red Science", "Glasswork", "Kataleptic Toxicology", "Mithridacy", "Monstrous Anatomy", "Shapeling Arts", "Zeefaring", "Neathproofed", "Steward of the Discordance"]
    menace_stats= ["Nightmares", "Scandal", "Suspicion", "Wounds"]
    old_stats=["Savage!", "Elusive!", "Baroque!", "Cat Upon Your Person"]

    all_stats = [base_stats, bdr_stats, magcats_stats, menace_stats, old_stats]

    categories = ["Hat","Clothing","Gloves","Weapon","Boots","Companion","Affiliation","Transport","Home_Comfort"]
    unchangeable_categories = ["Spouse","Treasure","Destiny","Tools_of_the_Trade","Ship","Club"]

    all_categories = [categories, unchangeable_categories]

    data = {}

    for stats, categories in zip(all_stats, all_categories):
        for stat in stats:
            data[stat] = []
            for category in categories:
                # Query to get the title and maximum value of the specified stat for the given category
                query = f"SELECT title, MAX({stat}) FROM items WHERE category = '{category}'"
                cur = g.db.execute(query)
                result = cur.fetchone()
                # If the result is None, use a default value (e.g., 0)
                if result[1] is None:
                    result = (result[0], 0)
                data[stat].append(result)

    return render_template('fl_items.html', 
                            all_stats=all_stats, 
                            all_categories=all_categories, 
                            data=data, 
                            zip=zip)

if __name__ == '__main__':
    app.run(debug=True)
