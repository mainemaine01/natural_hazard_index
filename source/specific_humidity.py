import ee

def get_specific_humidity():
    # Load data
    fldas_dataset = ee.ImageCollection("NASA/FLDAS/NOAH01/C/GL/M/V001")
    
    # Select bands
    humidity = fldas_dataset.select('Qair_f_tavg')
    
    # Define observation Period
    humidity_2000_2020 = humidity.filterDate('2000-01-01', '2021-01-01')
    
    specific_humidity_mean = humidity_2000_2020.mean()

    return specific_humidity_mean
    

def min_max(normalization_reference):
    """
    Calculates the minimum and maximum average specific humidity (2000-2020) within the given normalization reference.

    Args:
        normalization_reference (ee FeatureCollection): The reference at which to normalize the variable.

    Returns:
        float: The minimum average specific humidity within the normalization reference.
        float: The maximum average specific humidity within the normalization reference.
    """

    specific_humidity = get_specific_humidity()

    # Define a function to compute min and max for each tile
    def get_min_max(tile):
            min_max = specific_humidity.reduceRegion(
                reducer=ee.Reducer.minMax(),
                geometry=tile.geometry(),
                scale=11132,
                maxPixels=1e10
            )
            return tile.set({'min_Qair_f_tavg': min_max.get('Qair_f_tavg_min'), 'max_Qair_f_tavg': min_max.get('Qair_f_tavg_max')})

    # Apply the function over the fishnet tiles
    min_max_tiles = normalization_reference.map(get_min_max)
    
    # Aggregate the results
    min_humidity_list = min_max_tiles.aggregate_array('min_Qair_f_tavg').getInfo()
    max_humidity_list = min_max_tiles.aggregate_array('max_Qair_f_tavg').getInfo()
    
    min_humidity_float = min(min_humidity_list)
    max_humidity_float = max(max_humidity_list)
    
    print(f"Min specific humidity: {min_humidity_float}, Max specific humidity: {max_humidity_float }")

    return min_humidity_float, max_humidity_float


def get_specific_humidity_region(region_of_interest, min_value, max_value):
    """
    Calculates the mean average specific humidity (2000-2020) within the given region of interest and normalizes the value at the normalization reference level.

    Args:
        region_of_interest (ee geometry object): The region for which to calculate the hazard index.
        min_value (float): The minimum value of this variable within the normalization reference.
        max_value (float): The maximum value of this variable within the normalization reference.

    Returns:
        ee number object: The normalized average specific humidity for the region of interest.
    """

    specific_humidity = get_specific_humidity()

    min_humidity = ee.Number(min_value)
    max_humidity = ee.Number(max_value)
    max_minus_min_humidity = max_humidity.subtract(min_humidity)

    # Get mean specific humidity for region of interest
    humidity_region = specific_humidity.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region_of_interest,
        scale=90 # Originally 11132
    ).get('Qair_f_tavg')
    
    humidity_region = ee.Number(humidity_region)

    # Normalize specific humidity value for region of interest
    humidity_region_normalized = (max_humidity.subtract(humidity_region)).divide(max_minus_min_humidity)
    
    return ee.Number(humidity_region_normalized).getInfo()
    
    
    
    
    
    
    
    
    
