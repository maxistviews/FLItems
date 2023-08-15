# stats_group = [
#     ["Watchful", "Shadowy", "Dangerous", "Persuasive","Bizarre", "Dreaded", "Respectable", "A_Player_of_Chess", "Artisan_of_the_Red_Science", "Glasswork", "Kataleptic_Toxicology", "Mithridacy", "Monstrous_Anatomy", "Shapeling_Arts", "Zeefaring", "Neathproofed", "Steward_of_the_Discordance"]
# ]
from itertools import product

main_stats = ["Watchful", "Shadowy", "Dangerous", "Persuasive"]
rep_stats = ["Bizarre", "Dreaded", "Respectable"]
advanced_stats= ["A_Player_of_Chess", "Artisan_of_the_Red_Science", "Glasswork", "Kataleptic_Toxicology", "Mithridacy", "Monstrous_Anatomy", "Shapeling_Arts", "Zeefaring", "Neathproofed", "Steward_of_the_Discordance"]
menace_stats= ["Nightmares", "Scandal", "Suspicion", "Wounds"]
old_stats=["Savage", "Elusive", "Baroque", "Cat_Upon_Your_Person"]

# 25 groups in total

stat_group = main_stats + rep_stats + advanced_stats + menace_stats + old_stats
# stat_comma = main_stats,rep_stats,advanced_stats,menace_stats,old_stats

# print(len(stat_group))

changeable_categories = ["Hat","Clothing","Gloves","Weapon","Boots","Companion","Affiliation","Transport","Home_Comfort"]
static_categories = ["Spouse","Treasure","Destiny","Tools_of_the_Trade","Ship","Club"]

item_type = ["have_item","free_item","all_item"]

table_dictionary = {
    "Changeable": {},
    "Static":{}
}

# table_dictionary_ref = {
#     "Changeable": {
#         "Hat" : {
#             "Watchful": {
#                 # Top item in this category in the database that has have=1
#                 "have":{
#                     "item_name" : "",
#                     "value" : 0,
#                     "origin" : "",
#                     "icon" : "",
#                     "color" : ""
#                 },
#                 # Top item in this category in the database that has fate=0
#                 "free_items": {
#                     "item_name" : "",
#                     "value" : 0,
#                     "origin" : "",
#                     "icon" : ""
#                 },
#                 # Top item in this category in the database, no matter the fate.
#                 "all_items": {
#                     "item_name" : "",
#                     "value" : 0,
#                     "origin" : "",
#                     "icon" : ""
#                 }
#             }
#         }
#     },
#     "Static": {
#         "Spouse" : {
#             "Watchful": {
#                 # Top item in this category in the database that has have=1
#                 "have":{
#                     "item_name" : "",
#                     "value" : 0,
#                     "origin" : "",
#                     "icon" : "",
#                     "color" : ""
#                 },
#                 # Top item in this category in the database that has fate=0
#                 "free_items": {
#                     "item_name" : "",
#                     "value" : 0,
#                     "origin" : "",
#                     "icon" : ""
#                 },
#                 # Top item in this category in the database, no matter the fate.
#                 "free_items": {
#                     "item_name" : "",
#                     "value" : 0,
#                     "origin" : "",
#                     "icon" : ""
#                 }
#             }
#         }
#     }
# }

# First time this runs, is_static = False. Second time, its true.
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

print(len(table_dictionary))