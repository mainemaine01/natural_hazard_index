import ee

def get_slope():
    # Load data
    srtm_dataset = ee.Image("CGIAR/SRTM90_V4")

    # Select bands
    dem = srtm_dataset.select('elevation')
    
    # Calculate slope
    slope = ee.Terrain.slope(dem)

    return slope


def min_max(normalization_reference):
    """
    Calculates the minimum and maximum slope within the given normalization reference.

    Args:
        normalization_reference (ee FeatureCollection): The reference at which to normalize the variable.

    Returns:
        float: The minimum slope within the normalization reference.
        float: The maximum slope within the normalization reference.
    """

    slope = get_slope()

    # Define a function to compute min and max for each tile
    def get_min_max(tile):
                min_max = slope.reduceRegion(
                    reducer=ee.Reducer.minMax(),
                    geometry=tile.geometry(),
                    scale=90,
                    maxPixels=1e11
                )
                return tile.set({'min_slope': min_max.get('slope_min'), 'max_slope': min_max.get('slope_max')})

    # Apply the function over the fishnet tiles
    min_max_tiles = normalization_reference.map(get_min_max)
    
    # Aggregate the results
    min_slope_list = min_max_tiles.aggregate_array('min_slope').getInfo()
    max_slope_list = min_max_tiles.aggregate_array('max_slope').getInfo()
    
    min_slope_float = min(min_slope_list)
    max_slope_float = max(max_slope_list)
    
    print(f"Min slope: {min_slope_float}, Max slope: {max_slope_float }")

    return min_slope_float, max_slope_float


def get_slope_region(region_of_interest, min_value, max_value):
    """
    Calculates the mean slope within the given region of interest and normalizes the value at the normalization reference level.

    Args:
        region_of_interest (ee geometry object): The region for which to calculate the hazard index.
        min_value (float): The minimum value of this variable within the normalization reference.
        max_value (float): The maximum value of this variable within the normalization reference.

    Returns:
        ee number object: The normalized slope for the region of interest.
    """

    slope = get_slope()

    min_slope = ee.Number(min_value)
    max_slope = ee.Number(max_value)
    max_minus_min_slope = max_slope.subtract(min_slope)

    # Get mean slope for region of interest
    slope_region = slope.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region_of_interest,
        scale=90
    ).get('slope')
    
    slope_region = ee.Number(slope_region)
    
    # Normalize slope value for region of interest
    slope_region_normalized = (slope_region.subtract(min_slope)).divide(max_minus_min_slope)
    
    return ee.Number(slope_region_normalized).getInfo()









