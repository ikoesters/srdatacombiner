# %%
from pathlib import Path

import pandas as pd
import plotly.express as px
import xarray as xr

from srdatacombiner.sensors.sensors import Sensors


class Labjack(Sensors):
    def __init__(self, filename) -> None:
        self.usecols: list[int]
        super().__init__(filename)

    def post_process(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.set_index("time")
        return df

    def get_raw_data(self) -> pd.DataFrame:
        df = pd.read_csv(
            self.filename,
            sep=r"\t",
            skiprows=5,
            usecols=self.usecols,
            engine="python",
        )
        return df


class Labjack_ovguFish(Labjack):
    def __init__(self, filename: str | Path) -> None:
        self.usecols = [0, 1, 2, 3]
        self.col_rename_dict = {
            "Time": "time",
            "v0": "vtail",
            "v1": "vmid",
            "v2": "vhead",
        }
        self.infolist: list[str] = ["Unit", "Range", "Sensor"]
        self.units_dict = {
            "time": "s",
            "v": ("V", "+/- 1.6", "LabJack T7 & custom amplifier"),
        }
        super().__init__(filename)


# %%
if __name__ == "__main__":
    filename = ""  # your filename here
    self = Labjack_ovguFish(filename)
    ds = self.get_xarray()
    # %%
