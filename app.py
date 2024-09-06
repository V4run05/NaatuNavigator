from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import json
from datetime import datetime
import requests
from pprint import pprint
# Load the GeoJSON file
with open(r"C:\Varun\VSCode\Projects\Python\Hackathon\OpenStreetMap\chennai_bus_stops.geojson", 'r', encoding='utf-8') as f:
    geojson_data = json.load(f)

# Extract bus stop coordinates and names
bus_stops = []
for feature in geojson_data['features']:
    # GeoJSON stores coordinates in [longitude, latitude] format
    coordinates = feature['geometry']['coordinates']
    lon, lat = coordinates[0], coordinates[1]

    # Extract the name of the bus stop if available
    name = feature['properties'].get('name', 'Unnamed Stop')

    # Store the bus stop data
    bus_stops.append({
        'name': name,
        'lat': lat,
        'lng': lon
    })

#dbms
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)
api_key = 'j4t0mdWGaE9dhNXBd3FyZaWQiY7yVKYK'

class BusDBMS(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.String(200), nullable=False)
    end = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return '<Task %r>' % self.id

with app.app_context():
        db.create_all()

route_geometry=[]

@app.route('/', methods=['POST','GET'])
def index(): 
    if request.method == "POST":
        #bus_id = request.form['bus_id']
        start_loc = request.form['start_loc']
        end_loc = request.form['end_loc']
        bus_search = request.form['bus_search']
        new_bus = BusDBMS(start=start_loc, end=end_loc)
        buses = BusDBMS.query.all()
        bus_start=None
        bus_end=None
        start_lat=0
        start_lon=0
        end_lat=0
        end_lon=0
        for bus in buses:
            if(bus.id == int(bus_search)):
                bus_start = bus.start
                bus_end = bus.end
                break
        else:
            print('There is no proper start or stop information')
        for bus in bus_stops:
            if bus['name'] == bus_start:
                start_lat = bus['lat']
                start_lon = bus['lng']
            elif bus['name'] == bus_end:
                end_lat = bus['lat']
                end_lon = bus['lng']

        url = f'https://api.tomtom.com/routing/1/calculateRoute/{start_lat},{start_lon}:{end_lat},{end_lon}/json?key={api_key}'
        response = requests.get(url)
        route_data = response.json()

        if response.status_code == 200:
            route_geometry = []
            route = route_data['routes'][0]
            route_summary = route['summary']
            distance = route_summary['lengthInMeters'] / 1000  # Distance in kilometers
            duration = route_summary['travelTimeInSeconds'] / 60  # Duration in minutes

            pprint(route)
            print(f"Distance: {distance:.2f} km")
            print(f"Duration: {duration:.2f} minutes")

            route_geometry = route['legs'][0]['points']

        else:   
            print(f"Error: {response.status_code} - {response.reason}")

        try:
            db.session.add(new_bus)
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue adding the bus'
    else:
        return render_template('map.html', bus_stops=bus_stops)

@app.route('/ViewAllBuses/')
def ShowDatabase():
    buses = BusDBMS.query.all()
    return render_template('BusDatabase.html',buses=buses)

#@app.route('/route/')
#def ShowRoute():
    #++++return render_template('Routes.html',bus_stops=bus_stops)

if __name__ == '__main__':
    app.run(debug=True)
