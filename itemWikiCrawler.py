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
DB_PATH = "items.db"  # Path to the database file

#List of categories to query the API
api_categories = ["Category:Boon","Category:Hat","Category:Clothing","Category:Gloves","Category:Weapon","Category:Boots","Category:Companion","Category:Destiny","Category:Spouse","Category:Treasure","Category:Tools_of_the_Trade","Category:Affiliation","Category:Transport","Category:Home_Comfort","Category:Ship","Category:Club"]
# api_categories = ["Category:Home_Comfort"]
# api_categories = ["Category:Ship"]
api_categories = ["Category:Companion"]
# api_categories = ["Category:Hat"]

cl_categories = ["Category:Fate Story Items","Category:Fate Items","Category: Retired"]
# cl_categories = []

infoStatus = {
    "totalItems": {category: 0 for category in api_categories},
    "infoError": 0,
    "infoNew": {
        "total": 0,
        "item_name": {}
    },
    "infoSkipped": 0,
    "APICalls": 0
}

dashes = "=========================================\n"

# Function to construct the URL for the API request
def construct_url(params):
    base_url = "https://fallenlondon.wiki/w/api.php"
    params_str = "&".join([f"{key}={value}" for key, value in params.items()])
    return f"{base_url}?{params_str}"

# Get list of items from a specific category.
def fetch_category_members(category_title):
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
            "cmlimit": "max",
            "cmcontinue": cmcontinue
        }

        # Send the request to the server
        response = requests.get(url, params=params)

        # If the request was successful, return the data
        if response.status_code == 200:
            data = response.json()
            infoStatus["APICalls"] +=1
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

# Fetch multiple items in a batch
def fetch_items_batch(page_ids):
    # Define the endpoint URL
    url = "https://fallenlondon.wiki/w/api.php"

    # Convert list of ids into a single string separated by '|'
    page_ids_str = '|'.join(map(str, page_ids))
    cl_categories_str = '|'.join(map(str, cl_categories))

    # Define the parameters for the API request
    params = {
        "action": "query",
        "prop": "revisions|categories",
        "pageids": page_ids_str,
        "rvprop": "content|ids",
        "rvslots": "main",
        "format": "json",
        "formatversion": "2",
        "cllimit": "max",
        "clcategories": cl_categories_str,
        "clshow": "!hidden"
    }

    # Construct the URL with the parameters
    if DEBUG_PRINT_API:
        full_url = construct_url(params)
        print(colored(f"API Call URL:\n {full_url}","green"))

    # Send the request to the server
    response = requests.get(url, params=params)

    # If the request was successful, return the data
    if response.status_code == 200:
        data = response.json()

        infoStatus["APICalls"] +=1
        if DEBUG_PRINT_API:
            print(f"Number of batch items: {len(data['query']['pages'])}")
            for page in data["query"]["pages"]:
                print(colored(page.keys(), "grey"))

        return data["query"]["pages"]
    else:
        print(colored(f"ERROR: Request failed with status code: {response.status_code}.\nCheck if API/Wiki is down.", "red"))
        return None

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
        infoStatus["APICalls"] +=1
        if DEBUG_PRINT_API:
            print(colored(response.text,"grey"))

        content = data["query"]["pages"][0]["revisions"][0]["slots"]["main"]
        last_update = data["query"]["pages"][0]["revisions"][0]["revid"]        
        content = data["query"]["pages"][0]["revisions"][0]["slots"]["main"]
        last_update = data["query"]["pages"][0]["revisions"][0]["revid"]
        return content, last_update
    # If the request failed, print an error message and return None
    else:
        print(colored(f"ERROR: Request failed with status code: {response.status_code}.\nCheck if API/Wiki is down.","red"))
        return None, None


