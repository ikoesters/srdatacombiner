# %%
from pathlib import Path
from typing import Callable

import xarray as xr

from srdatacombiner.experiments.experiments import Experiments
from srdatacombiner.sensors.kollmorgen import Kollmorgen
from srdatacombiner.sensors.sensors import Sensors


class Strikes(Experiments):
    t_minus_impact = -1 / 200  # s
    t_plus_impact = 1 / 10  # s

    def __init__(
        self,
        datafolder: str,
        sensors: list,
        interpolation_master_args: tuple,
        get_folder_coord_from_path: Callable = None,
        get_file_coord_from_path: Callable = None,
    ) -> None:
        curr_dir = Path(__file__).parent
        self.datafolder = curr_dir / datafolder
        self.interpolation_master_args = [
            curr_dir / interpolation_master_args[0],
            interpolation_master_args[1],
        ]
        self.sensors = {s.label: s for s in sensors}

        if get_folder_coord_from_path is not None:
            self.get_folder_coord_from_path = get_folder_coord_from_path
        if get_file_coord_from_path is not None:
            self.get_file_coord_from_path = get_file_coord_from_path
        self.crop_coord = "time"

        super().__init__()

        self.coord_names = {
            "strvel": self.get_folder_coord_from_path,
            "trial": self.get_file_coord_from_path,
        }

    @staticmethod
    def get_folder_coord_from_path(path: Path) -> float:
        return float(path.parts[-2][:-2])

    @staticmethod
    def get_file_coord_from_path(path: Path) -> float:
        return int(path.parts[-1])


class Sensorprobe:
    def __init__(
        self,
        processor: Sensors,
        file_glob: str,
        sample_rate: int,
        thresh_acc_cuttoimpact: float,
        sensor_kwargs: dict = {},
        label: str = "sensorprobe",
        post_process_fct: Callable = None,
    ) -> None:
        self.processor = processor
        self.sample_rate = sample_rate
        self.file_glob = file_glob
        self.thresh_acc_cuttoimpact = thresh_acc_cuttoimpact
        self.sensor_kwargs = sensor_kwargs
        self.label = label
        if post_process_fct is not None:
            self.post_process = post_process_fct

    def find_impact_idx(self, ds: xr.Dataset) -> int:
        idx_impact = (ds.accmag > self.thresh_acc_cuttoimpact).argmax("time").item()
        return idx_impact

    def get_crop_idcs(self, ds: xr.Dataset) -> (int, int):
        idx_impact = self.find_impact_idx(ds)
        idx_start = idx_impact + round(Strikes.t_minus_impact * self.sample_rate)
        idx_stop = idx_impact + round(Strikes.t_plus_impact * self.sample_rate)
        return (idx_start, idx_stop)


class Scope:
    def __init__(
        self,
        file_glob,
        sensor_kwargs: dict = {},
        sample_rate: int = 4000,
        strike_loc: float = 0.935,  # m
        label: str = "servoscope",
        processor: Sensors = Kollmorgen,
    ) -> None:
        self.file_glob = file_glob
        self.sensor_kwargs = sensor_kwargs
        self.sample_rate = sample_rate
        self.strike_loc = strike_loc
        self.label = label
        self.processor = processor

    def find_impact_idx(self, ds: xr.Dataset) -> int:
        idx_impact = abs(ds.pos - self.strike_loc).argmin("time").item()
        return idx_impact

    def get_crop_idcs(self, ds: xr.Dataset) -> (int, int):
        idx_impact = self.find_impact_idx(ds)
        idx_start = idx_impact + round(Strikes.t_minus_impact * self.sample_rate)
        idx_stop = idx_impact + round(Strikes.t_plus_impact * self.sample_rate)
        return (idx_start, idx_stop)


# %%
