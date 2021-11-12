import requests
import json
import random
import math
import database
import asyncio

def convertToDBModel(result):
    final_dict = {}
    final_dict["name"] = result['name']
    final_dict["place_id"] = result['place_id']
    if 'price_level' in result.keys():
        final_dict["price_level"] = result['price_level']
    if 'rating' in result.keys():
        final_dict["rating"] = result['rating']
    final_dict["types"] = result['types']
    if 'user_ratings_total' in result.keys():
        final_dict["user_ratings_total"] = result['user_ratings_total']
    final_dict["location"] = result['geometry']['location']
    final_dict["instantaneous_dist"] = calculate_dist(loc, result['geometry']['location'], 3)
    return final_dict

def calculate_dist(curr_loc, result, rounded_digits):
    lat_init, lon_init = map(float, curr_loc.split("%2C"))
    lat_final = float(result['lat'])
    lon_final = float(result['lng'])
    del_phi = ((lat_final - lat_init) * math.pi / 360)
    del_lambda = ((lon_final - lon_init) * math.pi / 360)
    a = ((math.sin(del_phi))**2) + (math.cos(lat_init)*math.cos(lat_final)*(math.sin(del_lambda))**2)
    c = 2 * math.atan2(a**(1/2), (1-a)**(1/2))
    return round(6371 * c, rounded_digits)

async def insert_records_into_db(index):
    db = (await database.get_client())
    user_event_history = db['user_event_history']
    await user_event_history.insert_many(index)
    return
    

PLACES_API_KEY = "<YOUR_API_KEY>"

request_str = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?"
types = ["restaurant", "museum", "zoo", "amusement_park", "aquarium", "art_gallery", "night_club", "bar", "bakery", "book_store", "tourist_attraction", "shopping_mall", "park", "movie_theater"]
loc = "33.748550%2C-84.391502"
radius = "5000"
parameters = "location={}&radius={}&type={}&key={}"
parameter_next = "location={}&radius={}&type={}&key={}&next_page_token={}"
usernames = [ "ymahapatra", "vneal" ]
num_rand_events = 5
indexing_array = []
for i in range(len(usernames)):
    indexing_array.insert(len(indexing_array), {})
    indexing_array[i]['username'] = usernames[i]
    indexing_array[i]['event_history'] = []
place_ids = []

for i in range(len(usernames)):
    for type in types:
        res = requests.get(request_str + parameters.format(loc, radius, type, PLACES_API_KEY))
        results = json.loads(res.content.decode('utf-8'))
        next_token = ""
        if 'next_page_token' in results.keys():
            next_token = results['next_page_token']
        for _ in range(num_rand_events):
            if(len(results['results']) == 0):
                continue
            rand_selection = random.randint(0, min(20, len(results['results']) - 1))
            place_id = results['results'][rand_selection]['place_id']
            if place_id in place_ids:
                continue
            place_ids.insert(len(place_ids), place_id)
            indexing_array[i]['event_history'].insert(len(indexing_array[i]['event_history']), convertToDBModel(results['results'][rand_selection]))
            res = requests.get(request_str + parameter_next.format(loc, radius, type, PLACES_API_KEY, next_token))
            results = json.loads(res.content.decode('utf-8'))
            if 'next_page_token' in results.keys():
                next_token = results['next_page_token']
            else:
                break
loop = asyncio.get_event_loop()
loop.run_until_complete(insert_records_into_db(indexing_array))