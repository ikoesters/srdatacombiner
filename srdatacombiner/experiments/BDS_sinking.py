# %%
from pathlib import Path

import xarray as xr
import numpy as np


from srdatacombiner.experiments.experiments import Experiments
from srdatacombiner.sensors.taltech import BDS250


class BDS_Sinking(Experiments):
    def __init__(self) -> None:
        self.datafolder = "../../data/25_01_16_Sink_Experiment"
        self.t_measurement = 6  # s
        self.crop_coord = "time"
        self.coord_names = {
            "trial": self.get_file_coord_from_path,
        }

        self.sensors = {"sensorprobe": Sensorprobe(self)}
        self.interpolation_master_args = (
            "../../data/25_01_16_Sink_Experiment/01/C760116180335.txt",
            "sensorprobe",
        )
        super().__init__()

    def get_file_coord_from_path(self, path: Path) -> float:
        return int(path.parts[-1])


class Sensorprobe:
    def __init__(self, config: Experiments) -> None:
        self.config = config
        self.processor = BDS250
        self.sensor_kwargs = {}
        self.file_glob = "*txt"

        self.sample_rate = 250
        self.cut_threshold = -10
        self.idx_offset = -50
        self.len_measurement = round(config.t_measurement * self.sample_rate)

    def get_crop_idcs(self, ds: xr.Dataset) -> (int, int):
        arr = self.config.savgol_filter(
            ds=ds,
            window_length=500,
            polyorder=2,
            dim="time",
        ).accy.values
        indices = np.where(arr < self.cut_threshold)[0]  # Get indices of values < -10
        idx_start = indices[-1] + self.idx_offset
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


# %%
if __name__ == "__main__":
    import plotly.express as px

    from srdatacombiner.combineFiles import CombineFiles
    from srdatacombiner.helper_scripts.xarray_tools import save_as_h5

    comb = CombineFiles(BDS_Sinking)
    folderlist = comb.folderlist_from_datafolder()
    ds = comb.combine_datasets_from_paths(folderlist)
    # %%
    save_as_h5(ds, "../../data/combined_data", comb.datafolder.name)

# %%
