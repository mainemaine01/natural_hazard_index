import ee

def get_friction():
    # Load data
    oxford_friction_dataset = ee.Image("Oxford/MAP/friction_surface_2019")
    
    # Select bands
    friction = oxford_friction_dataset.select('friction')

    return friction


def min_max(normalization_reference):
    """
    Calculates the minimum and maximum friction within the given normalization reference.

    Args:
        normalization_reference (ee FeatureCollection): The reference at which to normalize the variable.

    Returns:
        float: The minimum friction within the normalization reference.
        float: The maximum friction within the normalization reference.
    """

    friction = get_friction()

    # Define a function to compute min and max for each tile
    def get_min_max(tile):
        min_max = friction.reduceRegion(
            reducer=ee.Reducer.minMax(),
            geometry=tile.geometry(),
            scale=927.67,
            maxPixels=1e10
        )
        return tile.set({'min_friction': min_max.get('friction_min'), 'max_friction': min_max.get('friction_max')})

    # Apply the function over the fishnet tiles
    min_max_tiles = normalization_reference.map(get_min_max)
    
    # Aggregate the results
    min_friction_list = min_max_tiles.aggregate_array('min_friction').getInfo()
    max_friction_list = min_max_tiles.aggregate_array('max_friction').getInfo()
    
    min_friction_float = min(min_friction_list)
    max_friction_float = max(max_friction_list)
    
    print(f"Min friction: {min_friction_float}, Max friction: {max_friction_float }")

    return min_friction_float, max_friction_float
    

def get_friction_region(region_of_interest, min_value, max_value):
    """
    Calculates the mean friction within the given region of interest and normalizes the value at the normalization reference level.

    Args:
        region_of_interest (ee geometry object): The region for which to calculate the hazard index.
        min_value (float): The minimum value of this variable within the normalization reference.
        max_value (float): The maximum value of this variable within the normalization reference.

    Returns:
        ee number object: The normalized friction for the region of interest.
    """

    friction = get_friction()

    # Change min/max float to Earth Engine number object
    min_friction = ee.Number(min_value)
    max_friction = ee.Number(max_value)
    max_minus_min_friction = max_friction.subtract(min_friction)  
    
    # Get mean friction for region of interest
    friction_region = friction.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region_of_interest,
        scale=90 # Originally 927.67
    ).get('friction')

    friction_region = ee.Number(friction_region)
    
    # Normalize friction value for region of interest
    friction_region_normalized = (friction_region.subtract(min_friction)).divide(max_minus_min_friction)
    
    return ee.Number(friction_region_normalized).getInfo()






