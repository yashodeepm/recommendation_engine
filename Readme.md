##Steps
- Server is currently running at: recoserver.me/
- 2 APIs provided: 
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

