# %%
from pathlib import Path

import plotly.express as px
import xarray as xr

from srdatacombiner.combineFiles import CombineFiles
from srdatacombiner.experiments.strikes.strikes import Scope, Sensorprobe, Strikes
from srdatacombiner.helper_scripts.xarray_tools import save_as_h5
from srdatacombiner.sensors.serialplot import Serialplot_Stickfish

# Sensorprobe
sp = Sensorprobe(
    processor=Serialplot_Stickfish,
    file_glob="probe*",
    sample_rate=Serialplot_Stickfish.sample_rate,
    thresh_acc_cuttoimpact=100,
)


def find_impact_idx(ds: xr.Dataset) -> int:
    idx_impact = (ds.accmag2 > sp.thresh_acc_cuttoimpact).argmax("time").item()
    return idx_impact


def find_impact_idx(ds: xr.Dataset) -> (int, int):
    std = ds["accz2"].isel(time=range(0, 1000)).std("time")
    mean = ds["accz2"].isel(time=range(0, 1000)).mean("time")
    threshold = 15 * std
    condition = abs(ds["accz2"] - mean) > threshold
    idx_impact = (condition.argmax(dim="time")).values.item()
    return idx_impact


sp.find_impact_idx = find_impact_idx

# Scope
scope = Scope(
    file_glob="*.csv",
    strike_loc=0.98,
)


strikes = Strikes(
    datafolder="../../../data/25_02_17_PurpleTaltech_9.5mmBlade_1to10mps_1mpsSteps_5N",
    sensors=[sp, scope],
    interpolation_master_args=(
        "../../../data/25_02_17_PurpleTaltech_9.5mmBlade_1to10mps_1mpsSteps_5N/01ms/01/probe_20250214_1303",
        sp.label,
    ),
)


comb = CombineFiles(strikes)
# %%
folderlist = comb.folderlist_from_datafolder()
ds = comb.combine_datasets_from_paths(folderlist)
# %%
save_as_h5(ds, "../../../data/combined_data", comb.datafolder.name)

# %%
