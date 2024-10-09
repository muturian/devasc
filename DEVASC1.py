###############################################################
# This program:
# - Asks the user to enter an access token or use the hard-coded access token.
# - Lists the user's Webex rooms.
# - Asks the user which Webex room to monitor for "/seconds" of requests.
# - Monitors the selected Webex Team room every second for "/seconds" messages.
# - Discovers GPS coordinates of the ISS flyover using ISS API.
# - Displays the geographical location using Bing Maps API based on the GPS coordinates.
# - Formats and sends the results back to the Webex Team room.
###############################################################

# 1. Import libraries for API requests, JSON formatting, epoch time conversion, and iso3166.

import requests
import json
import time
import os
import iso3166

# 2. Complete the if statement to ask the user for the Webex access token.
choice = input("Do you wish to use the hard-coded Webex token? (y/n) ")

if choice.lower() == "n":
    accessToken = input("What is your Webex access token? ")
    accessToken = "Bearer " + accessToken
else:
    accessToken = "Bearer " + os.getenv("WEBEX_ACCESS_TOKEN", "YOUR_HARDCODED_TOKEN")

# 3. Provide the URL to the Webex room API.
r = requests.get("https://webexapis.com/v1/rooms", headers={"Authorization": accessToken})

#######################################################################################
# DO NOT EDIT ANY BLOCKS WITH r.status_code
if r.status_code != 200:
    raise Exception("Incorrect reply from Webex API. Status code: {}. Text: {}".format(r.status_code, r.text))
#######################################################################################

# 4. Create a loop to print the type and title of each room.
print("\nList of available rooms:")
rooms = r.json()["items"]
for room in rooms:
    print("Type: '" + room["type"] + "' Name: " + room["title"])

#######################################################################################
# SEARCH FOR WEBEX ROOM TO MONITOR
#######################################################################################

while True:
    roomNameToSearch = input("Which room should be monitored for the /seconds messages? ")
    roomIdToGetMessages = None

    for room in rooms:
        if roomNameToSearch.lower() in room["title"].lower():
            print("Found room with the word " + roomNameToSearch)
            print(room)
            roomIdToGetMessages = room["id"]
            roomTitleToGetMessages = room["title"]
            print("Found room: " + roomTitleToGetMessages)
            break

    if roomIdToGetMessages is None:
        print("Sorry, I didn't find any room with " + roomNameToSearch + " in it.")
        print("Please try again...")
    else:
        break

#######################################################################################
# WEBEX BOT CODE - Start Webex bot to listen for and respond to /seconds messages.
#######################################################################################

while True:
    time.sleep(1)
    GetParameters = {
        "roomId": roomIdToGetMessages,
        "max": 1
    }
    
    # 5. Provide the URL to the Webex messages API.
    r = requests.get("https://webexapis.com/v1/messages", params=GetParameters, headers={"Authorization": accessToken})

    # Verify if the returned HTTP status code is 200/OK
    if r.status_code != 200:
        raise Exception("Incorrect reply from Webex API. Status code: {}. Text: {}".format(r.status_code, r.text))

    json_data = r.json()
    if len(json_data["items"]) == 0:
        print("No new messages in the room.")
        continue

    messages = json_data["items"]
    message = messages[0]["text"]
    print("Received message: " + message)

    if message.startswith("/") and message[1:].isdigit():
        seconds = int(message[1:])
    else:
        raise Exception("Incorrect user input.")
    
    # For testing, the max number of seconds is set to 5.
    if seconds > 5:
        seconds = 5
    
    time.sleep(seconds)

    # 6. Provide the URL to the ISS Current Location API.
    r = requests.get("http://api.open-notify.org/iss-now.json")
    if r.status_code != 200:
        raise Exception("Failed to retrieve ISS data. Status code: {}".format(r.status_code))

    json_data = r.json()

    if json_data["message"] != "success":
        raise Exception("Incorrect reply from Open Notify API.")

    # 7. Record the ISS GPS coordinates and timestamp.
    lat = json_data["iss_position"]["latitude"]
    lng = json_data["iss_position"]["longitude"]
    timestamp = json_data["timestamp"]

    # 8. Convert the timestamp epoch value to a human-readable date and time.
    timeString = time.ctime(timestamp)

    # 9. Use the Bing Maps API to reverse geocode the ISS location.
    bing_maps_key = os.getenv("BING_MAPS_API_KEY", "YOUR_BING_MAPS_API_KEY")
    bingmapsParameters = {
        "q": f"{lat},{lng}",
        "key": bing_maps_key
    }
    r = requests.get("https://dev.virtualearth.net/REST/v1/Locations", params=bingmapsParameters)

    if r.status_code != 200:
        raise Exception("Failed to retrieve location from Bing Maps API. Status code: {}".format(r.status_code))

    bing_data = r.json()

    if len(bing_data["resourceSets"]) == 0 or len(bing_data["resourceSets"][0]["resources"]) == 0:
        raise Exception("No location data found in Bing Maps API response.")

    location = bing_data["resourceSets"][0]["resources"][0]["address"]

    street = location.get("addressLine", "Unknown")
    city = location.get("locality", "Unknown")
    state = location.get("adminDistrict", "Unknown")
    country_code = location.get("countryRegion", "Unknown")

    country = iso3166.countries.get(country_code)
    country_name = country.name if country else "Unknown"

    # 10. Complete the code to format the response message.
    if country_name == "Unknown":
        responseMessage = f"On {timeString}, the ISS was flying over a body of water at latitude {lat}° and longitude {lng}°."
    else:
        responseMessage = f"In {city}, {state}, {country_name}, the ISS flew over on {timeString} for {seconds} seconds."

    # Print the response message
    print("Sending to Webex: " + responseMessage)

    # 11. Complete the code to post the message to the Webex room.
    HTTPHeaders = {
        "Authorization": accessToken,
        "Content-Type": "application/json"
    }

    PostData = {
        "roomId": roomIdToGetMessages,
        "text": responseMessage
    }

    # Post the call to the Webex message API.
    r = requests.post("https://webexapis.com/v1/messages", data=json.dumps(PostData), headers=HTTPHeaders)
    if r.status_code != 200:
        raise Exception("Incorrect reply from Webex API. Status code: {}. Text: {}".format(r.status_code, r.text))
