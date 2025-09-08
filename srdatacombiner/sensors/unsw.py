# %%
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from srdatacombiner.helper_scripts import xarray_tools
from srdatacombiner.sensors.sensors import Sensors


class UNSW:
    sample_rate: int = 396
    filename_extension: str = ".csv"

    def __init__(
        self,
        filename: str | Path,
        interpolate_method: str | Path = "linear",
        resample_rate: int = None,
    ) -> None:
        self.filename = Path(filename)

        self.pres_file_glob = "*_pressure.csv"
        self.acc_file_glob = "*_acc.csv"
        self.filename_pres = next(self.filename.parent.glob(self.pres_file_glob))
        self.filename_acc = next(self.filename.parent.glob(self.acc_file_glob))

        self.interpolate_method = interpolate_method
        self.resample_rate = resample_rate

        self.pres_obj = UNSW_Pres(self.filename_pres)
        self.acc_obj = UNSW_Acc(self.filename_acc)

    def get_xarray(self) -> pd.DataFrame:
        dspres = self.pres_obj.get_xarray()
        dsacc = self.acc_obj.get_xarray()
        dspres = dspres.interp_like(dsacc, method=self.interpolate_method)
        ds = xr.merge([dsacc, dspres])
        ds = ds.drop_duplicates(dim="time")

        if self.resample_rate is not None:
            ds = ds.interp(
                time=np.arange(ds.time[0], ds.time[-1], 1 / self.resample_rate)
            )
        return ds

    def get_df(self) -> pd.DataFrame:
        ds = self.get_xarray()
        df = xarray_tools.ds2df(ds)
        return df


class UNSW_Common(Sensors):
    def convert_timestamp(self, df: pd.DataFrame) -> pd.DataFrame:
        df["time"] -= df["time"].iloc[0]
        df["time"] /= 1000
        return df

    def get_raw_data(self) -> pd.DataFrame:
        df = pd.read_csv(self.filename)
        return df

    def post_process(self, df) -> pd.DataFrame:
        df = self.convert_timestamp(df)
        df = df.set_index("time")
        return df


class UNSW_Pres(UNSW_Common):
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.infolist: list[str] = ["Unit", "Range", "Sensor"]

        self.col_rename_dict = {
            "Date": "time",
            " Pressure(mbar)": "pres",
            " Temperature(C)": "temp",
        }
        self.units_dict = {
            "pres": ("mbar", "+/- 160", "TE-Connectivity MS580314BA01-00"),
            "temp": "C",
        }

    def post_process(self, df) -> pd.DataFrame:
        df = super().post_process(df)
        df = df[df["pres"] > 1000]  # Remove invalid data
        return df


class UNSW_Acc(UNSW_Common):
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.infolist: list[str] = ["Unit", "Range", "Sensor"]
        self.col_rename_dict = {
            "Date": "time",
            "x-axis": "accx",
            "y-axis": "accy",
            "z-axis": "accz",
        }
        self.units_dict = {
            "acc": ("m/s^2, +/- 160", "Bosch BMI160"),
        }

    def post_process(self, df):
        df = super().post_process(df)

        df = df.loc[:, ["accx", "accy", "accz"]] * 9.81
        df["accmag"] = (df["accx"] ** 2 + df["accy"] ** 2 + df["accz"] ** 2) ** 0.5
        return df


# %%
if __name__ == "__main__":
    import plotly.express as px
    from matplotlib import pyplot as plt

    plt.style.use("seaborn-v0_8-whitegrid")

    filename = ""  # your filename here
    self = UNSW(filename=filename, resample_rate=200)
    ds = self.get_xarray()
# %%
