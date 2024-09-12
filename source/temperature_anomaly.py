import ee

def get_temperature_anomaly():
    # Load data
    era_dataset = ee.ImageCollection(ee.ImageCollection("ECMWF/ERA5/DAILY"))
    
    # Select bands
    air_temperature = era_dataset.select('mean_2m_air_temperature')
    
    # Define observation Period
    air_temperature_1980_1991 = air_temperature.filterDate('1980-01-01', '1992-01-01')
    air_temperature_2008_2019 = air_temperature.filterDate('2008-01-01', '2020-01-01')
    
    # Calculate mean temperature
    air_temperature_1980_1991_mean = air_temperature_1980_1991.mean()
    air_temperature_2008_2019_mean = air_temperature_2008_2019.mean()
    
    # Calculate long-term temperature anomaly
    temperature_anomaly = air_temperature_2008_2019_mean.subtract(air_temperature_1980_1991_mean)

    return temperature_anomaly


def min_max(normalization_reference):
    """
    Calculates the minimum and maximum long-term temperature anomaly (climate normal: 1980-1992) within the given normalization reference.

    Args:
        normalization_reference (ee FeatureCollection): The reference at which to normalize the variable.

    Returns:
        float: The minimum long-term temperature anomaly within the normalization reference.
        float: The maximum long-term temperature anomaly within the normalization reference.
    """

    temperature_anomaly = get_temperature_anomaly()

    # Define a function to compute min and max for each tile
    def get_min_max(tile):
        min_max = temperature_anomaly.reduceRegion(
            reducer=ee.Reducer.minMax(),
            geometry=tile.geometry(),
            scale=27830,
            maxPixels=1e9
        )
        return tile.set({'min_mean_2m_air_temperature': min_max.get('mean_2m_air_temperature_min'), 'max_mean_2m_air_temperature': min_max.get('mean_2m_air_temperature_max')})

    # Apply the function over the fishnet tiles
    min_max_tiles = normalization_reference.map(get_min_max)
    
    # Aggregate the results
    min_temperature_anomaly_list = min_max_tiles.aggregate_array('min_mean_2m_air_temperature').getInfo()
    max_temperature_anomaly_list = min_max_tiles.aggregate_array('max_mean_2m_air_temperature').getInfo()
    
    min_temperature_anomaly_float = min(min_temperature_anomaly_list)
    max_temperature_anomaly_float = max(max_temperature_anomaly_list)
    
    print(f"Min temperature anomaly: {min_temperature_anomaly_float}, Max temperature anomaly: {max_temperature_anomaly_float}")

    return min_temperature_anomaly_float, max_temperature_anomaly_float
    

def get_temperature_anomaly_region(region_of_interest, min_value, max_value):
    """
    Calculates the mean long-term temperature anomaly (climate normal: 1980-1992) within the given region of interest and normalizes the value at the normalization reference level.

    Args:
        region_of_interest (ee geometry object): The region for which to calculate the hazard index.
        min_value (float): The minimum value of this variable within the normalization reference.
        max_value (float): The maximum value of this variable within the normalization reference.

    Returns:
        ee number object: The normalized long-term temperature anomaly for the region of interest.
    """

    temperature_anomaly = get_temperature_anomaly()
    
    min_temperature_anomaly = ee.Number(min_value)
    max_temperature_anomaly = ee.Number(max_value)
    max_minus_min_temperature_anomaly = max_temperature_anomaly.subtract(min_temperature_anomaly)
    

    # Get mean temperature anomaly for region of interest
    temperature_anomaly_region = temperature_anomaly.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region_of_interest,
        scale=90 # Originally 27830
    ).get("mean_2m_air_temperature")

    temperature_anomaly_region = ee.Number(temperature_anomaly_region)
    
    # Normalize temperature anomaly value for region of interest
    temperature_anomaly_region_normalized = (temperature_anomaly_region.subtract(min_temperature_anomaly)).divide(max_minus_min_temperature_anomaly)
    
    return ee.Number(temperature_anomaly_region_normalized).getInfo()










