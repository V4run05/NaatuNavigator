from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
import json
from datetime import datetime
import requests
from pprint import pprint
import math

#dbms
app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
#db = SQLAlchemy(app)
app.secret_key = 'secret_key'
api_key = 'j4t0mdWGaE9dhNXBd3FyZaWQiY7yVKYK'

route_geometry=[]
bus_stops_on_route=[]

def GetCoordinates(location):
    url = f'https://api.tomtom.com/search/2/geocode/{location}.json?key={api_key}'
    response = requests.get(url)
    data = response.json()
    if data['results']:
        latitude = data['results'][0]['position']['lat']
        longitude = data['results'][0]['position']['lon']
        #print(f"Starting Point => Latitude: {start_lat}, Longitude: {start_lon}")
        return latitude,longitude
    else:
        print("Place not found.")
        return 'No Results Found'


def is_close(lat1, lon1, lat2, lon2, threshold=0.0001):
    """Check if two latitude/longitude points are within a given threshold."""
    return math.isclose(lat1, lat2, abs_tol=threshold) and math.isclose(lon1, lon2, abs_tol=threshold)

route_geometry = []
@app.route('/', methods=['POST','GET'])
def index(): 
    if request.method == "POST":
        #bus_id = request.form['bus_id']
        start_loc = request.form['start_loc']
        end_loc = request.form['end_loc']
        start_lat = GetCoordinates(start_loc)[0]
        start_lon = GetCoordinates(start_loc)[1]
        end_lat = GetCoordinates(end_loc)[0]
        end_lon = GetCoordinates(end_loc)[1]

        url = f'https://api.tomtom.com/routing/1/calculateRoute/{start_lat},{start_lon}:{end_lat},{end_lon}/json?key={api_key}&travelMode=bus'
        response = requests.get(url)
        route_data = response.json()

        if response.status_code == 200:
            route_geometry = []
            route = route_data['routes'][0]
            route_summary = route['summary']
            distance = route_summary['lengthInMeters'] / 1000  # Distance in kilometers
            duration = route_summary['travelTimeInSeconds'] / 60  # Duration in minutes

            #pprint(route)
            #print(f"Distance: {distance:.2f} km")
            #print(f"Duration: {duration:.2f} minutes")

            route_geometry = route['legs'][0]['points']
            session['route_geometry'] = route_geometry

        else:   
            print(f"Error: {response.status_code} - {response.reason}")
        #return redirect('/route/')
        #Step 2: Search for bus stops along the route using the Search API
        # if route_data['routes']:
        #     bus_stops_on_route = []

        #     for leg in route_data['routes'][0]['legs']:
        #         for point in leg['points']:
        #             lat = point['latitude']
        #             lon = point['longitude']

        #             # Step 3: Search for bus stops near each route point with a small radius
        #             search_url = f"https://api.tomtom.com/search/2/poiSearch/bus%20stop.json?key={api_key}&lat={lat}&lon={lon}&radius=50&categorySet=9609"
        #             search_response = requests.get(search_url)
        #             if search_response.status_code == 200:
        #                 search_data = search_response.json()

        #                 pprint(search_data)
        #                 #Process the data
        #                 #Step 4: Check if the bus stops are exactly on the route
        #                 for result in search_data['results']:
        #                     bus_stop_lat = result['position']['lat']
        #                     bus_stop_lon = result['position']['lon']
                            
        #                     if is_close(lat, lon, bus_stop_lat, bus_stop_lon):
        #                         bus_stop_name = result['poi']['name']
        #                         bus_stops_on_route.append({
        #                             "name": bus_stop_name,
        #                             "lat": bus_stop_lat,
        #                             "lon": bus_stop_lon
        #                         })
        #             else:
        #                 print(f"Error: {response.status_code} - {response.reason}")

        #     #Output the bus stops exactly on the route
        #     if bus_stops_on_route:
        #         for stop in bus_stops_on_route:
        #             print(f"Bus Stop: {stop['name']}, Lat: {stop['lat']}, Lon: {stop['lon']}")
        #     else:
        #         print("No bus stops found on the route.")
        # else:
        #     print("No route found.")

        # session['bus_stops_on_route'] = bus_stops_on_route
        return redirect('/route/')
    else:
        return render_template('main.html')

@app.route('/route/')
def ShowRoute():
    route_geometry = session.get('route_geometry', [])
    bus_stops_on_route = session.get('bus_stops_on_route', [])
    return render_template('Routes.html',route=route_geometry, bus_stops=bus_stops_on_route)

@app.route('/autocomplete')
def autocomplete():
    query = request.args.get('query')
    if query:
        url = f'https://api.tomtom.com/search/2/search/{query}.json?key={api_key}'
        response = requests.get(url)
        data = response.json()
        # Return the data as JSON, which the frontend will use to display suggestions
        return data
    return {'results': []}  # Return an empty result if no query

if __name__ == '__main__':
    app.run(debug=True)
