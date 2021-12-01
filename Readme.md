##Steps
- Server is currently running at: recoserver.me/
- 3 APIs provided: 
- - `/initUser/{username}?key=<API_KEY>: add a user to start tracking event_history. To be used for first time users.
- - `/addRecommendation/{username}?key=<API_KEY>, Body: {"places_id": "xxxxx"}`: shifts a place from recommended to user state to event_history which would be used for recommendation evaluation from next step
- - `/getRecommendations/{username}?key=<API_KEY>, Body: See openapi spec`.
Eg: 
```
reco_data = {
    "date": "test",
    "search_categories": ["restaurant", "park"],
    "location": {"lat": 33.748550, "lon": -84.391502}
}:
```
gets new recommendations and adds them to the recommended to user list in mongoDB
- openapi spec link: recoserver.me/openapi.json
- Can test out APIs using swagger here: recoserver.me/docs

<API_KEY> will be sent separately
Postman example:
```
GET http://recoserver.me/initUser/{username}?key=<API_KEY>
```
POST http://recoserver.me/getRecommendations/vneal?key=<API_KEY>
Body (application/json):
{
    "date": "test",
    "search_categories": ["museum"],
    "location": {"lat": 33.748550, "lon": -84.391502}
}
```

```
POST http://recoserver.me/addRecommendations/vneal?key=<API_KEY>
Body (application/json):
{
    "place_id": "xxxxx"
}
```

Run the server with: uvicorn main:app --reload --host 0.0.0.0 --port 8000
To use this as a web service: add firewall rules to redirect traffic from port 80 to 8000
0.0.0.0 allows other computer on the network to join. For development purposes use 127.0.0.1

