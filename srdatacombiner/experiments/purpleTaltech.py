# %%
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from srdatacombiner.experiments.experiments import Experiments
from srdatacombiner.sensors.serialplot import Serialplot_PurpleTaltech
from srdatacombiner.sensors.kollmorgen import Kollmorgen


class PurpleTaltech(Experiments):
    def __init__(self) -> None:
        self.datafolder = (
            "../../data/25_02_17_PurpleTaltech_9.5mmBlade_1to10mps_1mpsSteps_5N"
        )
        self.t_measurement = 0.4  # s
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
            "../../data/25_02_17_PurpleTaltech_9.5mmBlade_1to10mps_1mpsSteps_5N/01ms/01/probe_20250214_1303",
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
        self.processor = Serialplot_PurpleTaltech
        self.sensor_kwargs = {}
        self.file_glob = "probe*"

        self.sample_rate = 5000
        self.idx_offset = -200
        self.len_measurement = round(config.t_measurement * self.sample_rate)

    def get_crop_idcs(self, ds: xr.Dataset) -> (int, int):
        std = ds["accz2"].isel(time=range(0, 1000)).std("time")
        mean = ds["accz2"].isel(time=range(0, 1000)).mean("time")
        threshold = 15 * std
        condition = abs(ds["accz2"] - mean) > threshold
        idx_start = (condition.argmax(dim="time") + self.idx_offset).values.item()
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
        self.file_glob = "*csv"
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

    comb = CombineFiles(PurpleTaltech)
    folderlist = comb.folderlist_from_datafolder()
    ds = comb.combine_datasets_from_paths(folderlist)
    # %%
    save_as_h5(ds, "../../data/combined_data", comb.datafolder.name)

# %%
