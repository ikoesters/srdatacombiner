# %%
from pathlib import Path

import plotly.express as px
import xarray as xr

from srdatacombiner.combineFiles import CombineFiles
from srdatacombiner.experiments.strikes.strikes import Scope, Sensorprobe, Strikes
from srdatacombiner.helper_scripts.xarray_tools import save_as_h5
from srdatacombiner.sensors.taltech import RAPIDv1

curr_dir = Path(__file__).parent
# %%
# Sensorprobe
sp = Sensorprobe(
    processor=RAPIDv1,
    file_glob="*.txt",
    sample_rate=RAPIDv1.sample_rate,
    thresh_acc_cuttoimpact=300,
    sensor_kwargs={
        "calibration_folder": curr_dir
        / "../../../data/24_08_08_RAPIDv1_9.5mmBlade_1mpsSteps_1to10mps_30N/T04_calibration_files"
    },
)

# Scope
scope = Scope(
    file_glob="*.csv",
)

# Strikes setup
strikes_calib = Strikes(
    datafolder="../../../data/24_08_08_RAPIDv1_9.5mmBlade_1mpsSteps_1to10mps_30N/requires_calib",
    sensors=[sp, scope],
    interpolation_master_args=(
        "../../../data/24_08_08_RAPIDv1_9.5mmBlade_1mpsSteps_1to10mps_30N/requires_calib/01ms/01/2_T040812151253.txt",
        sp.label,
    ),
)
comb = CombineFiles(strikes_calib)
folderlist = comb.folderlist_from_datafolder()
ds_calib = comb.combine_datasets_from_paths(folderlist)
# %%

# Sensorprobe
sp = Sensorprobe(
    processor=RAPIDv1,
    file_glob="*.txt",
    sample_rate=RAPIDv1.sample_rate,
    thresh_acc_cuttoimpact=300,
)

strikes_no_calib = Strikes(
    datafolder="../../../data/24_08_08_RAPIDv1_9.5mmBlade_1mpsSteps_1to10mps_30N/no_calib_needed",
    sensors=[sp, scope],
    interpolation_master_args=(
        "../../../data/24_08_08_RAPIDv1_9.5mmBlade_1mpsSteps_1to10mps_30N/requires_calib/01ms/01/2_T040812151253.txt",
        sp.label,
    ),
)
comb = CombineFiles(strikes_no_calib)

folderlist = comb.folderlist_from_datafolder()
ds_n_calib = comb.combine_datasets_from_paths(folderlist)
# %%
ds = xr.concat([ds_calib, ds_n_calib], dim="strvel")
ds = ds.sortby("strvel")
# %%
# save_as_h5(
#    ds,
#    "../../../data/combined_data",
#    "24_08_08_RAPIDv1_9.5mmBlade_1mpsSteps_1to10mps_30N",
# )

# %%
