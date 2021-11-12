import json
import math
import random
from typing import List, Dict
import copy

import database
from fastapi import FastAPI, Response
import aiohttp

from models import RecommendationAcceptRequest, RecommendationRequest
from fastapi.middleware.cors import CORSMiddleware

PLACES_API_KEY = ""
RECOMMENDED = 'recommended'

app = FastAPI()
db = ""
api_key = ""
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def init_server():
    global db 
    db = (await database.get_client('reco_engine'))['user_event_history']
    global api_key
    api_key = (await (await database.get_client('api_keys'))['api_keys'].find_one({'api_key': { '$exists': 'true' }}))['api_key']
    global PLACES_API_KEY
    PLACES_API_KEY = (await (await database.get_client('api_keys'))['api_keys'].find_one({'places_api_key': { '$exists': 'true' }}))['places_api_key']

async def getPlacesResponse(searchCategory: str, radius: float, location: Dict[str, float], places: List[List[Dict]], index: int):
    baseurl = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?"
    parameters = "location={}&radius={}&type={}&key={}".format(str(location['lat'])+"%2C"+str(location['lon']), str(radius), searchCategory, PLACES_API_KEY)
    async with aiohttp.ClientSession() as session:
        async with session.get(baseurl + parameters) as response:
            results = json.loads(await response.text())
            places[index].extend(results['results'])
    return

def dot_product(event: Dict, place: Dict):
    event_types = event['types']
    place_types = place['types']
    counter = 0
    for place_type in place_types:
        if place_type in event_types:
            counter += 1
    return counter

def convertToRecommendationResponseModel(recommendationsReceived: List[Dict]):
    converted_recommendations = []
    for recommendation in recommendationsReceived:
        temp = {}
        temp["name"] = recommendation['name']
        temp["place_id"] = recommendation['place_id']
        if "rating" in recommendation.keys():
            temp['rating'] = recommendation['rating']
        if "user_ratings_total" in recommendation.keys():
            temp['user_ratings_total'] = recommendation['user_ratings_total']
        temp['distance'] = recommendation['instantaneous_dist']
        converted_recommendations.append(temp)
    return converted_recommendations

def convertToDBModel(curr_location: Dict, result: Dict):
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
    final_dict["instantaneous_dist"] = calculate_dist(curr_location, result['geometry']['location'], 3)
    return final_dict

def calculate_dist(curr_loc: Dict[str, float], result, rounded_digits):
    lat_init = curr_loc['lat']
    lon_init = curr_loc['lon']
    lat_final = float(result['lat'])
    lon_final = float(result['lng'])
    del_phi = ((lat_final - lat_init) * math.pi / 360)
    del_lambda = ((lon_final - lon_init) * math.pi / 360)
    a = ((math.sin(del_phi))**2) + (math.cos(lat_init)*math.cos(lat_final)*(math.sin(del_lambda))**2)
    c = 2 * math.atan2(a**(1/2), (1-a)**(1/2))
    return round(6371 * c, rounded_digits)

def euclidean_dist(place: Dict, event: Dict):
    del_price_level = 0
    del_rating = 0
    if 'price_level' in place.keys() and 'price_level' in event.keys():
        del_price_level = place['price_level'] - event['price_level']
    if 'rating' in place.keys() and 'rating' in event.keys():
        del_rating = place['rating'] - event['rating']
    del_instantaneous_dist = place['instantaneous_dist'] - event['instantaneous_dist']
    return (del_price_level**2 + del_rating**2 + del_instantaneous_dist**2)**0.5

def evaluateRecommendations(curr_location: Dict[str, float], event_history: List[Dict], places: List[List]):
    # Convert to DB model. For each list in places do dot product with each in event_history.
    # Now consider only those with dot product > 2 and group these from event_history and recommendations. 
    # If there are no recommendations inside a particular type which were able to satisy the dot product rule,
    # then do random selection for that category because this implies that user has never gone to that place type
    for i in range(len(places)):
        for j in range(len(places[i])):
            places[i][j] = convertToDBModel(curr_location, places[i][j])
    type_correlation = []
    for place_list in places:
        type_correlation.append({})
        type_correlation[len(type_correlation) - 1]['event_history'] = []
        type_correlation[len(type_correlation) - 1]['correlation'] = []
        for event in event_history:
            for place in place_list:
                if dot_product(event, place) > 2:
                    type_correlation[len(type_correlation) - 1]['event_history'].append(event)
                    type_correlation[len(type_correlation) - 1]['correlation'].append(place)
    # Dot product > 2 aims at reducing the cosine distance based on the type of place already visited anf trying to visit.
    # Now among available calulate the euclidean distance. And use the topmost result from each type_correlation
    final_recommendations = []
    for i in range(len(type_correlation)):
        if len(type_correlation[i]['correlation']) == 0 and len(places[i]) > 0:
            rand_selection = random.randint(0, len(places[i]) - 1)
            final_recommendations.append(places[i][rand_selection])
            continue
        
        distance_sum = math.inf
        type_reco = {}
        for place in type_correlation[i]['correlation']:
            local_sum = 0
            for event in type_correlation[i]['event_history']:
                local_sum += euclidean_dist(place, event)
            if local_sum < distance_sum:
                distance_sum = local_sum
                type_reco = place
        final_recommendations.append(type_reco)
    return final_recommendations

