import ee

def get_precipitation_coefficient_variation():
    # Load data
    chirps_dataset = ee.ImageCollection('UCSB-CHG/CHIRPS/PENTAD')

    # Select bands
    chirps_precipitation = chirps_dataset.select('precipitation')

    # Define function to calculate precipitation sum for a given year
    def sum_year(year):
        start_date = ee.Date.fromYMD(year, 1, 1)
        end_date = start_date.advance(1, 'year')
        one_year = chirps_precipitation.filterDate(start_date, end_date)
        return one_year.sum().set('year', year)

    years = ee.List.sequence(1990, 2020)

    # Calculate the annual precipitation sum for the years 1990-2020
    sum_year_images = years.map(lambda year: sum_year(ee.Number(year)))

    # Convert the list to an ImageCollection
    sum_year_imageCollection = ee.ImageCollection(sum_year_images)

    # Calculate the annual mean precipitation between 1990 and 2020
    precipitation_1990_2020_mean = sum_year_imageCollection.mean()
    
    # Calculate the standard deviation of the annual precipitation sum between 1990-2020
    annual_precipitation_sd = sum_year_imageCollection.reduce(ee.Reducer.stdDev())

    # Calculate the coefficient of variation
    precipitation_cv = annual_precipitation_sd.divide(precipitation_1990_2020_mean)

    return precipitation_cv
    

def min_max(normalization_reference):
    """
    Calculates the the minimum and maximum interannual coefficient of variation regarding precipitation (1990-2020) within the given normalization reference.

    Args:
        normalization_reference (ee FeatureCollection): The reference at which to normalize the variable.

    Returns:
        float: The minimum interannual coefficient of variation regarding precipitation within the normalization reference.
        float: The maximum interannual coefficient of variation regarding precipitation within the normalization reference.
    """

    precipitation_cv = get_precipitation_coefficient_variation()

    # Define a function to compute min and max for each tile
    def get_min_max(tile):
        min_max = precipitation_cv.reduceRegion(
            reducer=ee.Reducer.minMax(),
            geometry=tile.geometry(),
            scale=5566,
            maxPixels=1e10
        )
        return tile.set({'min_precipitation_stdDev': min_max.get('precipitation_stdDev_min'), 'max_precipitation_stdDev': min_max.get('precipitation_stdDev_max')})

    # Apply the function over the fishnet tiles
    min_max_tiles = normalization_reference.map(get_min_max)
    
    # Aggregate the results
    min_cv_list = min_max_tiles.aggregate_array('min_precipitation_stdDev').getInfo()
    max_cv_list = min_max_tiles.aggregate_array('max_precipitation_stdDev').getInfo()
    
    min_cv_float = min(min_cv_list)
    max_cv_float = max(max_cv_list)

    print(f"Min precipitation cv: {min_cv_float}, Max precipitation cv: {max_cv_float}")

    return min_cv_float, max_cv_float

    
def get_precipitation_coefficient_variation_region(region_of_interest, min_value, max_value):
    """
    Calculates the mean interannual coefficient of variation regarding precipitation (1990-2020) within the given region of interest and normalizes the value at the normalization reference level.

    Args:
        region_of_interest (ee geometry object): The region for which to calculate the hazard index.
        min_value (float): The minimum value of this variable within the normalization reference.
        max_value (float): The maximum value of this variable within the normalization reference.

    Returns:
        ee number object: The normalized interannual coefficient of variation regarding precipitation for the region of interest.
    """

    precipitation_cv = get_precipitation_coefficient_variation()
    
    min_cv = ee.Number(min_value)
    max_cv = ee.Number(max_value)
    max_minus_min_cv = max_cv.subtract(min_cv)
    
    # Get mean precipitation coefficient of variation for region of interest
    mean_region_precip_cv = precipitation_cv.reduceRegion(
        reducer=ee.Reducer.mean(), 
        geometry=region_of_interest, 
        scale= 90, # Originally 5566
        maxPixels=1e10
    ).get("precipitation_stdDev")

    cv_region = ee.Number(mean_region_precip_cv)

    # Normalize precipitation coefficient of variation value for region of interest
    cv_normalized = (cv_region.subtract(min_cv)).divide(max_minus_min_cv)
    
    return ee.Number(cv_normalized).getInfo()


























