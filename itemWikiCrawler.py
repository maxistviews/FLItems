import requests
import sqlite3
import mwparserfromhell
import json
import re
import os
from termcolor import colored

SKIP_ITEMS = {
    "A Box of Ten Delights!","A Selection of Jilt's Treasures","A Set of Wedding Lithographs","Amber Carnival Token","Anticandle (Second Chance)","Archaeologist's Hat","Calamitous Parrot","Chrysalis Candle (Retired)","Crumbled Remnant","Echo (Harbour Provisioners)","Exceptional Petal","Feducci's Confession","Forbidden Map-Fragment","Fuel","Gambit: Benjamin's Friends","Gift of Adoration","Handsome Lad with a Healthy Appetite","His Amused Lordship's Confession","Iron Knife Token","Knife-and-Candle: A Proud Parade of Victories","Knot-name","Letter of introduction","Lettice's Confession","Listening Candle","Montaigne Lantern","Noise-Eaters","Order of the Wistful Rose, First Class","Order of the Wistful Rose, Second Class","Order of the Wistful Rose, Third Class","Order Ovate, Blood","Order Ovate, Glory","Order Ovate, Ice","Order Ovate, Night","Order Vespertine, Merciless","Order Vespertine, Monstrous","Order Vespertine, Perilous","Primitive Hat","Queer Parcel","Retired Vake-Hunter's Rifle","Sharp Iron Key","Sinning Jenny's Confession","St Beau's Candle (old)","Supplies","Surprise Attack Plan","The Ambitious Barrister's Confession","The Bishop of St Fiacre's' Confession","The Captivating Princess' Confession","The Cheery Man's Confession","The Illuminated Gentleman's Confession","The Jovial Contrarian's Confession","The Kashmiri Princess' Confession","The Melancholy Curate's Confession","The Soft-Hearted Widow's Confession","The Veteran Privy Councillor's Confession","Twincandle", "Mitigating Factor", "Category:Connected Pet","Category:Knife-and-Candle Medals"
    }

#Config
OVERWRITE_ALL = True  # Set to False if you don't want to overwrite every database entry
DEBUG_ITEM_EFFECTS_EXTRACTION = True
DEBUG_PRINT_API = True  # Set to True if you want to print the API response to the console

#List of categories to query the API
api_categories = ["Category:Boon","Category:Hat","Category:Clothing","Category:Gloves","Category:Weapon","Category:Boots","Category:Companion","Category:Destiny","Category:Spouse","Category:Treasure","Category:Tools_of_the_Trade","Category:Affiliation","Category:Transport","Category:Home_Comfort","Category:Ship","Category:Club"]
# api_categories = ["Category:Home_Comfort"]
api_categories = ["Category:Weapon"]
# api_categories = ["Category:Companion"]

dashes = "=========================================\n"

# Function to fetch the content of a specific page using the page_id
def get_page_content(page_id):
    # Define the endpoint URL
    url = "https://fallenlondon.wiki/w/api.php"

    # Define the parameters for the API request
    params = {
        "action": "query",
        "prop": "revisions",
        "pageids": page_id,
        "rvprop": "content|ids",
        "rvslots": "main",
        "format": "json",
        "formatversion": "2"
    }

	# Send the request to the server
    response = requests.get(url, params=params)

    # If the request was successful, return the data
    if response.status_code == 200:
        data = response.json()
        if DEBUG_PRINT_API:
            print(colored(response.text,"grey"))

        content = data["query"]["pages"][0]["revisions"][0]["slots"]["main"]
        last_update = data["query"]["pages"][0]["revisions"][0]["revid"]
        return content, last_update
    # If the request failed, print an error message and return None
    else:
        print(colored(f"ERROR: Request failed with status code: {response.status_code}.\nCheck if API/Wiki is down.","red"))
        return None, None

