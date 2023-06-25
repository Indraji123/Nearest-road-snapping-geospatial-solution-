import geopandas as gpd
from shapely import snap, get_point
import numpy as np
import pandas as pd

## function for generating nearest point to line

def generate_nearest_point_to_line(a, b):
    points_ =[get_point(a,i) for i in [0 , -1]]
    i = 0
    point_to_snap = []
    for point_ in points_:
        interpolated_ = b.interpolate(b.project(point_))
        for point__ in points_:
            dist_ = point__.distance(interpolated_)
            if (i == 0) or (point_to_snap[0] > dist_):
                point_to_snap= [dist_ , point__, interpolated_]
            i += 1
    return point_to_snap

##  read vector geojson layer & finding nearest road from another road layer

data = gpd.read_file("main_data.geojson",crs='epsg:4326')
data = data.to_crs('epsg:3857')
osm_data = gpd.read_file("osm_data.geojson",crs='epsg:4326')
osm_data = osm_data.to_crs('epsg:3857')
osm_data = osm_data[['highway','geometry']]
highway_cross_landuse = data[~data.highway.isna()].sjoin(data[~data.landuse.isna()][['geometry']], predicate='crosses')
osm_data =  osm_data[~osm_data['highway'].isna()]
osm_data = osm_data.drop(osm_data[['geometry']].sjoin(data[~data.landuse.isna()][['geometry']],predicate='intersects').index)
highway_cross_landuse = highway_cross_landuse.drop(columns='index_right')
nn_joined = highway_cross_landuse[['geometry']].sjoin_nearest(osm_data[['geometry']])

nn_joined["index_left"]= nn_joined.index

nn_joined = nn_joined.overlay(data[~data.landuse.isna()],how='difference').explode(index_parts = True).reset_index(drop=True)

## snaping with one road layer to nearest main another road layer

for _, row in nn_joined.iterrows():
    a1 = row.geometry
    a = data.loc[row.index_left, 'geometry']
    b = osm_data.geometry[row.index_right]
    dist_, _ ,snap_point = generate_nearest_point_to_line(a1,b)
    b = snap(b, snap_point, 0.5)
    a = snap(a, snap_point, dist_ + 0.5)
    data.loc[row.index_left, 'geometry'] = a
    osm_data.loc[row.index_right, 'geometry'] = b
    
pd.concat([data.reset_index(drop=True), osm_data.reset_index(drop=True)], axis=0).to_crs('epsg:4326').to_file('output.geojson')