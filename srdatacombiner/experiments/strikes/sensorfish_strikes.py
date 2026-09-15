# %%
from pathlib import Path

import plotly.express as px

from srdatacombiner.combineFiles import CombineFiles
from srdatacombiner.experiments.strikes.strikes import Scope, Sensorprobe, Strikes
from srdatacombiner.helper_scripts.xarray_tools import save_as_h5
from srdatacombiner.sensors.sensorfish import SensorFish

curr_dir = Path(__file__).parent

G = 9.81  # m/s^2

# Sensorprobe
sp = Sensorprobe(
    processor=SensorFish,
    file_glob="*ms_*.csv",
    sample_rate=SensorFish.sample_rate,
    # Strike onset threshold, above handling accelerations and below those of a
    # 1 m/s strike. The RAPID uses the same value.
    thresh_acc_cuttoimpact=30 * G,
)

# Scope
scope = Scope(
    file_glob="[0-9][0-9][0-9][0-9]*.csv",
)

# Strikes setup
strikes = Strikes(
    datafolder="../../../data/24_07_26_ATS_9.5mmBlade_1mpsSteps_1to8mps_30N",
    sensors=[sp, scope],
    interpolation_master_args=(
        "../../../data/24_07_26_ATS_9.5mmBlade_1mpsSteps_1to8mps_30N/1ms/01/1ms_4_0111_20240726135708.csv",
        sp.label,
    ),
)

comb = CombineFiles(strikes)
# %%
folderlist = comb.folderlist_from_datafolder()
ds = comb.combine_datasets_from_paths(folderlist)
# %%
save_as_h5(ds, curr_dir / "../../../data/combined_data", comb.datafolder.name)
