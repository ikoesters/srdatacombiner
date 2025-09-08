# %%
from pathlib import Path

import plotly.express as px

from srdatacombiner.combineFiles import CombineFiles
from srdatacombiner.experiments.strikes.strikes import Scope, Sensorprobe, Strikes
from srdatacombiner.helper_scripts.xarray_tools import save_as_h5
from srdatacombiner.sensors.serialplot import Serialplot_Stickfish

# Sensorprobe
sp = Sensorprobe(
    processor=Serialplot_Stickfish,
    file_glob="probe*",
    sample_rate=Serialplot_Stickfish.sample_rate,
    thresh_acc_cuttoimpact=120,
)


# Scope
scope = Scope(
    file_glob="*.csv",
    strike_loc=0.98,
)


# Strikes setup
def get_folder_coord_from_path(path: Path) -> float:
    return float(path.parts[-2][:-3])  # cut off the "mps" at the end


strikes = Strikes(
    datafolder="../../../data/25_05_13_PurpleTaltech_9.5mm_1to8mps_1mpsSteps_30N",
    sensors=[sp, scope],
    interpolation_master_args=(
        "../../../data/25_05_13_PurpleTaltech_9.5mm_1to8mps_1mpsSteps_30N/01mps/01/probe_20250516_1054",
        sp.label,
    ),
    get_folder_coord_from_path=get_folder_coord_from_path,
)


comb = CombineFiles(strikes)
# %%
folderlist = comb.folderlist_from_datafolder()
ds = comb.combine_datasets_from_paths(folderlist)
# %%
save_as_h5(ds, "../../../data/combined_data", comb.datafolder.name)

# %%
