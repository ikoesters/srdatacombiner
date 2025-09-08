# %%
from pathlib import Path

import xarray as xr

from srdatacombiner.experiments.experiments import Experiments


class CombineFiles:
    def __init__(
        self,
        experiment_class: Experiments,
    ):
        self.exp = experiment_class
        self.datafolder = Path(self.exp.datafolder)

    def folderlist_from_datafolder(self) -> list[Path]:
        file_glob = self.exp.sensors[self.exp.interpolation_master_args[1]].file_glob
        filelist = [p.parents[0] for p in self.datafolder.rglob(file_glob)]
        return sorted(filelist)

    def get_all_coords(self, folderlist: list[Path]) -> dict[str, list]:
        coords = {key: [] for key in self.exp.coord_names.keys()}
        for p in folderlist:
            coord = self.get_coords(p)
            for key, val in coord.items():
                if val[0] not in coords[key]:
                    coords[key].append(val[0])
        return coords

    def get_coords(self, folderpath: Path) -> dict[str, list]:
        coord = {}
        for key, val in self.exp.coord_names.items():
            coord[key] = [val(folderpath)]
        return coord

    def get_ds_filepaths(self, folderpath: Path, coord: dict) -> xr.Dataset:
        file_paths = {}
        for key, val in self.exp.sensors.items():
            file_paths[key] = next(folderpath.glob(val.file_glob))
        ds = xr.Dataset(data_vars=file_paths, coords=coord)
        return ds

    def get_ds_data(self, folderpath: Path, coord: dict) -> xr.Dataset:
        data = []
        for key, val in self.exp.sensors.items():
            filepath = next(folderpath.glob(val.file_glob))
            data.append(self.exp.get_xarray(filepath, key))
        ds = xr.merge(data)
        ds = ds.expand_dims(coord)
        return ds

    def combine_datasets_from_paths(self, folderlist: list[Path]) -> xr.Dataset:
        ds = self.create_empty_ds(folderlist)
        filepath_datasets = []
        data_datasets = []
        for p in folderlist:
            coord = self.get_coords(p)
            filepath_ds = self.get_ds_filepaths(p, coord)
            filepath_datasets.append(filepath_ds)
            data_ds = self.get_ds_data(p, coord)
            data_datasets.append(data_ds)

        datasets = filepath_datasets + data_datasets
        ds = xr.combine_by_coords(datasets, combine_attrs="override")
        ds = self.cast_paths_to_str(ds)
        return ds

    def cast_paths_to_str(self, ds: xr.Dataset) -> xr.Dataset:
        for key in self.exp.sensors.keys():
            ds[key] = ds[key].astype(str)
        return ds

    def create_empty_ds(self, folderlist: list[Path]) -> xr.Dataset:
        coords = self.get_all_coords(folderlist)
        ds = xr.Dataset(coords=coords)
        return ds
