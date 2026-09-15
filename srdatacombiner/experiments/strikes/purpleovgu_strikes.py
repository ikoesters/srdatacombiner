# %%
from pathlib import Path

import plotly.express as px
import xarray as xr

from srdatacombiner.combineFiles import CombineFiles
from srdatacombiner.experiments.strikes.strikes import Scope, Sensorprobe, Strikes
from srdatacombiner.helper_scripts.xarray_tools import save_as_h5
from srdatacombiner.sensors.labjack import Labjack_ovguFish

# Sensorprobe
sp = Sensorprobe(
    processor=Labjack_ovguFish,
    file_glob="probe*",
    sample_rate=Labjack_ovguFish.sample_rate,
    thresh_acc_cuttoimpact=120,
)


def find_impact_idx(ds: xr.Dataset) -> int:
    std = ds["vmid"].isel(time=range(0, 100)).std("time")
    mean = ds["vmid"].isel(time=range(0, 100)).mean("time")
    threshold = 15 * std
    condition = abs(ds["vmid"] - mean) > threshold
    idx_impact = (condition.argmax(dim="time")).values.item()
    return idx_impact


sp.find_impact_idx = find_impact_idx

# Scope
scope = Scope(
    file_glob="*.csv",
    strike_loc=0.98,
)


strikes = Strikes(
    datafolder="../../../data/25_02_10_PurpleOVGUv2_9.5mmBlade_1mpsSteps_1to10mps_5N",
    sensors=[sp, scope],
    interpolation_master_args=(
        "../../../data/25_02_10_PurpleOVGUv2_9.5mmBlade_1mpsSteps_1to10mps_5N/01ms/01/probe_20250210_1326.dat",
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
