import ee

def get_flow_accumulation():
    
    # Load data
    merit_hydro_dataset = ee.Image("MERIT/Hydro/v1_0_1")
    
    # Select bands
    flow_accumulation = merit_hydro_dataset.select('upg')

    return flow_accumulation
    

def min_max(normalization_reference):
    """
    Calculates the minimum and maximum flow accumulation within the given normalization reference.

    Args:
        normalization_reference (ee FeatureCollection): The reference at which to normalize the variable.

    Returns:
        float: The minimum flow accumulation within the normalization reference.
        float: The maximum flow accumulation within the normalization reference.
    """

    flow_accumulation = get_flow_accumulation()

    # Define a function to compute min and max for each tile
    def get_min_max(tile):
                min_max = flow_accumulation.reduceRegion(
                    reducer=ee.Reducer.minMax(),
                    geometry=tile.geometry(),
                    scale=92.77,
                    maxPixels=1e10
                )
                return tile.set({'min_upg': min_max.get('upg_min'), 'max_upg': min_max.get('upg_max')})

    # Apply the function over the fishnet tiles
    min_max_tiles = normalization_reference.map(get_min_max)
    
    # Aggregate the results
    min_flow_list = min_max_tiles.aggregate_array('min_upg').getInfo()
    max_flow_list = min_max_tiles.aggregate_array('max_upg').getInfo()
    
    min_flow_float = min(min_flow_list)
    max_flow_float = max(max_flow_list)

    print(f"Min flow: {min_flow_float}, Max flow: {max_flow_float }")

    return min_flow_float, max_flow_float
    
    
def get_flow_accumulation_region(region_of_interest, min_value, max_value):
    """
    Calculates the mean flow accumulation within the given region of interest and normalizes the value at the normalization reference level.

    Args:
        region_of_interest (ee geometry object): The region for which to calculate the hazard index.
        min_value (float): The minimum value of this variable within the normalization reference.
        max_value (float): The maximum value of this variable within the normalization reference.

    Returns:
        ee number object: The normalized flow accumulation for the region of interest.
    """

    flow_accumulation = get_flow_accumulation()

    # Change min/max float to Earth Engine number object
    min_flow = ee.Number(min_value)
    max_flow = ee.Number(max_value)
    max_minus_min_flow = max_flow.subtract(min_flow)
    
    # Get mean flow accumulation for region of interest
    flow_region = flow_accumulation.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region_of_interest,
        scale=90 # Originally 92.77
    ).get('upg')

    flow_region = ee.Number(flow_region)
    
    # Normalize flow accumulation value for region of interest
    flow_region_normalized = (flow_region.subtract(min_flow)).divide(max_minus_min_flow)
    
    return ee.Number(flow_region_normalized).getInfo()
    








