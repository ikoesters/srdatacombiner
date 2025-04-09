# %%
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from srdatacombiner.experiments.experiments import Experiments
from srdatacombiner.sensors.unsw import UNSW
from srdatacombiner.sensors.kollmorgen import Kollmorgen


class UNSW_Strikes(Experiments):
    def __init__(self) -> None:
        self.datafolder = "../../data/25_02_24_UNSW_9.5mmBlade_1mpsSteps_1to10mps_30N"
        self.t_measurement = 0.5  # s
        self.crop_coord = "time"
        self.coord_names = {
            "strvel": self.get_folder_coord_from_path,
            "trial": self.get_file_coord_from_path,
        }
        self.sensors = {
            "sensorprobe": Sensorprobe(self),
            "servoscope": Scope(self),
        }
        self.interpolation_master_args = (
            "../../data/25_02_24_UNSW_9.5mmBlade_1mpsSteps_1to10mps_30N/01ms/01/2025_02_24_13_25_20_MetaWear_acc.csv",
            "sensorprobe",
        )
        super().__init__()

    def get_folder_coord_from_path(self, path: Path) -> float:
        return float(path.parts[-2][:-2])  # cut off the "ms" at the end

    def get_file_coord_from_path(self, path: Path) -> float:
        return int(path.parts[-1])


class Sensorprobe:
    def __init__(self, config: Experiments) -> None:
        self.config = config
        self.processor = UNSW
        self.sensor_kwargs = {}
        self.file_glob = "*acc.csv"

        self.sample_rate = 400
        self.idx_offset = -15
        self.len_measurement = round(config.t_measurement * self.sample_rate)

    def get_crop_idcs(self, ds: xr.Dataset) -> (int, int):
        idx_start = (ds.accmag > 10).argmax("time").item() + self.idx_offset
        idx_stop = idx_start + self.len_measurement
        return (idx_start, idx_stop)

    def post_process(self, ds: xr.Dataset) -> xr.Dataset:
        ds = self.config.savgol_filter(
            ds=ds,
            window_length=11,
            polyorder=2,
            dim="time",
        )
        return ds


class Scope:
    def __init__(self, config: Experiments) -> None:
        self.config = config
        self.processor = Kollmorgen
        self.sensor_kwargs = {}
        self.file_glob = "*scope*.csv"
        self.strike_loc = 0.98  # m

        self.sample_rate = 4000
        self.len_measurement = round(config.t_measurement * self.sample_rate)

    def get_crop_idcs(self, ds: xr.Dataset) -> (int, int):
        idx_start = abs(ds.pos - self.strike_loc).argmin("time").item()
        idx_stop = idx_start + self.len_measurement
        return (idx_start, idx_stop)


# %%
if __name__ == "__main__":
    import plotly.express as px

    from srdatacombiner.combineFiles import CombineFiles
    from srdatacombiner.helper_scripts.xarray_tools import save_as_h5

    comb = CombineFiles(UNSW_Strikes)
    folderlist = comb.folderlist_from_datafolder()
    ds = comb.combine_datasets_from_paths(folderlist)
    # %%
    # save_as_h5(ds, "../../data/combined_data", comb.datafolder.name)

    # %%
