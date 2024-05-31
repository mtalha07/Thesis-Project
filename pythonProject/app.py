from flask import Flask, render_template, jsonify, request
import geopandas as gpd
import pandas as pd
import networkx as nx
from shapely.geometry import Point, LineString, MultiLineString
import numpy as np
import json
import os

app = Flask(__name__)

# Function to find the nearest node in the graph
def find_nearest_node(G, point):
    min_distance = float('inf')
    nearest_node = None
    for node, data in G.nodes(data=True):
        node_point = Point(data['x'], data['y'])
        distance = point.distance(node_point)
        if distance < min_distance:
            min_distance = distance
            nearest_node = node
    return nearest_node

# Load hospitals data from GeoJSON file
with open('data/hospitals.geojson') as f:
    hospitals_data = json.load(f)

# Load road network from Shapefile using GeoPandas
road_network = gpd.read_file('data/Lahore_Network_clipped/Lahore_Network_ND_Junctions.shp')

# Load nodes data from multiple .nds files
nodes_folder_path = 'data/Lahore_Network_clipped/Lahore_Network_ND.nd'
nodes_files = [f for f in os.listdir(nodes_folder_path) if f.endswith('.nds')]

# Combine all .nds files into a single DataFrame
nodes_df_list = []
for nodes_file in nodes_files:
    file_path = os.path.join(nodes_folder_path, nodes_file)
    nodes_df = pd.read_csv(file_path, delimiter='\t')
    nodes_df_list.append(nodes_df)

nodes_df = pd.concat(nodes_df_list)

# Ensure the DataFrame has the expected columns
required_columns = {'node_id', 'x', 'y'}
if not required_columns.issubset(nodes_df.columns):
    raise ValueError(f"Nodes files must contain columns: {required_columns}")

# Create a NetworkX graph from the road network
G = nx.Graph()

# Add nodes from nodes DataFrame
for index, row in nodes_df.iterrows():
    node_id = row['node_id']
    x, y = row['x'], row['y']
    G.add_node(node_id, x=x, y=y)

# Add edges from road network with weights (road lengths)
for index, row in road_network.iterrows():
    geom = row['geometry']
    if isinstance(geom, LineString):
        u, v = geom.coords[0], geom.coords[-1]
        distance = geom.length
        u_node = find_nearest_node(G, Point(u))
        v_node = find_nearest_node(G, Point(v))
        G.add_edge(u_node, v_node, weight=distance)
    elif isinstance(geom, MultiLineString):
        for line in geom.geoms:
            u, v = line.coords[0], line.coords[-1]
            distance = line.length
            u_node = find_nearest_node(G, Point(u))
            v_node = find_nearest_node(G, Point(v))
            G.add_edge(u_node, v_node, weight=distance)

@app.route('/')
def index():
    return render_template('index.html', hospitalsData=hospitals_data)

@app.route('/api/hospitals')
def get_hospitals():
    return hospitals_data

@app.route('/api/route', methods=['POST'])
def calculate_route():
    try:
        data = request.json
        clicked_marker = data['marker']
        selected_hospital = data['hospital']

        clicked_point = Point(clicked_marker['lng'], clicked_marker['lat'])
        nearest_node = find_nearest_node(G, clicked_point)

        shortest_path = nx.shortest_path(G, source=int(selected_hospital), target=nearest_node, weight='weight')
        path_coordinates = [[G.nodes[node]['x'], G.nodes[node]['y']] for node in shortest_path]

        response_data = {'path': path_coordinates}
        return jsonify(response_data)
    except Exception as e:
        error_message = str(e)
        return jsonify({'error': error_message}), 400

if __name__ == '__main__':
    app.run(debug=True)
