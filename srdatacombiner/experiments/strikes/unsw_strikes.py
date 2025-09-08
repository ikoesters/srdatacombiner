# %%
import plotly.express as px

from srdatacombiner.combineFiles import CombineFiles
from srdatacombiner.experiments.strikes.strikes import Scope, Sensorprobe, Strikes
from srdatacombiner.helper_scripts.xarray_tools import save_as_h5
from srdatacombiner.sensors.unsw import UNSW

resample_rate = 2000
# Sensorprobe
sp = Sensorprobe(
    processor=UNSW,
    file_glob="*acc.csv",
    sample_rate=resample_rate,
    thresh_acc_cuttoimpact=130,
    sensor_kwargs={"resample_rate": resample_rate},
)

# Scope
scope = Scope(
    file_glob="*scope*.csv",
)

# Strikes setup
strikes = Strikes(
    datafolder="../../../data/25_02_24_UNSW_9.5mmBlade_1mpsSteps_1to10mps_30N",
    sensors=[sp, scope],
    interpolation_master_args=(
        "../../../data/25_02_24_UNSW_9.5mmBlade_1mpsSteps_1to10mps_30N/01ms/01/2025_02_24_13_25_20_MetaWear_acc.csv",
        sp.label,
    ),
)

comb = CombineFiles(strikes)
# %%
folderlist = comb.folderlist_from_datafolder()
ds = comb.combine_datasets_from_paths(folderlist)
# %%
# save_as_h5(ds, "../../data/combined_data", comb.datafolder.name)
