# %%
import xarray as xr
from pathlib import Path


from srdatacombiner.sensors.taltech import RAPIDv1
from srdatacombiner.sensors.kollmorgen import Kollmorgen
from srdatacombiner.experiments.experiments import Experiments


class RAPIDv1(Experiments):
    def __init__(self) -> None:
        self.datafolder = "../../data/24_08_08_EDF_9.5mmBlade_1mpsSteps_1to10.3mps_30N"
        self.t_measurement = 0.125  # s
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
            "../../data/24_08_08_EDF_9.5mmBlade_1mpsSteps_1to10.3mps_30N/01ms/01/2_T040812151253.txt",
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
        self.processor = RAPIDv1
        self.sensor_kwargs = {}
        self.file_glob = "*.txt"

        self.sample_rate = 2048
        self.idx_offset = -5
        self.thresh_acc_cuttoimpact = 300
        self.len_measurement = round(config.t_measurement * self.sample_rate)

    def get_crop_idcs(self, ds: xr.Dataset) -> (int, int):
        idx_start = (ds.accmag > self.thresh_acc_cuttoimpact).argmax(
            "time"
        ).item() + self.idx_offset
        idx_stop = idx_start + self.len_measurement
        return (idx_start, idx_stop)


class Scope:
    def __init__(self, config: Experiments) -> None:
        self.config = config
        self.processor = Kollmorgen
        self.sensor_kwargs = {}
        self.file_glob = "*.csv"
        self.strike_loc = 0.935  # m

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

    comb = CombineFiles(RAPIDv1)
    folderlist = comb.folderlist_from_datafolder()
    ds = comb.combine_datasets_from_paths(folderlist)
    # %%
    # save_as_h5(ds, "../../data/combined_data", comb.datafolder.name)
