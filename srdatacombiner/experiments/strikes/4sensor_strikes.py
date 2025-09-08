# %%
from pathlib import Path

import numpy as np
import xarray as xr

from srdatacombiner.experiments.strikes import (
    bds_strikes,
    rapid_strikes,
    sensorfish_strikes,
    unsw_strikes,
)
from srdatacombiner.helper_scripts.xarray_tools import save_as_h5

# %%
ds_sf = sensorfish_strikes.ds
ds_rapid = rapid_strikes.ds
ds_bds = bds_strikes.ds
ds_unsw = unsw_strikes.ds

# Interpolate all datasets to match ds_ats time coordinates
target_time = ds_sf["time"]
ds_rapid = ds_rapid.interp(time=target_time)
ds_bds = ds_bds.interp(time=target_time)
ds_unsw = ds_unsw.interp(time=target_time)
# %%
ds = xr.concat([ds_sf, ds_rapid, ds_bds, ds_unsw], dim="sensor").assign_coords(
    sensor=["sf", "rapid", "bds", "unsw"]
)
for var in ds.data_vars:
    ds[var].attrs = {}
# %%
save_as_h5(ds, "../../data/combined_data/", "25_05_28_4sensors")

# %%