# Get list of items from a specific category.
def get_items(category_title):
    # Define the endpoint URL
    url = "https://fallenlondon.wiki/w/api.php"
    items = []
    cmcontinue = ""
    while True:
        # Define the parameters for the API request
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category_title,
            "format": "json",
            "cmcontinue": cmcontinue
        }

        # Send the request to the server
        response = requests.get(url, params=params)

        # If the request was successful, return the data
        if response.status_code == 200:
            data = response.json()
            items.extend(data["query"]["categorymembers"])

            if "continue" in data:
                cmcontinue = data["continue"]["cmcontinue"]
                print("Found " + str(len(items))+ " entries...")
            else:
                print("Total: " + str(len(items))+ " entries.")
                break
        # If the request failed, print an error message and return an empty list
        else:
            
            print(colored(f"ERROR: Request failed with status code: {response.status_code}.\nCheck if API/Wiki is down.","red"))
            break

    return items

# Function to extract the effects from the page content
def extract_effects(page_content):
    wikitext = page_content["content"]
    parsed_wikitext = mwparserfromhell.parse(wikitext)
    templates = parsed_wikitext.filter_templates()
    
    effects = {}
    origin = None
    fate = False
    # have = False
    shop = None
    access = None
    access_info = None
    icon = None
    ID = None

    wikilinks = parsed_wikitext.filter_wikilinks()
    categories = [link.title.strip() for link in wikilinks if link.title.startswith("Category:")]
    
    jobs = ["Campaigner","Enforcer","Rat-Catcher","Trickster","Journalist","Watcher","Tough","Minor Poet","Pickpocket","Enquirer","Author","Murderer","Stalker","Agent","Mystic","Conjurer","Tutor","Undermanager","Correspondent","Licentiate","Monster-Hunter","Midnighter","Silverer","Crooked-Cross","Notary","Doctor"]
    set_jobs = set("Category:" + job for job in jobs)
    # Creates a few Categories that will be avoided later.
    item_rarity = set("Category:" + item for item in ["Precious", "Rare", "Coveted", "Scarce", "Commonplace"])
    item_categories = set(["Category:Boon","Category:Hat","Category:Clothing","Category:Gloves","Category:Weapon","Category:Boots","Category:Companion","Category:Destiny","Category:Spouse","Category:Treasure","Category:Tools_of_the_Trade","Category:Affiliation","Category:Transport","Category:Home_Comfort","Category:Ship","Category:Club"])
    unwanted_categories = item_rarity | item_categories

    for template in templates:
        if template.name.strip() == "Item":
            for param in template.params:
                # print(param)
                param_name = param.name.strip()
                # if the param_name is description, just continue to the next item.
                if param_name == "Description" or param_name == "Item Type":
                    continue
                elif param_name == "ID":
                    if param.value.strip().isdigit():
                        ID = int(param.value.strip())
                    else:
                        ID = None  # or some other default value
                elif param_name == "Icon":
                    icon = str(param.value.strip())
                    #Make the first letter lowercase
                    if icon[0].isupper():
                        icon = icon[0].lower() + icon[1:]
                    icon = icon.replace(" ", "_")
                elif param_name == "Origin":
                    origin = str(param.value.strip())
                elif param_name == "Access":
                    access = str(param.value.strip())
                elif param_name == "Access info":
                    access_info = str(param.value.strip()).replace(" (Guide)", "")  # Remove (Guide) if present
                
                    # For some reason, the wiki is not consistent with the naming, so add the full name to this:
                    if access_info == "Feast of the Rose":
                        access_info = "Feast of the Exceptional Rose"

                    # if the item is retired, from the access, then append "Retired" to the access info. First check if it starts with the word "Retired"
                    if not access_info.startswith("Retired") and access == "Retired":
                            access_info = "Retired: " + access_info
                elif param_name == "Shop":
                    shop = str(param.value.strip())
                elif param_name == "Rat Shop":
                    shop = str(param.value.strip()) + " (The Rat Market)"
                elif param_name == "Fate":
                    fate_value = str(param.value.strip()).lower()
                    fate = True if fate_value == "yes" else False

                # Extract each of the "Effects", which are the stats.

                if param_name.startswith("Effects"):
                    # Find the portion of the string between {{IL| and }}
                    match_effect_name = re.search(r"{{IL\|(.*?)}}", str(param.value))
                    if match_effect_name:
                        
                        # Search for any weird characters at the end, like a |
                        if match_effect_name.group(1).endswith("|"):
                            if DEBUG_ITEM_EFFECTS_EXTRACTION: print(f"Removing | from {match_effect_name.group(1)}")
                            effect_name = match_effect_name.group(1)[:-1]
                        else:
                            effect_name = match_effect_name.group(1)

                        # Extract the effect value, which is the number after the "+/-" sign
                        match_effect_value = re.search(r"([+-]?\d+)", str(param.value))
                        if match_effect_value:
                            effect_value = int(match_effect_value.group(1))
                        else:
                            # If you cant find it, then set to None. Shouldnt happen a lot.
                            print(colored(f"ERROR: In {param_name} can't find value for {effect_name}","red"))
                            effect_value = None
                    else:
                        # If not in IL format, check for Menace Effect format: '{{Menace Effect|MenaceName|increase/decrease|rate={value}}}'
                        menace_effect_match = re.search(r"{{Menace Effect\|(.*?)\|(increase|decrease)?(\|rate=(\d+))?}}", str(param.value))
                        if menace_effect_match:
                            # Get name of the menace ["Nightmares", "Scandal", "Suspicion", "Wounds"]
                            effect_name = menace_effect_match.group(1)
                            # Check if thid matches the "increase/decrease". If nothing, assume decrease.
                            action = menace_effect_match.group(2) or "decrease" 
                            # In the future, we may get items that effect menaces more than just 10%, so this is here for that reason.
                            rate = menace_effect_match.group(4)

                            if rate:  # if rate is provided, use it as the effect value
                                effect_value = int(rate)
                            else:
                                # If the action was increase, then value is 10. If decrease, then -10.
                                effect_value = 10 if action == "increase" else -10
                        else:
                            print(colored(f"ERROR: In {param_name} can't find the name or value","red"))
                            effect_name = effect_value = None

                    if effect_name:
                        effects[effect_name] = effect_value


            if access is not None:
                if origin is not None:
                    print(f"DEBUG: ORIGIN IS NOT NONE")
                if access == "Festival":
                    if origin is not None:
                        origin = re.sub(r" \(Guide\)", "", origin)
                elif access == "Fate":
                    fate = True
                    if access_info == "Incarnadine Fur Robe":
                        origin = "Christmas"
                    elif access_info is not None:
                        origin = access_info
                    else:
                        origin = None
                elif access_info and access_info.startswith("Retired: "):
                    origin = access_info
                # elif access == "Retired" or access == "Legacy":
                elif access == "Legacy":
                    # If access_info exists, use that 
                    if access_info != None:
                        origin = str(access) + ": " + str(access_info)
                    else:
                        print(f"Origin: " + str(origin) + " replaced with Access: " + access)
                        origin = access
                elif access == "Location":
                    if access_info is not None:
                        origin = access_info
                    else:
                        origin = str(access) + ": " + str(access_info)
                elif access == "Code":
                    origin = "Code: " + str(access_info)
                elif access == "Developer":
                    origin = "Developer Item"
            
            if not origin and access == "Festival": # This might be redundant, but lets keep it...
                    origin = access_info
            elif shop != None:
                if origin is None:
                    origin =  "Shop: " + str(shop)

            for idx, category in enumerate(categories):
                sanitized_category = category.replace("Category:", "").replace(" Items", "")
                if sanitized_category in effect_names:
                    continue
                # Check for renown items
                elif fate is False and category == "Fate":
                    fate = True
                elif category == "Category:Renown Items":
                    origin = "Renown Item"
                    # Check the next category for the faction name
                    faction_pattern = re.compile(r"Category:Faction: ([\w\s-]+)")
                    match = faction_pattern.search(categories[idx+1])  # checking the next category
                    if match:
                        origin += f": {match.group(1)}"
                    break  # break once the faction is found

                # Check for profession
                elif category in set(set_jobs):
                    origin = "Profession: " + category.replace("Category:", "")
                    break  # break once the job is found

                # If category doesn't belong to unwanted ones, set the origin to that category
                elif category not in unwanted_categories:
                    origin = category.replace("Category:", "")
                    origin = "Retired: " + origin.strip()
                    break  # break once a suitable origin is found
            
            #If there is still no origin, and its a Fate item, say fate?
            if not origin and fate:
                origin = "Fate"

            # # Add other categories and their corresponding origin values as needed
            # elif "Category:Some Other Category" in categories:
            #     origin = "Some Other Origin Value"
    if DEBUG_ITEM_EFFECTS_EXTRACTION:
        # Debugging origin
        print(f"DEBUG: Item origin: {origin}")
        print(f"DEBUG: Item access: {access}")
        print(f"DEBUG: Item access_info: {access_info}")
        print(f"DEBUG: Item fate: {fate}")
        print(f"DEBUG: Item effects: {effects}")
    return effects, origin, fate, ID, icon