def extract_effects(param, effects):
    # Find the portion of the string between {{IL| and }}
    param_name = param.name.strip()
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
        # If the value is just a 10% increase/decrease, then the rate is not needed.
        menace_effect_match = re.search(r"{{Menace Effect\|(.*?)\|(increase|decrease)?(\|rate=(\d+))?}}", str(param.value))
        if menace_effect_match:
            # Get name of the menace, will catch anything with "Menace Effect" example: ["Nightmares", "Scandal", "Suspicion", "Wounds"]
            effect_name = menace_effect_match.group(1)
            # Check if thid matches the "increase/decrease". If nothing, assume decrease.
            action = menace_effect_match.group(2) or "decrease" 
            # Default rate is 10 and doesnt need to be specified. 
            # If the rate is higher, this should catch that extra value and assign the correct sign.
            if menace_effect_match.group(4):
                rate = menace_effect_match.group(4)
                if action == "decrease":
                    effect_value = -int(rate)
                else:
                    effect_value = int(rate)
            else:
                # If the action was increase, then value is 10. If decrease, then -10.
                effect_value = 10 if action == "increase" else -10
        else:
            print(colored(f"ERROR: In {param_name} can't find the name or value","red"))
            effect_name = effect_value = None
    if effect_name:
        effects[effect_name] = effect_value

# Function to extract the effects from the page content
def extract_page_info(page_content, extra_categories):
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
    retired = False

    wikilinks = parsed_wikitext.filter_wikilinks()
    categories = [link.title.strip() for link in wikilinks if link.title.startswith("Category:")]
    
    jobs = ["Campaigner","Enforcer","Rat-Catcher","Trickster","Journalist","Watcher","Tough","Minor Poet","Pickpocket","Enquirer","Author","Murderer","Stalker","Agent","Mystic","Conjurer","Tutor","Undermanager","Correspondent","Licentiate","Monster-Hunter","Midnighter","Silverer","Crooked-Cross","Notary","Doctor"]
    set_jobs = set("Category:" + job for job in jobs)
    # Creates a few Categories that will be avoided later.
    item_rarity = set("Category:" + item for item in ["Precious", "Rare", "Coveted", "Scarce", "Commonplace"])
    item_categories = set(["Category:Boon","Category:Hat","Category:Clothing","Category:Gloves","Category:Weapon","Category:Boots","Category:Companion","Category:Destiny","Category:Spouse","Category:Treasure","Category:Tools_of_the_Trade","Category:Affiliation","Category:Transport","Category:Home_Comfort","Category:Ship","Category:Club"])
    unwanted_categories = item_rarity | item_categories

    #Look through the categories and apply Fate to true if Category:Fate exists, or set origin to: Fate Story if Category:Fate Story Items exists
    if extra_categories:
        for extra_category in extra_categories:
            if extra_category['title'] == "Category:Fate Story Items":
                origin = "Fate Story"
            elif extra_category['title'] == "Category:Fate":
                fate = True
            elif extra_category['title'] == "Category:Retired":
                retired = True
            # elif extra_category['title'] == "Category:Chirurgical Touch Items":
            #     origin = "Great Hellbound Railway"

    for template in templates:
        if template.name.strip() == "Item":
            for param in template.params:
                # print(param)
                param_name = param.name.strip()
                # if the param_name is description, just continue to the next item.
                if param_name == "Description" or param_name == "Item Type" or param_name == "Buying/Selling":
                    continue
                elif param_name == "ID":
                    if param.value.strip().isdigit():
                        ID = int(param.value.strip())
                    else:
                        ID = None
                elif param_name == "Icon":
                    icon = str(param.value.strip())
                    #Make the first letter lowercase
                    if icon[0].isupper():
                        icon = icon[0].lower() + icon[1:]
                    icon = icon.replace(" ", "_")
                elif param_name == "Origin": origin = str(param.value.strip())
                elif param_name == "Access": 
                    access = str(param.value.strip())
                    if access == "Retired": retired = True
                elif param_name == "Access info":
                    access_info = str(param.value.strip()).replace(" (Guide)", "")  # Remove (Guide) if present
                
                    # For some reason, the wiki is not consistent with the naming, so add the full name to this:
                    if access_info == "Feast of the Rose":
                        access_info = "Feast of the Exceptional Rose"

                    # if the item is retired, from the access, then append "Retired" to the access info. First check if it starts with the word "Retired"
                    # if not access_info.startswith("Retired") and access == "Retired":
                    #         access_info = "Retired: " + access_info
                elif param_name == "Shop": shop = str(param.value.strip())
                elif param_name == "Upper Shop": shop = str(param.value.strip()) + " (Upper River)"
                elif param_name == "Rat Shop": shop = str(param.value.strip()) + " (The Rat Market)"
                elif param_name == "Khanate Shop": shop = str(param.value.strip()) + " (Khaganian Markets)"
                # Checks if the categories already set Fate, and if not, then check if content has Fate value.
                elif fate is None and param_name == "Fate":
                    fate_value = str(param.value.strip()).lower()
                    fate = True if fate_value == "yes" else False

                # Extract each of the "Effects", which are the stats.
                if param_name.startswith("Effects"):
                    param_name = param.name.strip()
                    match_effect_name = re.search(r"{{IL\|(.*?)}}", str(param.value))
                    if match_effect_name == "Chirurgical Touch":
                        origin = "Great Hellbound Railway"
                    extract_effects(param, effects)


            if shop != None:
                if origin is None:
                    origin =  "Shop: " + str(shop)
                if shop == "Mr Chimes' Lost & Found":
                    fate = True
            if origin is None:
                if access is not None:
                    # if origin is not None:
                    #     print(f"DEBUG: ORIGIN IS NOT NONE. Origin: {origin}")
                    if access == "Festival":
                        if origin is not None:
                            origin = re.sub(r" \(Guide\)", "", origin)
                        elif access_info is not None:
                            origin = access_info
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
                    elif access_info is not None:
                        origin = access_info
                
            elif not origin and access == "Festival": # This might be redundant, but lets keep it...
                    origin = access_info


            for idx, category in enumerate(categories):
                sanitized_category = category.replace("Category:", "").replace(" Items", "").replace(" Equipment", "")
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
                    if not origin:
                        origin = category.replace("Category:", "")
                    # origin = "Retired: " + origin.strip()
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
    return effects, origin, fate, ID, icon, retired

