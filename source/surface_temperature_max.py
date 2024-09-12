import ee

def get_surface_temperature_max():
    # Load data
    cfs_dataset = ee.ImageCollection("NOAA/CFSV2/FOR6H")

    # Select bands
    max_temp = cfs_dataset.select('Maximum_temperature_height_above_ground_6_Hour_Interval')

    # Define a function to calculate the maximum temperature for a given year
    def max_year(year):
        start_date = ee.Date.fromYMD(year, 1, 1)
        end_date = start_date.advance(1, 'year')
        one_year = max_temp.filterDate(start_date, end_date)
        return one_year.max()

    years = ee.List.sequence(2010, 2020)

    # Calculate the annual maximum temperature between 2010 and 2020
    max_surface_temperature_2010_2020 = years.map(max_year)

    # Convert the list to an ImageCollection
    max_surface_temperature_2010_2020_imageCollection = ee.ImageCollection(max_surface_temperature_2010_2020)
 
    max_surface_temperature_mean = max_surface_temperature_2010_2020_imageCollection.mean()

    return max_surface_temperature_mean
    

def min_max(normalization_reference):
    """
    Calculates the minimum and maximum annual maximum surface temperature (2010-2020) within the given normalization reference.

    Args:
        normalization_reference (ee FeatureCollection): The reference at which to normalize the variable.

    Returns:
        float: The minimum annual maximum surface temperature within the normalization reference.
        float: The maximum annual maximum surface temperature within the normalization reference.
    """

    max_surface_temperature_mean = get_surface_temperature_max()

    # Define a function to compute min and max for each tile
    def get_min_max(tile):
        min_max = max_surface_temperature_mean.reduceRegion(
            reducer=ee.Reducer.minMax(),
            geometry=tile.geometry(),
            scale=22264,
            maxPixels=1e10
        )
        return tile.set({'min_Maximum_temperature_height_above_ground_6_Hour_Interval': min_max.get('Maximum_temperature_height_above_ground_6_Hour_Interval_min'), 'max_Maximum_temperature_height_above_ground_6_Hour_Interval': min_max.get('Maximum_temperature_height_above_ground_6_Hour_Interval_max')})

    # Apply the function over the fishnet tiles
    min_max_tiles = normalization_reference.map(get_min_max)
    
    # Aggregate the results
    min_surf_temp_list = min_max_tiles.aggregate_array('min_Maximum_temperature_height_above_ground_6_Hour_Interval').getInfo()
    max_surf_temp_list = min_max_tiles.aggregate_array('max_Maximum_temperature_height_above_ground_6_Hour_Interval').getInfo()
    
    min_surf_temp_float = min(min_surf_temp_list)
    max_surf_temp_float = max(max_surf_temp_list)
    
    # Print the overall results
    print(f"Min surface temperature: {min_surf_temp_float}, Max surface temperature: {max_surf_temp_float }")

    return min_surf_temp_float, max_surf_temp_float
    

def get_surface_temperature_max_region(region_of_interest, min_value, max_value):
    """
    Calculates the mean annual maximum surface temperature (2010-2020) within the given region of interest and normalizes the value at the normalization reference level.

    Args:
        region_of_interest (ee geometry object): The region for which to calculate the hazard index.
        min_value (float): The minimum value of this variable within the normalization reference.
        max_value (float): The maximum value of this variable within the normalization reference.

    Returns:
        ee number object: The normalized annual maximum surface temperature (2010-2020) for the region of interest.
    """
    
    max_surface_temperature_mean = get_surface_temperature_max()

    min_surface_temperature = ee.Number(min_value)
    max_surface_temperature = ee.Number(max_value)
    max_minus_min_surface_temperature = max_surface_temperature.subtract(min_surface_temperature)

    # Get mean surface temperature for region of interest
    surface_temperature_region = max_surface_temperature_mean.reduceRegion(
        reducer=ee.Reducer.mean(), 
        geometry=region_of_interest, 
        scale=90, # Originally 22264
        maxPixels=1e10
    ).get('Maximum_temperature_height_above_ground_6_Hour_Interval')

    surface_temperature_region = ee.Number(surface_temperature_region)
    
    # Normalize surface temperature value for region of interest
    surface_temperature_normalized = (surface_temperature_region.subtract(min_surface_temperature)).divide(max_minus_min_surface_temperature)
    
    return ee.Number(surface_temperature_normalized).getInfo()


























