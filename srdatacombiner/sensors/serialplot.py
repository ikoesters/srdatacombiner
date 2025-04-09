# %%
from pathlib import Path

import numpy as np
import pandas as pd

from srdatacombiner.sensors.sensors import Sensors


class Serialplot(Sensors):
    def __init__(self, filename: str | Path):
        self.sample_rate: int
        super().__init__(filename)

    def create_timestamp(self, df: pd.DataFrame) -> pd.DataFrame:
        df["time"] = np.arange(0, len(df) / self.sample_rate, 1 / self.sample_rate)
        return df

    def post_process(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.create_timestamp(df)
        df = df.set_index("time")
        df["accmag1"] = self.calculate_magnitude(df["accx1"], df["accy1"], df["accz1"])
        df["accmag2"] = self.calculate_magnitude(df["accx2"], df["accy2"], df["accz2"])
        df["accmag3"] = self.calculate_magnitude(df["accx3"], df["accy3"], df["accz3"])
        return df

    def get_raw_data(self) -> pd.DataFrame:
        df = pd.read_csv(self.filename)
        return df


class Serialplot_PurpleTaltech(Serialplot):
    def __init__(self, filename: str | Path):
        self.sample_rate = 5000
        self.col_rename_dict = {
            "timestamp": "time",
            "ADXL373_1_X": "accx1",
            "ADXL373_1_Y": "accy1",
            "ADXL373_1_Z": "accz1",
            "ADXL373_2_X": "accx2",
            "ADXL373_2_Y": "accy2",
            "ADXL373_2_Z": "accz2",
            "ADXL373_3_X": "accx3",
            "ADXL373_3_Y": "accy3",
            "ADXL373_3_Z": "accz3",
        }
        self.infolist: list[str] = ["Unit", "Range", "Sensor"]
        self.units_dict = {
            "time": "s",
            "acc": ("g", "+/- 400", "ADXL373 Analog Devices"),
        }
        super().__init__(filename)


# %%
if __name__ == "__main__":
    import plotly.express as px
    import xarray as xr

    filename = ""  # your filename here
    self = Serialplot_PurpleTaltech(filename)
    ds = self.get_xarray()
    # %%
