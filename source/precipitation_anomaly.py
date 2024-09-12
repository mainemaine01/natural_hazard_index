import ee

def get_precipitation_anomaly():
    # Load data
    chirps_dataset = ee.ImageCollection('UCSB-CHG/CHIRPS/PENTAD')

    # Select bands
    chirps_precipitation = chirps_dataset.select('precipitation')

    # Define a function to calculate the precipitation sum for a given period within a given year
    def precipitation_sum(year, start_date, end_date):
        precipitation_month = chirps_precipitation.filterDate(year + start_date, year + end_date) 
        return precipitation_month.sum()

    # ----- MARCH -----
    precipitation_march_list = []

    # Calculate the precipitation sum for March of each year from 2000 to 2020 and append the results to precipitation_march_list
    for i in range(2000, 2021):
        precipitation_march_list.append(precipitation_sum(str(i), '-03-01', '-03-31'))

    precipitation_march_imageCollection = ee.ImageCollection(precipitation_march_list)
    precipitation_march_mean = precipitation_march_imageCollection.mean()

    # ----- APRIL -----
    precipitation_april_list = []

    # Calculate the precipitation sum for April of each year from 2000 to 2020 and append the results to precipitation_april_list
    for i in range(2000, 2021):
        precipitation_april_list.append(precipitation_sum(str(i), '-04-01', '-04-30'))

    precipitation_april_imageCollection = ee.ImageCollection(precipitation_april_list)
    precipitation_april_mean = precipitation_april_imageCollection.mean()

    # ----- MAY -----
    precipitation_may_list = []

    # Calculate the precipitation sum for May of each year from 2000 to 2020 and append the results to precipitation_may_list
    for i in range(2000, 2021):
        precipitation_may_list.append(precipitation_sum(str(i), '-05-01', '-05-31'))

    precipitation_may_imageCollection = ee.ImageCollection(precipitation_may_list)
    precipitation_may_mean = precipitation_may_imageCollection.mean()

    # ----- Calculate Anomaly -----
    
    # Define a function to calculate the precipitation anomaly for each image in a given month_list and return a list of anomaly images
    def calculate_anomaly_collection(month_list, precipitation_month_mean):
        return month_list.map(lambda image: image.subtract(precipitation_month_mean))
    
    # Calculate precipitation anomaly for MAM and combine into a single ImageCollection
    anomaly_march = calculate_anomaly_collection(ee.ImageCollection(precipitation_march_list), precipitation_march_mean)
    anomaly_april = calculate_anomaly_collection(ee.ImageCollection(precipitation_april_list), precipitation_april_mean)
    anomaly_may = calculate_anomaly_collection(ee.ImageCollection(precipitation_may_list), precipitation_may_mean)

    anomaly_march_april_may_imageCollection = anomaly_march.merge(anomaly_april).merge(anomaly_may)

    # Calculate the maximum monthly precipitation anomaly
    anomaly_march_april_may_max = anomaly_march_april_may_imageCollection.max()

    return anomaly_march_april_may_max
    

def min_max(normalization_reference):
    """
    Calculates the minimum and maximum maximum monthly precipitation anomaly in MAM (March–April–May) season (2000-2020) within the given normalization reference.

    Args:
        normalization_reference (ee FeatureCollection): The reference at which to normalize the variable.

    Returns:
        float: The minimum maximum monthly precipitation anomaly in MAM season within the normalization reference.
        float: The maximum maximum monthly precipitation anomaly in MAM season within the normalization reference.
    """

    anomaly_march_april_may_max = get_precipitation_anomaly()

    # Define a function to compute min and max for each tile
    def get_min_max(tile):
        min_max = anomaly_march_april_may_max.reduceRegion(
            reducer=ee.Reducer.minMax(),
            geometry=tile.geometry(),
            scale=5566,
            maxPixels=1e10
        )
        return tile.set({'min_precipitation': min_max.get('precipitation_min'), 'max_precipitation': min_max.get('precipitation_max')})

    # Apply the function over the fishnet tiles
    min_max_tiles = normalization_reference.map(get_min_max)
    
    # Aggregate the results
    min_maxanomaly_list = min_max_tiles.aggregate_array('min_precipitation').getInfo()
    max_maxanomaly_list = min_max_tiles.aggregate_array('max_precipitation').getInfo()
    
    min_maxanomaly_float = min(min_maxanomaly_list)
    max_maxanomaly_float = max(max_maxanomaly_list)
    
    print(f"Min maximum precipitation anomaly: {min_maxanomaly_float}, Max maximum precipitation anomaly: {max_maxanomaly_float}")

    return min_maxanomaly_float, max_maxanomaly_float


def get_precipitation_anomaly_region(region_of_interest, min_value, max_value):
    """
    Calculates the mean maximum monthly precipitation anomaly in MAM (March–April–May) season (2000-2020) within the given region of interest and normalizes the value at the normalization reference level.

    Args:
        region_of_interest (ee geometry object): The region for which to calculate the hazard index.
        min_value (float): The minimum value of this variable within the normalization reference.
        max_value (float): The maximum value of this variable within the normalization reference.

    Returns:
        ee number object: The normalized maximum monthly precipitation anomaly in MAM season for the region of interest
    """
    
    anomaly_march_april_may_max = get_precipitation_anomaly()
    
    min_anomaly = ee.Number(min_value)
    max_anomaly = ee.Number(max_value)
    max_minus_min_anomaly = max_anomaly.subtract(min_anomaly)

    # Get mean maximum monthly precipitation anomaly in MAM season for region of interest
    anomaly_region = anomaly_march_april_may_max.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region_of_interest,
        scale=90 # Originally 5566 
        ).get("precipitation")

    anomaly_region = ee.Number(anomaly_region)

    # Normalize maximum monthly precipitation anomaly in MAM season value for region of interest
    anomaly_normalized = (anomaly_region.subtract(min_anomaly)).divide(max_minus_min_anomaly)
    
    return ee.Number(anomaly_normalized).getInfo()


    

















