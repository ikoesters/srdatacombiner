# %%
from pathlib import Path

import pandas as pd
import xarray as xr

from srdatacombiner.helper_scripts import xarray_tools
from srdatacombiner.sensors.sensors import Sensors


class ATS(Sensors):
    def __init__(self, filename: str | Path) -> None:
        self.filename = filename
        self.col_rename_dict = {
            "Acc_x": "accx",
            "Acc_y": "accy",
            "Acc_z": "accz",
            "Acc": "accmag",
            "Pressure": "pres",
            "Temprature": "temp",
            "Temperature": "temp",
            "Voltage": "volt",
            "Gyro_x": "gyrox",
            "Gyro_y": "gyroy",
            "Gyro_z": "gyroz",
            "Gyro": "gyromag",
            "Mag_x": "magx",
            "Mag_y": "magy",
            "Mag_z": "magz",
            "Mag": "magmag",
        }
        self.infolist: list[str] = ["Unit", "Range", "Sensor"]
        self.units_dict = {
            "time": "s",
            "pres": ("mBar", "+/- 6000", "Measurement Specialties MS5412-BM"),
            "acc.": ("m/s^2", "+/- 1962 (=200g)", "Analog Devices ADXL377"),
            "gyro.": ("deg/s", "+/- 2000 per axis", "IvenSense ITG-3200"),
            "mag.": ("µT", "+/- 810", "STMicroelectronics LSM303DLHC"),
            "temp": ("°C", "-40,+125", "Microchip Technology TC1046"),
            "accmag": (
                "m/s^2",
                "+/- sqrt(3)*1962 = +/- 3398",
                "Analog Devices ADXL377",
            ),
            "gyromag": ("deg/s", "+/- sqrt(3)*2000 = +/- 3464", "IvenSense ITG-3200"),
            "magmag": (
                "µT",
                "+/- sqrt(3)*810 = +/- 1403",
                "STMicroelectronics LSM303DLHC",
            ),
        }
        super().__init__(filename)

    def post_process(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.convert_units_to_SI(df)
        return df

    def convert_units_to_SI(self, df: pd.DataFrame) -> pd.DataFrame:
        df.loc[:, "accx":"accmag"] *= 9.81  # convert G to m/s^2
        df["pres"] *= 68.9476  # convert psia to mBar
        df.loc[:, "magx":"magmag"] *= 1e2  # convert Gauss to µT
        return df

    def get_raw_data(self) -> pd.DataFrame:
        return pd.read_csv(
            self.filename,
            header=0,
            skiprows=[1],
            index_col=0,
            skipinitialspace=True,
        )


# %%
if __name__ == "__main__":
    import plotly.express as px

    filename = ""  # your filename here
    self = ATS(filename=filename)
    ds = self.get_xarray()
    px.line(ds.accmag)

# %%
