import requests
import json

SKIP_ATTRIBUTES = ["Aerial Armament", "Aerial Prowess", "Cat Upon Your Person"]

def get_effect_names():
    # The base URL of the API endpoint
    url = "https://fallenlondon.wiki/w/api.php"

    # The parameters for the API request
    params = {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "rvslots": "main",
        "indexpageids": 1,
        "formatversion": "2",
        "cmtitle": "Category:Attributes"
    }

    # A list to store the effect names
    effect_names = []

    # Loop until all pages of results have been fetched
    while True:
        # Make the API request
        response = requests.get(url, params=params)

        # Parse the JSON response
        data = response.json()

        # Extract the effect names from this page of results and add them to the list
        for category in data["query"]["categorymembers"]:
            if category["title"] not in SKIP_ATTRIBUTES:
                effect_names.append(category["title"])
        
        # Old code for before I included SKIP_ATTRIBUTES. It's not needed anymore, but I'm keeping it here just in case.
        #effect_names.extend(page["title"] for page in data["query"]["categorymembers"])

        # If there's a 'continue' field in the response, update the parameters with it to get the next page of results
        if "continue" in data:
            params.update(data["continue"])
        # Otherwise, all pages of results have been fetched, so break the loop
        else:
            break
    
    # Adds the menaces that can also be modified by clothing
    effect_names.extend(['Troubled Waters','Nightmares','Scandal','Suspicion','Wounds'])

    # Write the list of effect names to a file
    with open('effectNames.json', 'w') as f:
        json.dump(effect_names, f)


    print(effect_names)

if __name__ == "__main__":
    get_effect_names()