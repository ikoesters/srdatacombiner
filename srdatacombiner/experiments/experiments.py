# %%
from abc import ABC
from pathlib import Path
from typing import Any, Callable

import numpy as np
import xarray as xr
from scipy.signal import savgol_filter

from srdatacombiner.helper_scripts import xarray_tools
from srdatacombiner.sensors.sensors import Sensors


class Experiments(ABC):
    def __init__(self) -> None:
        # self.file_globs: dict[str, str]
        self.datafolder: str | Path
        self.sensors: dict[str, Any]
        self.interpolation_master_args: tuple(Sensors, str | Path)
        self.crop_idcs: tuple[int]
        self.crop_coord: str
        self.coord_names = dict[
            str, Callable
        ]  # Maps coordinate names to functions that extract the coordinate from a path
        self.t_measurement: int

        self.interpolation_master = self.get_xarray(*self.interpolation_master_args)

    def isel_crop(self, ds: xr.Dataset) -> xr.Dataset:
        if hasattr(self, "crop_idcs"):
            return ds.isel(time=slice(*self.crop_idcs))
        return ds

    def isel_crop_ds(self, ds: xr.Dataset, crop_idcs) -> xr.Dataset:
        return ds.isel({self.crop_coord: slice(*crop_idcs)})

    def reset_coord(self, ds: xr.Dataset, coord: str) -> xr.Dataset:
        offset = ds[coord].isel({coord: 0}).item()
        new_coord = ds[coord] - offset
        new_coord = np.round(new_coord, 10)  # remove floating point errors
        return ds.assign_coords({coord: new_coord})

    def change_coord(self, ds: xr.Dataset, new_coord: str) -> xr.Dataset:
        # FIXME: This deletes all metadata
        return xarray_tools.df2ds(xarray_tools.ds2df(ds).set_index(new_coord))

    def interpolate_coord(
        self, ds: xr.Dataset, coord: str, interpolation_points: list | tuple
    ) -> xr.Dataset:
        interp_ds = ds.drop_duplicates(dim=coord)
        return interp_ds.interp({coord: interpolation_points})

    def get_xarray(self, filename: str | Path, sensorname: str) -> xr.Dataset:
        sensor_settings = self.sensors[sensorname]
        sensor = sensor_settings.processor(
            filename=filename, **sensor_settings.sensor_kwargs
        )
        ds = sensor.get_xarray()

        if hasattr(self, "crop_coord"):
            crop_idcs = sensor_settings.get_crop_idcs(ds)
            if crop_idcs[0] >= 0:
                ds = self.isel_crop_ds(ds, crop_idcs)
                ds = self.reset_coord(ds, self.crop_coord)
            else:
                ds = xr.full_like(ds, np.nan)
        if hasattr(self, "interpolation_master"):
            ds = ds.interp_like(self.interpolation_master)
        if hasattr(sensor_settings, "post_process"):
            ds = sensor_settings.post_process(ds)
        return ds

    def savgol_filter(
        self, ds: xr.Dataset, window_length: int, polyorder: int, dim: str
    ) -> xr.Dataset:
        ds_filtered = ds.copy()
        for var in ds.data_vars:
            if (
                dim in ds[var].dims
            ):  # Only apply filter if dimension exists in the variable
                ds_filtered[var] = ds[var].copy(
                    data=savgol_filter(
                        ds[var],
                        window_length=window_length,
                        polyorder=polyorder,
                        axis=ds[var].get_axis_num(dim),
                    )
                )
        return ds_filtered