def sanitize_column_name(name):
    sanitized_name = re.sub(r'\W|^(?=\d)','_', name)
    return sanitized_name.rstrip('_')

def create_database():
    # Get the absolute path
    full_db_path = os.path.abspath(DB_PATH)
    print(f"Connecting to database at: {full_db_path}")

    # Connect to the SQLite database
    conn = sqlite3.connect(full_db_path)
    cursor = conn.cursor()

    # Create the "items" table if it doesn't already exist
    # Generate the SQL to create the table
    COLUMNS = ["ID INTEGER PRIMARY KEY UNIQUE", # This will make ID the primary key and unique
                "page_id INTEGER",
                "last_update TEXT", 
                "category TEXT", 
                "title TEXT",
                "have BOOLEAN",
                "origin TEXT", 
                "fate BOOLEAN",
                "retired BOOLEAN",
                "icon TEXT"]

    for effect_name in effect_names:
        COLUMNS.append(f"{sanitize_column_name(effect_name)} INTEGER")
    create_table_sql = "CREATE TABLE IF NOT EXISTS items (" + ", ".join(COLUMNS) + ")"
    cursor.execute(create_table_sql)

    return conn, cursor

def update_or_insert_item(cursor, values, db_id, db_page_id, db_last_update):
    #Does this item ID exist in the database?
    page_id = values["page_id"]
    last_update = values["last_update"]
    title = values["title"]
    if db_id and values["ID"] == db_id:
        #Does this ID have the same page_id?
        if page_id != db_page_id or OVERWRITE_ALL:
            # Need to update the database's page_id.
            values_without_have = {key: values[key] for key in values if key != "have"}
            sql_update = "UPDATE items SET " + ", ".join(f"{key} = ?" for key in values_without_have) + " WHERE ID = ?"
            cursor.execute(sql_update, list(values_without_have.values()) + [values["ID"]])

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
                infoStatus["infoSkipped"] +=1
                return
            # now if the if statement returns false, we need to update the database.
            else:
                print(colored("ERROR: ID and page_id is the same, but there was an error with last_update.","red"))
                infoStatus["infoError"] +=1
                return
        else:
            print(colored("ERROR: ID Found, but there was an error with page_id.","red"))
            infoStatus["infoError"] +=1

    # Item ID doesn't exist in the database. Its a New Item!
    else:  
        # Construct the SQL insert statement
        COLUMNS = ", ".join(values.keys())
        placeholders = ", ".join("?" for _ in values)

        sql_insert = f"INSERT INTO items ({COLUMNS}) VALUES ({placeholders})"
        cursor.execute(sql_insert, list(values.values()))
        print(colored("INFO: *** New Item! Adding. ***",'green'))
        infoStatus["infoNew"]["total"] +=1


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    # Load the effect names from the file
    with open('effectNames/effectNames.json', 'r') as f:
        global effect_names
        effect_names = json.load(f)
        sanitized_effect_names = {effect_name: sanitize_column_name(effect_name) for effect_name in effect_names}

    # Create the database if it doesn't already exist
    conn, cursor = create_database()

    # Loop over each category (ie Category:Boots)
    for category in api_categories:
        # Remove the "Category:" prefix from the category name
        category_name = category.replace("Category:", "")

        print(dashes + "Looking through Category:" + category_name + "\n" +dashes)

        # Get the items in the category. items = list of items for the category.
        items = fetch_category_members(category)
        infoStatus["totalItems"][category] += len(items)

        for i in range(0, len(items), 50):
            batch = items[i:i + 50]
            page_ids = [item.get("pageid", None) for item in batch]
            
            # Fetch the batch data
            batch_data = fetch_items_batch(page_ids)

            # Loop over each item
            if batch_data:
                for item in batch_data:
                    title = item["title"]
                    # Use get method to fetch ID and default to None if not found
                    page_id = item.get("pageid", None)
                    extra_categories = item.get("categories", None)

                    # If the item doesn't have an ID or is in the skip list, continue to the next iteration
                    if title in SKIP_ITEMS:
                        print(colored(f"INFO: SKIPPING Known Item with no ID: {title}","yellow"))
                        infoStatus["infoSkipped"] +=1
                        continue

                    print("Item name: " + title)
                    print("Item ID: " + str(item))

                    # Get the content of the item's page
                    # content_data, last_update = get_page_content(page_id)
                    content_data, last_update = item["revisions"][0]["slots"]["main"], item["revisions"][0]["revid"]


                    # if content_data:
                    # Extract the DISPLAYTITLE value from the page content, if available
                    # The only case I've seen so far is for "M. D_____' A_____ for _______: F____ Edition", but there may be others in the future!
                    
                    display_title_pattern = re.compile(r"{{DISPLAYTITLE:(.*?)}}")
                    match = display_title_pattern.search(content_data['content'])
                    if match:
                        title = match.group(1).strip()
                        print(colored(f"INFO: Changed Item name to Wiki display name: {title}","yellow"))

                    # print(page_content)
                    # If the page content was successfully retrieved, extract the effects
                    # Extract the effects from the page content
                    effects, origin, fate, ID, icon, retired = extract_page_info(content_data, extra_categories)
                    have = None
                    db_id, db_page_id, db_last_update = None, None, None
                    # If we dont have the ID, skip this item.
                    if not ID:
                        print(colored(f"INFO: SKIPPING. UNKNOWN ITEM: *** NO ID in Wiki. Item: {title} ***","yellow"))
                        infoStatus["infoSkipped"] +=1
                        continue

                    # Now we assume the item has an ID.
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
                        "have": have,
                        "origin": origin,
                        "fate": fate,
                        "retired": retired,
                        "last_update": last_update,
                        "icon": icon
                    }

                    # Add all effect names to the item dictionary, to add to the database. If the effect is not found, then it will be None.
                    for effect_name in effect_names:
                        sanitized_name = sanitized_effect_names[effect_name]
                        values[sanitized_name] = effects.get(effect_name, None)

                    # Update or insert the item into the database
                    update_or_insert_item(cursor, values, db_id, db_page_id, db_last_update)

        
    # Commit the changes and close the connection to the database
    conn.commit()
    conn.close()


# If the script is run directly (not imported as a module), call the main function
if __name__ == "__main__":
    main()

    print(dashes + "DONE!\n" + dashes)
    if infoStatus["infoError"] > 0: 
        print(f"Errors: {infoStatus['infoError']}")
    else:
        print("No Errors.")
    print(f"{dashes}Skipped Items:\t{infoStatus['infoSkipped']}")
    print(f"New Items:\t{infoStatus['infoNew']['total']}")
    if infoStatus["infoNew"]["total"] > 0:
        for each in infoStatus["infoNew"]["item_name"]:
            print(colored(f"\tNew Item: {each}", "green"))
    print(f"API Calls: \t {infoStatus['APICalls']}")

    print(f"{dashes}Total item counts by Category:")
    for category, count in infoStatus["totalItems"].items():
        print(f"    {category} = \t{count}")