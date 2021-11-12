import requests
import json
import time

reco_data = {
    "date": "test",
    "search_categories": ["restaurant", "park"],
    "location": {"lat": 33.748550, "lon": -84.391502}
}

add_reco_data = {
    "place_id": "ChIJUZrqlngE9YgRaLYKLIxmjEQ"
}

def test_getRecommendations():
    # Latency measure for getRecommendations API (~ 1s for 2 types)
    ts1 = time.time()
    res = requests.post(url = "http://127.0.0.1:8000/getRecommendations/vneal", data = json.dumps(reco_data))
    ts2 = time.time()
    print(ts2 - ts1)
    print(res.content.decode('utf-8'))

def test_addRecommendation():
    #Latency measure for addRecommendation API (~ 330ms worst case considering cold start on local)
    ts1 = time.time()
    res = requests.post(url = "http://127.0.0.1:8000/addRecommendation/vneal", data = json.dumps(add_reco_data))
    ts2 = time.time()
    print(ts2 - ts1)
    print(res.content.decode('utf-8'))