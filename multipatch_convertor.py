import json
import geopandas as gpd
from shapely.geometry import Polygon 

def multipatch_convertor(geodataframe, z_unit_in='m', z_unit_out='m', relative_h=False, save=False, path='./', filename='output', out_format='geojson'):
    
    """Function converting ESRI Multipatch file into single polygons with 
    assigned height attribute using GeoPandas. It allows conversion between 
    meters ('m') and feets ('ft'), as well as assigining relative height.
    
    Dependencies:
        geopandas==0.3.0
        json==2.0.9
        shapely==1.5.16

    Keyword arguments:
    geodataframe: geopandas.GeoDataFrame() object
            GeoDataFrame to be converted;
    z_unit_in: str, {‘m’, ‘ft’}, default ‘m’
            height units of the input GeoDataFrame;
    z_unit_out: str, {‘m’, ‘ft’}, default ‘m’
            height units of the output GeoDataFrame;
    relative_h: bool, default False
            If the output GeoDataFrame should present relative height (Applies 
            when minimum height value is not equal to 0). All height values will 
            be subtructed minimum height of the feature.
    save: bool, default False
            whether the function should create an object in memory or save it 
            to file.
    path: str, default ‘./’
            if ‘save’ is set to True, defines directory where to save the output
    filename: str, default ‘output’
            if ‘save’ is set to True, defines the output name of the file
    out_format: str, {‘geojson’, ‘shp’}, default ‘geojson’
            if ‘save’ is set to True, defines the output file format between
            GeoJSON and ESRI Shapefile
    """   
    
    # Extract Coordinate Reference System (CRS) of the GeoDataFrame
    crs = geodataframe.crs
    
    # Convert GeoDataFrame inot JSON structure
    gdf_gj = json.loads(geodataframe.to_json())
    
    # Initiate list of features
    feature_list = []

    # Iterate through features of GeoDataFrame
    for feature in gdf_gj['features']:
        # Extract properties of each feature
        properties = feature['properties']
        # Flatten MultiPolygons into list of Polygons
        polygon_list = [p for mp in feature['geometry']['coordinates'] for p in mp]
        
        # Define minimum height
        if z_unit_in == 'm':
            min_h = 9000
        else:
            min_h = 30000
        
        # Initiate Polygon list for the feature
        splitted_feature_list = []
        
        # Iterate through Polygon list
        for polygon in polygon_list:
            # Create new feature and assign properties to each Polygon
            new_feature = properties.copy()
            
            # Extract new feature height
            height = polygon[0][2]
            
            # Compare height to minimum height and save if smaller
            if height < min_h:
                min_h = height
            
            # Assign new feature's height and vertices
            new_feature['height'] = height
            new_feature['geometry'] = Polygon([vertex[:2] for vertex in polygon])

            # Populate polygon list
            splitted_feature_list.append(new_feature)
            
        # Adjust height if relative
        if relative_h:
            for f in splitted_feature_list:
                f['height']=f['height'] - min_h
             
        # Convert height units
        if (z_unit_in == 'm') & (z_unit_out == 'ft'):
            for f in splitted_feature_list:
                f['height']=f['height'] * 3.28084
        elif (z_unit_in == 'ft') & (z_unit_out == 'm'):
            for f in splitted_feature_list:
                f['height']=f['height'] * 0.3048
        elif z_unit_in == z_unit_out:
            pass
        else:
            raise NameError('wrongUnits')
            print('Wrong height units given! Please, choose either ‘m’ for meters or ‘ft’ for feets')            
                
        # Add extracted new features to global feature list
        feature_list = feature_list + splitted_feature_list

    # Create a GeoDataFrame from new features
    new_gdf_gj = gpd.GeoDataFrame(
        feature_list, 
        index=range(len(feature_list)), 
        crs=crs)
    
    # Convert CRS to WGS 84 (lat and long in degrees)
    new_gdf_gj.to_crs({'init':'epsg:4326'}, inplace=True)
    
    # save file in desired location and format or return a GeoDataFrame
    if save:
        if out_format == 'geojson':
            new_gdf_gj.to_file(
                '{}{}.geojson'.format(path, filename), 
                driver='GeoJSON')
        elif out_format == 'shp':
            new_gdf_gj.to_file('{}{}.shp'.format(path, filename))
        else:
            raise NameError('wrongFormat')
            print('Wrong output file format given! Please, choose either ‘geojson’ or ‘shp’')
    else:
        return new_gdf_gj