def validateAPIKey(key: str):
    if api_key == key:
        return
    else:
        return Response(content = json.dumps({ "errorList": [ "API_KEY not found" ]}), media_type = "application/json")    

@app.get("/", status_code = 200)
async def root():
    return {"message": "You have reached the backend of recommendation algo created as part of Gatech RTES 6235/4220"}

@app.post("/getRecommendations/{username}", status_code = 200)
async def getRecommendations(*, username: str, key: str, recommendationRequest: RecommendationRequest):
    # Get first 10 results (by prominence) of each type. Use aynscio here to make multiple requests to the API to improve latency.
    # Each of this is evaluated against the event_history of the user and top recommendation selected.
    # Response contains all the top results from each category to be presented to the user.
    res = validateAPIKey(key)
    if res != None:
        return res
    places = []
    user_data = await db.find_one({"username": username})
    old_id = user_data['_id']
    for _ in range(len(recommendationRequest.search_categories)):
        places.insert(len(places), [])
    for i in range(len(recommendationRequest.search_categories)):
        await getPlacesResponse(recommendationRequest.search_categories[i], recommendationRequest.radius, recommendationRequest.location, places, i)
    
    # First time user
    if len(user_data['event_history']) == 0:
        recommendations = []
        for place in places:
            rand_selection = random.randint(0, len(place) - 1)
            if RECOMMENDED not in user_data.keys():
                user_data[RECOMMENDED] = []
            if len(place) > 0:
                recommendations.append(convertToDBModel(recommendationRequest.location, place[rand_selection]))
        user_data[RECOMMENDED].extend(recommendations)
        await db.replace_one({"_id": old_id}, user_data)
        return convertToRecommendationResponseModel(recommendations)

    # More than one-time use
    recommendationsReceived = evaluateRecommendations(recommendationRequest.location, user_data['event_history'], copy.deepcopy(places))
    if RECOMMENDED in user_data.keys():
        unique_recommendations = []
        for recommendation in recommendationsReceived:
            if recommendation not in user_data[RECOMMENDED]:
                unique_recommendations.append(recommendation)
        if len(unique_recommendations) == 0:
            #TODO: Consider case when the random_selection is again a duplicate
            for place in places:
                rand_selection = random.randint(0, len(place) - 1)
                if len(place) > 0:
                    unique_recommendations.append(convertToDBModel(recommendationRequest.location, place[rand_selection]))
        user_data[RECOMMENDED].extend(unique_recommendations)
        recommendationsReceived = unique_recommendations
    else:
        user_data[RECOMMENDED] = recommendationsReceived

    await db.replace_one({"_id": old_id}, user_data)
    return Response(content = json.dumps(convertToRecommendationResponseModel(recommendationsReceived)), media_type = "application/json" )

@app.post("/addRecommendation/{username}", status_code = 200)
async def addRecommendation(*, username: str, key: str, recommendationAcceptRequest: RecommendationAcceptRequest):
    res = validateAPIKey(key)
    if res != None:
        return res
    user_data = await db.find_one({"username": username})
    old_id = user_data['_id']
    found  = False
    index = -1

    if RECOMMENDED not in user_data.keys():
        return Response(content = json.dumps({ "errorList": [ "Requested place_id not found attached to user" ]}), media_type = "application/json")

    for i in range(len(user_data['recommended'])):
        if recommendationAcceptRequest.place_id == user_data['recommended'][i]['place_id']:
            found = True
            index = i
    
    if not found:
        return Response(content = json.dumps({ "errorList": [ "Requested place_id not found attached to user" ]}), media_type = "application/json")

    recommendation = user_data['recommended'][index]
    del(user_data['recommended'][index])
    user_data['event_history'].insert(len(user_data['event_history']), recommendation)

    await db.replace_one({'_id': old_id}, user_data)

    return Response(content = json.dumps(True), media_type = "application/json")