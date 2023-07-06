import os
import numpy as np
import pandas as pd
import geopandas as gpd

################################################################################
################################################################################
##############################   MAIN FUNCTIONS   ##############################
################################################################################
################################################################################

def load_sm_data(base_loc,depth='v2',covariates=None):
    # Read in the raw gauge and soil moisture data
    raw_gauge_data = pd.read_csv(os.path.join(base_loc,'processed','daily_gauge_data.csv'),index_col=0)
    raw_sm_data = pd.read_csv(os.path.join(base_loc,'processed','daily_sm_data.csv'),index_col=0)

    # Read in the location metadata and convert to a GeoDataFrame
    loc_meta = pd.read_csv(os.path.join(base_loc,'Coords.csv'))
    loc_meta = gpd.GeoDataFrame(loc_meta, geometry=gpd.points_from_xy(loc_meta.longitude, loc_meta.latitude))

    # Strip whitespace from the 'loc' column and transform to EPSG 23855
    loc_meta.loc[:,'loc'] = loc_meta.loc[:,'loc'].str.strip()
    loc_meta = loc_meta.set_crs('EPSG:4326')
    loc_meta = loc_meta.to_crs('EPSG:28355')
    
    # select a depth and pivot on day and device to get a dataframe 
    # with one column per probe
    sm_data = raw_sm_data[['Date','device', depth]].pivot(index='Date',columns='device',values=depth)
    #and rename sm gauges 
    sm_data.columns = ['_'.join(_.split(' ')[:-1]).replace('-','_') for _ in sm_data.columns]

    # clean zeros
    sm_data[sm_data==0] = np.nan
    sm_data.index = pd.to_datetime(sm_data.index)  

    # clean external gauge data
    if not covariates is None: 
        covariates_df = raw_gauge_data[covariates].copy()
    else:
        covariates_df = raw_gauge_data

    # drop duplicates and sort
    probe_meta = loc_meta.reset_index(drop=False).copy()
    probe_meta = probe_meta.drop_duplicates(subset=['site','loc','treatment','treatment rep'])
    probe_meta.sort_values(by=['site','loc'],inplace=True)

    if probe_meta['loc'].isin(sm_data.columns).sum() != len(probe_meta):
        raise ImportError('ERROR: not all locations in meta data are in the SM data')

    probe_meta.set_index('loc',inplace=True)

    # now final gauge meta
    probe_meta = probe_meta[['site','treatment','treatment rep']]
    covariates_df.index = pd.to_datetime(covariates_df.index)

    # reorder df_Y to match probe_meta
    sm_data = sm_data[probe_meta.index.tolist()]
    return covariates_df, sm_data, loc_meta, probe_meta

################################################################################
################################################################################
 

################################################################################
################################################################################



################################################################################
################################################################################
