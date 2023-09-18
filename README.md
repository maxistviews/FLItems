# FLItems
A script to record all items available in the FLWiki into a simple SQLite database.
Using this to better understand my items, which are best in slot (BIS) and help me learn Python!

# Instructions
Download all the files presented to you here.
Navigate to your Fallen London Items page, and open Developer Tools. Go to the Network tab and reload the page. Within the list, there should be a file called `myself`. Copy the response into the `myself.json` file at the root of the directory (replace the default one I've given you). 
Now run `CharacterCruncher.py`. This will look through your character's items and check off which ones you have into the `items.db` database.
Now you can launch `webpage.py` from the itemViewer folder. This will launch a Flask server so that you can view your items. Navigate to the link presented.

Right now, running the Flask Server will give you something like this:

![image](https://github.com/maxistviews/FL_Items/assets/17325179/3e2587fb-5f09-41b0-8090-9675ba0a9d3f)


Built on Python 3.11.4


Currently, I am using this to browse the data:
https://sqlitebrowser.org/

Please do not abuse.