def sanitize_column_name(name):
    sanitized_name = re.sub(r'\W|^(?=\d)','_', name)
    return sanitized_name.rstrip('_')

# # Might use this later. not now.
# def insert_or_update_audit_log(cursor, page_id, old_value, new_value):
#     cursor.execute("SELECT old_value, new_value FROM audit_log WHERE page_id=?", (page_id,))
#     existing_log = cursor.fetchone()
    
#     if existing_log:
#         db_old_value, db_new_value = existing_log
#         # If the new value is different from the existing value in the audit log
#         if db_new_value != new_value:
#             cursor.execute("UPDATE audit_log SET old_value=?, new_value=? WHERE page_id=?", (db_new_value, new_value, page_id))
#     else:
#         cursor.execute("INSERT INTO audit_log (page_id, old_value, new_value) VALUES (?, ?, ?)", (page_id, old_value, new_value))


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    # Load the effect names from the file
    with open('effectNames/effectNames.json', 'r') as f:
        global effect_names
        effect_names = json.load(f)

    global infoError, infoNew, infoSkipped
    infoError, infoNew, infoSkipped = 0, 0, 0

    # Define the relative path to the database
    db_path = "items.db"
    # Get the absolute path
    full_db_path = os.path.abspath(db_path)
    print(f"Connecting to database at: {full_db_path}")

    # Connect to the SQLite database
    conn = sqlite3.connect(full_db_path)
    cursor = conn.cursor()

    # Create the "items" table if it doesn't already exist
    # Generate the SQL to create the table
    columns = ["ID INTEGER PRIMARY KEY UNIQUE", # This will make ID the primary key and unique
                "page_id INTEGER",
                "last_update TEXT", 
                "category TEXT", 
                "title TEXT",
                "have BOOLEAN", 
                "origin TEXT", 
                "fate BOOLEAN", 
                "icon TEXT"]
	
    # Create the "audit_log" table if it doesn't already exist. Not using this rightnow.
    # cursor.execute("""CREATE TABLE IF NOT EXISTS audit_log (
    #                 log_id INTEGER PRIMARY KEY,
    #                 page_id INTEGER,
    #                 old_value TEXT,
    #                 new_value TEXT,
    #                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")

    for effect_name in effect_names:
        columns.append(f"{sanitize_column_name(effect_name)} INTEGER")
    create_table_sql = "CREATE TABLE IF NOT EXISTS items (" + ", ".join(columns) + ")"
    cursor.execute(create_table_sql)

    # Loop over each category (ie Category:Boots)
    for category in api_categories:
        # Remove the "Category:" prefix from the category name
        category_name = category.replace("Category:", "")

        print(dashes + "Looking through category:" + category_name + "\n" +dashes)


        # Get the items in the category
        items = get_items(category)

        # Loop over each item
        for item in items:
            title = item["title"]
			# Use get method to fetch ID and default to None if not found
            page_id = item.get("pageid", None)

            # If the item doesn't have an ID or is in the skip list, continue to the next iteration
            if title in SKIP_ITEMS:
                print(colored(f"INFO: SKIPPING Known Item with no ID: {title}","yellow"))
                infoSkipped +=1
                continue

            print("Item name: " + title)

            # Get the content of the item's page
            content_data, last_update = get_page_content(page_id)

            # Extract the DISPLAYTITLE value from the page content, if available
            # The only case I've seen so far is for "M. D_____' A_____ for _______: F____ Edition", but there may be others in the future!
            if content_data:
                display_title_pattern = re.compile(r"{{DISPLAYTITLE:(.*?)}}")
                match = display_title_pattern.search(content_data['content'])
                if match:
                    title = match.group(1).strip()
                    print(colored(f"INFO: Changed Item name to Wiki display name: {title}","yellow"))

            # print(page_content)
            # If the page content was successfully retrieved
            if content_data:
                # Extract the effects from the page content
                effects, origin, fate, ID, icon = extract_effects(content_data)
                have = None
                db_id, db_page_id, db_last_update = None, None, None
                # If we dont have the ID, skip this item.
                if not ID:
                    print(colored(f"INFO: SKIPPING. UNKNOWN ITEM: *** NO ID in Wiki. Item: {title} ***","yellow"))
                    infoSkipped +=1
                    continue

                #Now we assume the item has an ID.
                # Check if item already exists in database with the same last_update
                # If an item with the same ID exists
                cursor.execute("SELECT ID, page_id, last_update FROM items WHERE ID=?", (ID,))
                database_item = cursor.fetchone()
                if database_item:
                    db_id, db_page_id, db_last_update = database_item
                
                # Prepare a dictionary of column names and values
                values = {
                    "ID": ID,
                    "page_id": page_id,
                    "category": category_name,
                    "title": title,
                    "origin": origin,
                    "fate": fate,
                    "have": have,
                    "last_update": last_update,
                    "icon": icon
                }

                for effect_name in effect_names:
                    sanitized_effect_name = sanitize_column_name(effect_name)
                    values[sanitized_effect_name] = effects.get(effect_name, None)

                #Does this item ID exist in the database?                
                if db_id and ID == db_id:
                    #Does this ID have the same page_id?
                    if page_id != db_page_id or OVERWRITE_ALL:
                        # Need to update the database's page_id.
                        values_without_have = {key: values[key] for key in values if key != "have"}
                        sql_update = "UPDATE items SET " + ", ".join(f"{key} = ?" for key in values_without_have) + " WHERE ID = ?"
                        cursor.execute(sql_update, list(values_without_have.values()) + [ID])

                        if not OVERWRITE_ALL:
                            print(f"Wiki changed page_id for this item. Old: {db_page_id} New: {page_id}")
                    elif page_id == db_page_id:
                        #If the page_id is the same, when was the last update?
                        # If the last_update is the same, then theres no change and no reason to update it. unless you want to with OVERWRITE_ALL flag.
                        if db_last_update != last_update:
                            values_without_page_id_or_have = {key: values[key] for key in values if key != "page_id" and key != "have"}
                            sql_update = "UPDATE items SET " + ", ".join(f"{key} = ?" for key in values_without_page_id_or_have) + " WHERE ID = ?"
                            cursor.execute(sql_update, list(values_without_page_id_or_have.values()) + [db_id])

                        elif db_last_update == last_update or not OVERWRITE_ALL:
                            print(colored(f"INFO: SKIPPING. Up to Date. Item: {title}","yellow"))
                            infoSkipped +=1
                            continue
                        # now if the if statement returns false, we need to update the database.
                        else:
                            print(colored("ERROR: ID and page_id is the same, but there was an error with last_update.","red"))
                            infoError +=1
                    else:
                        print(colored("ERROR: ID Found, but there was an error with page_id.","red"))
                        infoError +=1

                # Item ID doesn't exist in the database. Its a New Item!
                else:  
                    # Construct the SQL insert statement
                    columns = ", ".join(values.keys())
                    placeholders = ", ".join("?" for _ in values)

                    sql_insert = f"INSERT INTO items ({columns}) VALUES ({placeholders})"
                    cursor.execute(sql_insert, list(values.values()))
                    print(colored("INFO: *** New Item! Adding. ***",'green'))

                    infoNew +=1
    # Commit the changes and close the connection to the database
    conn.commit()
    conn.close()


# If the script is run directly (not imported as a module), call the main function
if __name__ == "__main__":
    main()

    print(dashes + "DONE!\n" + dashes)
    if infoError > 0: 
        print(f"Errors: {infoError}")
    else:
        print("No Errors.")
    print(f"Skipped Items: {infoSkipped}")
    print(f"New Items: {infoNew}")