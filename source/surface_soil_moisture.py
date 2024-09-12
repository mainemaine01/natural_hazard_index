import ee

def get_surface_soil_moisture():
    # Load data
    smap_dataset = ee.ImageCollection("NASA_USDA/HSL/SMAP10KM_soil_moisture")
    
    # Define observation Period
    smap_2015_2020 = smap_dataset.filterDate('2015-04-02', '2021-01-01')
    
    # Select bands
    surface_soil_moisture = smap_2015_2020.select('ssm')
    
    surface_soil_moisture_mean = surface_soil_moisture.mean()

    return surface_soil_moisture_mean
    

def min_max(normalization_reference):
    """
    Calculates the minimum, maximum and mean average surface soil moisture (2015-2020) within the given normalization reference.

    Args:
        normalization_reference (ee FeatureCollection): The reference at which to normalize the variable.

    Returns:
        float: The minimum average surface soil moisture within the normalization reference.
        float: The maximum average surface soil moisture within the normalization reference.
        float: The mean average surface soil moisture within the normalization reference.
    """
    
    surface_soil_moisture = get_surface_soil_moisture()

    # Define a function to compute min, max and mean for each tile
    def get_min_max_mean(tile):
        stats = surface_soil_moisture.reduceRegion(
            reducer=ee.Reducer.minMax().combine(
                reducer2=ee.Reducer.mean(), 
                sharedInputs=True
            ),
            geometry=tile.geometry(),
            scale=10000,
            maxPixels=1e11
        )
        return tile.set({
            'min_ssm': stats.get('ssm_min'), 
            'max_ssm': stats.get('ssm_max'),
            'mean_ssm': stats.get('ssm_mean')
        })

    # Apply the function over the fishnet tiles
    min_max_mean_tiles = normalization_reference.map(get_min_max_mean)
    
    # Aggregate the results
    min_ssm_list = min_max_mean_tiles.aggregate_array('min_ssm').getInfo()
    max_ssm_list = min_max_mean_tiles.aggregate_array('max_ssm').getInfo()
    mean_ssm_list = min_max_mean_tiles.aggregate_array('mean_ssm').getInfo()
    
    min_ssm_float = min(min_ssm_list)
    max_ssm_float = max(max_ssm_list)
    mean_ssm_float = sum(mean_ssm_list) / len(mean_ssm_list)

    print(f"Min ssm: {min_ssm_float}, Max ssm: {max_ssm_float }, Mean ssm: {mean_ssm_float }")

    return min_ssm_float, max_ssm_float, mean_ssm_float
    

def get_surface_soil_moisture_region(region_of_interest, min_value, max_value, mean_value):
    """
    Calculates the mean average surface soil moisture (2015-2020) within the given region of interest and normalizes the value at the normalization reference level.

    Args:
        region_of_interest (ee geometry object): The region for which to calculate the hazard index.
        min_value (float): The minimum value of this variable within the normalization reference.
        max_value (float): The maximum value of this variable within the normalization reference.

    Returns:
        ee number object: The normalized average surface soil moisture for the region of interest.
    """
    
    surface_soil_moisture = get_surface_soil_moisture()

    min_ssm = ee.Number(min_value)
    max_ssm = ee.Number(max_value)
    max_minus_min_ssm = max_ssm.subtract(min_ssm)    

    # Get mean ssm for region of interest
    ssm_region = surface_soil_moisture.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=region_of_interest,
            scale=90 # Originally 10000
        ).get('ssm')

    # Assign mean value to ssm_region if value is null to fill data gaps
    ssm_region = ee.Algorithms.If(ssm_region, ssm_region, mean_value)

    ssm_region = ee.Number(ssm_region)
    
    # Normalize ssm value for region of interest
    ssm_region_normalized = (max_ssm.subtract(ssm_region)).divide(max_minus_min_ssm)

    return ee.Number(ssm_region_normalized).getInfo()

















