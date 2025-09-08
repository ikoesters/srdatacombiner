# %%
import plotly.express as px

from srdatacombiner.combineFiles import CombineFiles
from srdatacombiner.experiments.strikes.strikes import Scope, Sensorprobe, Strikes
from srdatacombiner.helper_scripts.xarray_tools import save_as_h5
from srdatacombiner.sensors.taltech import BDS250

resample_rate = 2000
# Sensorprobe
sp = Sensorprobe(
    processor=BDS250,
    file_glob="*.txt",
    sample_rate=resample_rate,
    thresh_acc_cuttoimpact=75,
    sensor_kwargs={"resample_rate": resample_rate},
)

# Scope
scope = Scope(
    file_glob="*.csv",
)

# Strikes setup
strikes = Strikes(
    datafolder="../../../data/24_07_18_BDS_9.5mmBlade_1mpsSteps_1to5mps_30N",
    sensors=[sp, scope],
    interpolation_master_args=(
        "../../../data/24_07_18_BDS_9.5mmBlade_1mpsSteps_1to5mps_30N/01ms/01/B170718112014.txt",
        sp.label,
    ),
)

comb = CombineFiles(strikes)
# %%
folderlist = comb.folderlist_from_datafolder()
ds = comb.combine_datasets_from_paths(folderlist)
# %%
# save_as_h5(ds, "../../data/combined_data", comb.datafolder.name)
