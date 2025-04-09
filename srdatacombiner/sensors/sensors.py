# %%
import pandas as pd
import numpy as np
import xarray as xr
from pathlib import Path
from srdatacombiner.helper_scripts import xarray_tools
from abc import ABC, abstractmethod

# %%


class Sensors(ABC):
    def __init__(
        self,
        filename: str | Path,
    ) -> None:
        self.filename = Path(filename)

        self.units_dict: dict
        self.infolist: list[str]
        self.col_rename_dict: dict

    @abstractmethod
    def post_process(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError("Must be implemented in subclass")

    @abstractmethod
    def get_raw_data(self) -> pd.DataFrame:
        raise NotImplementedError("Must be implemented in subclass")

    def rename_cols(self, df: pd.DataFrame) -> pd.DataFrame:
        if hasattr(self, "col_rename_dict"):
            df.rename(columns=self.col_rename_dict, inplace=True)
        return df

    def get_df(self) -> pd.DataFrame:
        df = self.get_raw_data()
        df = self.rename_cols(df)
        df = self.post_process(df)
        return df

    def get_xarray(self) -> xr.Dataset:
        df = self.get_df()
        ds = xarray_tools.df2ds(df)
        if hasattr(self, "coords"):
            ds = ds.assign_coords(self.coords)
        if hasattr(self, "units_dict") and hasattr(self, "infolist"):
            ds = xarray_tools.assign_datavar_info(
                ds,
                units_dict=self.units_dict,
                infonames=self.infolist,
            )
        ds = xarray_tools.set_attr_timestamp(ds)
        return ds

    def save_as_csv(self, df: pd.DataFrame, folder: str | Path, **kwargs) -> None:
        folder = Path(folder)
        self._mkdir(folder)
        df.to_csv(
            (folder / self.filename.stem).with_suffix(".csv"),
            sep=",",
            index=False,
            **kwargs,
        )

    def _mkdir(self, path_object: Path) -> None:
        path_object.mkdir(parents=True, exist_ok=True)

    def calculate_magnitude(
        self,
        *dataarrays: xr.DataArray | pd.Series,
    ) -> xr.DataArray | pd.Series:
        return np.sqrt(sum(da**2 for da in dataarrays))
