# def set_colors_old(fate_value=None):
#     # Take the color list we made and for each color, item-value-color-#
#     for i in range(len(color_list)):
#         color_dic[f"item-value-color-{i}"] = str(color_list[i])
    
#     # For each item category in all item categories, check each stat and compare it to the compare value.
#     for category in all_categories:
#             for stat in stat_group:
#                 if fate_value == 0:
#                     item_key = "free_item"
#                 else:
#                     item_key = "all_item"

#                 # Get the value of the stat for the item
#                 stat_shortcut = table_dictionary["Changeable" if category in changeable_categories else "Static"][category][stat]
#                 compare_value = stat_shortcut[item_key]["value"]
#                 have_value = stat_shortcut["have_item"]["value"]
#                 # if have_value == 0:
#                 #     have_value =1
#                 # Divide the have_value by the compare value. This will give you a %. The closer to 100% (1.0), the closer to green you are.
#                 if compare_value == 0:
#                     have_vs_compare = 10
#                 else:
#                     have_vs_compare = round(have_value / compare_value * 10)
#                     if have_vs_compare >=11:
#                         have_vs_compare = 10

#                     # have_vs_compare = have_value % compare_value

#                 stat_shortcut["have_item"]["color"] = color_dic[f'item-value-color-{have_vs_compare}']
                

#                 print(f"For {category} with: '{stat}' {have_value} / {compare_value} = {have_vs_compare}")
#                 print(f"Assigned colour {str(color_list[have_vs_compare])} to it. {have_vs_compare}th color.")


# def populate_dictionary_old(category, stat, have_value, fate_value, title, value, origin, icon):
#     """
#     Populates the table dictionary based on the category, stat, have_value, and fate_value.
#     TODO: Adjust this to only have a compare_item entry. Probaly replace the fate_value key also thats being passed.
#     update the functions to be "refresh_table" instead of create_table ?
#     """
#     #This is the basic item dictionary shared between all items.
#     item_dict = {
#         "item_name": title,
#         "value": value,
#         "origin": origin,
#         "icon": icon
#         }
    
#     if have_value == 1:
#         item_key = "have_item"
#         item_dict["color"] = ""  # This will be updated later when comparing values
#     elif fate_value == 0:
#         item_key = "free_item"
#     else:
#         item_key = "all_item"
        
#     # Now, populate the table_dictionary
#     table_dictionary["Changeable" if category in changeable_categories else "Static"][category][stat][item_key] = item_dict


# def update_table_old(totals, have_value=None, fate_value=None, compare_table=None):
#     """"""

#     """"""
#     # Connect to the database
#     conn = sqlite3.connect(DATABASE)
#     cursor = conn.cursor()

#     # Determine the item_key for populate_dictionary
#     if have_value is not None:
#         item_key = "have_item"
#     elif fate_value is not None:
#         if fate_value == 0:
#             item_key = "free_item"
#         else:
#             item_key = "all_item"
#     else:
#         # This is the compare_item case, determine the key based on compare_table
#         item_key = compare_table

#     try:
#         for category in all_categories:
#             for stat in stat_group:
#                 query = f"SELECT title, \"{stat}\", origin, icon FROM items WHERE category = '{category}'"

#                 if item_key == "have_item":
#                     query += f" AND have = 1"
#                 elif item_key == "free_item":
#                     query += f" AND fate = 0"
#                 elif item_key == "all_item":
#                     # No additional conditions for all items
#                     pass

#                 query += f" ORDER BY \"{stat}\" DESC LIMIT 1"

#                 try:
#                     cursor.execute(query)
#                 except sqlite3.Error as e:
#                     print(f"SQL error: {e}")
#                     # Handle the error appropriately. Maybe continue to the next iteration or exit the function.

#                 result = cursor.fetchone()

#                 if result:
#                     title, value, origin, icon = result
#                     icon = smallify_icons(icon)
#                     if not value or value <= 0:
#                         icon = "blanksmall.png",
#                         title = "----"
#                         origin = ""
#                         value = 0
#                     #Now that it is iconsmall.png, lets download it:
#                     download_icon(icon)
#                     if item_key == "have_item":
#                         totals[stat] += value
#                     populate_dictionary(category, stat, have_value, fate_value, title, value, origin, icon)
#                 else:
#                     icon = "blanksmall.png"
#                     title = "----"
#                     origin = ""
#                     value = 0
#                     #Now that it is iconsmall.png, lets download it:
#                     download_icon(icon)
#                     populate_dictionary(category, stat, have_value, fate_value, title, value, origin, icon)

#     except sqlite3.Error as e:
#         print(f"SQL error: {e}")
#     finally:
#         conn.close()