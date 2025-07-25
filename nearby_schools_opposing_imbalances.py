import duckdb
from folium import FeatureGroup

from logica.common import logica_lib
from pyproj import Transformer
import folium
import matplotlib
from matplotlib import colors

db_path = "../data/madrid.duckdb"
connection = duckdb.connect(db_path)

def school_lat_lon(school_code, schools_coordinates):
    school_coordinates = schools_coordinates.loc[schools_coordinates['school_code'] == school_code]
    if school_coordinates.empty:
        return None, None
    else:
        transformer = Transformer.from_crs("EPSG:25830", "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(school_coordinates.iloc[0]['x'], school_coordinates.iloc[0]['y'])
        return lat, lon

def marker_circle(lat, lon, radius, color, color_fill, popup):
    marker = folium.CircleMarker(
        location=[lat, lon],
        radius=radius,
        color=color,
        weight=1,
        fill=True,
        fill_color=color_fill,
        fill_opacity=0.7,
        popup=popup
    )
    return marker

def marker_school_segregation(school_segregation, min_segregation, max_segregation, schools_coordinates):
    code = school_segregation['school_code']
    name = school_segregation['school_name']
    imbalance = school_segregation['imbalance']
    minority_students = school_segregation['minority_students']
    total_students = school_segregation['total_students']
    lat, lon = school_lat_lon(code, schools_coordinates)
    popup = (f"{name}<br>"
             f"Imbalance = {imbalance}<br>"
             f"Minimum-income students: {int(minority_students)}<br>"
             f"Total students: {int(total_students)}<br>")
    if lat != None and  lon != None:
        min_radius = 4
        max_radius = 12
        if imbalance > 0:
            radius = min_radius + (imbalance/max_segregation) * (max_radius-min_radius)
            color = colors.to_hex(matplotlib.colormaps['Reds'](imbalance/max_segregation))
            return marker_circle(lat, lon, radius, 'red', color, popup)
        elif imbalance < 0:
            radius = min_radius + (imbalance/min_segregation) * (max_radius-min_radius)
            color = colors.to_hex(matplotlib.colormaps['Blues'](imbalance/min_segregation))
            return marker_circle(lat, lon, radius, 'blue', color, popup)
        else:
            return marker_circle(lat, lon, min_radius, 'white', 'white', popup)
    else:
        return None

map = folium.Map(location=[40.4168, -3.7038], zoom_start=9)
schools_segregation = logica_lib.RunPredicateToPandas('segregation.l',
                                                      'ExtremeSchools',
                                                      connection=connection)
schools_coordinates = logica_lib.RunPredicateToPandas('segregation.l',
                                                      'SchoolCoordinates', connection=connection)
max_segregation = max(schools_segregation['imbalance'])
min_segregation = min(schools_segregation['imbalance'])

for _, school_segregation in schools_segregation.iterrows():
    marker_school_segregation(
        school_segregation, min_segregation, max_segregation, schools_coordinates).add_to(map)

map.save(f"nearby_schools_opposing_imbalances.html")

connection.close()
