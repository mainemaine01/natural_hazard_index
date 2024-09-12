import ee

def get_precipitation_change():
     # Load data
    chirps_dataset = ee.ImageCollection('UCSB-CHG/CHIRPS/PENTAD')

    # Select bands
    chirps_precipitation = chirps_dataset.select('precipitation')

    # Define observation Period
    precipitation_1981_1990 = chirps_precipitation.filterDate('1981-01-01', '1991-01-01')
    precipitation_2009_2020 = chirps_precipitation.filterDate('2009-01-01', '2021-01-01')

    # Calclulate precipitation sum between 1981-1990
    precipitation_1981_1990_sum = precipitation_1981_1990.sum()
    
    # Calculate mean annual precipitation between 1981-1990
    precipitation_1981_1990_annual = precipitation_1981_1990_sum.divide(10)

    # Calclulate precipitation sum between 2009-2020
    precipitation_2009_2020_sum = precipitation_2009_2020.sum()

    # Calculate mean annual precipitation between 2009-2020
    precipitation_2009_2020_annual = precipitation_2009_2020_sum.divide(12)

    # Calculate change in annual accumulation
    annual_precipitation_change = precipitation_2009_2020_annual.subtract(precipitation_1981_1990_annual)

    return annual_precipitation_change


def min_max(normalization_reference):
    """
    Calculates the minimum and maximum change in annual precipitation accumulation (2009-2020 compared to 1981-1990) within the given normalization reference.
    
    Args:
        normalization_reference (ee FeatureCollection): The reference at which to normalize the variable.

    Returns:
        float: The minimum change in annual precipitation accumulation within the normalization reference.
        float: The maximum change in annual precipitation accumulation within the normalization reference.
    """
    
    annual_precipitation_change = get_precipitation_change()
    
    # Define a function to compute min and max for each tile
    def get_min_max(tile):
        min_max = annual_precipitation_change.reduceRegion(
            reducer=ee.Reducer.minMax(),
            geometry=tile.geometry(),
            scale=5566,
            maxPixels=1e10
        )
        return tile.set({'min_precipitation': min_max.get('precipitation_min'), 'max_precipitation': min_max.get('precipitation_max')})

    # Apply the function over the fishnet tiles
    min_max_tiles = normalization_reference.map(get_min_max)
    
    # Aggregate the results
    min_precip_list = min_max_tiles.aggregate_array('min_precipitation').getInfo()
    max_precip_list = min_max_tiles.aggregate_array('max_precipitation').getInfo()
    
    min_annual_precip_change_float = min(min_precip_list)
    max_annual_precip_change_float = max(max_precip_list)
    
    print(f"Min precipitation accumulation change: {min_annual_precip_change_float}, Max precipitation accumulation change: {max_annual_precip_change_float}")

    return min_annual_precip_change_float, max_annual_precip_change_float

    

def get_precipitation_change_region(region_of_interest, min_value, max_value):
    """
    Calculates the mean change in annual precipitation accumulation (2009-2020 compared to 1981-1990) within the given region of interest and normalizes the value at the normalization reference level. Uses standard normalization function, if change in annual precipitation accumulation is positive (indicating flood). Uses flipped normalization function, if change is negative (indicating drought).

    Args:
        region_of_interest (ee geometry object): The region for which to calculate the hazard index.
        min_value (float): The minimum value of this variable within the normalization reference.
        max_value (float): The maximum value of this variable within the normalization reference.

    Returns:
        ee number object: The normalized change in annual precipitation accumulation for the region of interest.
    """
    
    annual_precipitation_change = get_precipitation_change()
       
    min_annual_precipitation_change = ee.Number(min_value)
    max_annual_precipitation_change = ee.Number(max_value)
    
    # Get mean annual precipitation change for region of interest
    precip_change_region = annual_precipitation_change.reduceRegion(
        reducer=ee.Reducer.mean(), 
        geometry=region_of_interest,
        scale=90, # Originally 5566
        maxPixels=1e10
    ).get('precipitation')

    precip_change_region = ee.Number(precip_change_region)

    # Normalize change in annual precipitation accumulation value for region of interest
    precip_region_normalized = ee.Algorithms.If(
        precip_change_region.gt(0),
        precip_change_region.divide(max_annual_precipitation_change),  # Normalize for flood
        ee.Algorithms.If(
            precip_change_region.lt(0),
            precip_change_region.divide(min_annual_precipitation_change),  # Normalize for drought
            ee.Number(0)
        )
    )
    
    return ee.Number(precip_region_normalized).getInfo()
    
    
