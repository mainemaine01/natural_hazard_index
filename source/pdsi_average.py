import ee

def get_pdsi_average():
        
    # Load data
    terraclimate_dataset = ee.ImageCollection('IDAHO_EPSCOR/TERRACLIMATE')

    # Define observation Period
    terraclimate_2000_2020 = terraclimate_dataset.filterDate('2000-01-01', '2021-01-01')

    # Select bands
    pdsi_2000_2020 = terraclimate_2000_2020.select('pdsi')

    # Get mean for observation period
    pdsi_average = pdsi_2000_2020.mean()

    return pdsi_average
    

def min_max(normalization_reference):
    """
    Calculates the minimum and maximum average PDSI (2000-2020) within the given normalization reference.

    Args:
        normalization_reference (ee FeatureCollection): The reference at which to normalize the variable.

    Returns:
        float: The minimum average PDSI within the normalization reference.
        float: The maximum average PDSI within the normalization reference.
    """
    
    pdsi_average = get_pdsi_average()

    # Define a function to compute min and max for each tile
    def get_min_max(tile):
        min_max = pdsi_average.reduceRegion(
            reducer=ee.Reducer.minMax(),
            geometry=tile.geometry(),
            scale=4638.3,
            maxPixels=1e9
        )
        return tile.set({'min_pdsi': min_max.get('pdsi_min'), 'max_pdsi': min_max.get('pdsi_max')})

    # Apply the function over the fishnet tiles
    min_max_tiles = normalization_reference.map(get_min_max)
    
    # Aggregate the results
    min_pdsi_list = min_max_tiles.aggregate_array('min_pdsi').getInfo()
    max_pdsi_list = min_max_tiles.aggregate_array('max_pdsi').getInfo()
    
    min_pdsi_float = min(min_pdsi_list)
    max_pdsi_float = max(max_pdsi_list)
    
    print(f"Min PDSI: {min_pdsi_float }, Max PDSI: {max_pdsi_float}")

    return min_pdsi_float, max_pdsi_float


def get_pdsi_region(region_of_interest, min_value, max_value):
    """
    Calculates the mean average PDSI (2000-2020) within the given region of interest and normalizes the value at the normalization reference level. Uses flipped normalization function, if values are smaller than 0, indicating dry conditions. Otherwise the normalized value is set to 0.

    Args:
        region_of_interest (ee geometry object): The region for which to calculate the hazard index.
        min_value (float): The minimum value of this variable within the normalization reference.
        max_value (float): The maximum value of this variable within the normalization reference.

    Returns:
        ee number object: The normalized average PDSI for the region of interest.
    """
    
    pdsi_average = get_pdsi_average()

    min_pdsi = ee.Number(min_value) 
    max_pdsi = ee.Number(0)
    max_minus_min_pdsi = max_pdsi.subtract(min_pdsi)
    
    # Get mean average pdsi for region of interest
    pdsi_region = pdsi_average.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region_of_interest,
        scale=90 # Originally 4638.3
    ).get('pdsi')

    pdsi_region = ee.Number(pdsi_region)

    # Normalize pdsi value for region of interest
    pdsi_region_normalized = ee.Algorithms.If(
    pdsi_region.lt(0),
    (max_pdsi.subtract(pdsi_region)).divide(max_minus_min_pdsi),
    ee.Number(0)  # Set all positive values, which indicate wet conditions, to 0
    )
    
    return ee.Number(pdsi_region_normalized).getInfo()






