# %%
import numpy as np
import pandas as pd
import xarray as xr
from pathlib import Path
from srdatacombiner.sensors.sensors import Sensors
from srdatacombiner.helper_scripts import xarray_tools


class Kollmorgen(Sensors):
    def __init__(
        self,
        filename: str | Path,
        use_cols: list | tuple = (0, 1, 2, 3, 4, 5),
        crop_to_traj: bool = True,
        index: str = "time",
        **kwargs,
    ) -> None:
        self.filename = filename
        self.use_cols = use_cols
        self.crop_to_traj = crop_to_traj
        self.index = index

        self.effective_diam_pulley = 122.23e-3  # m

        self.units_dict = {
            "time": "s",
            "curr": ("A", "Kollmorgen AKD-P01207-NBCC-E00", "Siemens 1FT6102-8AC71"),
            "vel": ("m/s", "Kollmorgen AKD-P01207-NBCC-E00", "Siemens 1FT6102-8AC71"),
            "pos": ("m", "Kollmorgen AKD-P01207-NBCC-E00", "Siemens 1FT6102-8AC71"),
        }
        self.infolist = ["Unit", "Sensor", "Motor"]
        self.col_rename_dict = {
            "Time[ms]": "time",
            "VL.CMD([Axis1] Velocity command)[rpm]": "velcom",
            "VL.CMD - [Axis1] Velocity command(VL.CMD - [Axis1] Velocity command)[rpm]": "velcom",
            "VL.FB([Axis1] Velocity feedback)[rpm]": "vel",
            "VL.FB - [Axis1] Velocity feedback(VL.FB - [Axis1] Velocity feedback)[rpm]": "vel",
            "PL.FB([Axis1] Position feedback)[Counts16Bit]": "pos",
            "PL.FB - [Axis1] Position feedback(PL.FB - [Axis1] Position feedback)[Counts16Bit]": "pos",
            "IL.FB([Axis1] Current feedback)[Arms]": "curr",
            "IL.FB - [Axis1] Current feedback(IL.FB - [Axis1] Current feedback)[Arms]": "curr",
            "DOUT1.STATE(Digital output 1 state)[-]": "dout1",
            "DOUT1.STATE - Digital output 1 state(DOUT1.STATE - Digital output 1 state)[-]": "dout1",
            "VBUS.VALUE - Bus voltage(VBUS.VALUE - Bus voltage)[Vdc]": "vbus",
        }

        # Overwrite attributes
        self.__dict__.update(kwargs)

        super().__init__(filename)

    def rpm2ms(self, rpm: float | np.ndarray) -> float | np.ndarray:
        """Calculate the linear velocity in m/s
        given the rpm of the motor using the effective diameter
        of the pulley (defined in outer scope)

        Args:
            rpm (float | np.ndarray): rounds per minute of the motor

        Returns:
            float | np.ndarray: velocity in metres/second
        """
        vel = rpm * (np.pi * self.effective_diam_pulley) / 60
        return vel

    def pos2m(self, pos: float | np.ndarray) -> float | np.ndarray:
        """Calculate the position in metres from the home position
        given the position feedback from the servocontroller.

        Args:
            pos (float | np.ndarray): position feedback

        Returns:
            float | np.ndarray: position in metres
        """
        pos /= 2**16
        m = pos * np.pi * self.effective_diam_pulley
        return m

    def if_german_locale(self) -> bool:
        with open(self.filename) as f:
            german_locale = True if f.readline().find(";") >= 1 else False
        return german_locale

    def get_raw_data(self) -> pd.DataFrame:
        german_locale = self.if_german_locale()
        sep = ";" if german_locale else ","
        decimal = "," if german_locale else "."
        df = pd.read_csv(
            self.filename, sep=sep, decimal=decimal, usecols=self.use_cols, header=0
        )
        return df

    def get_endoftraj_idx(self, df: pd.DataFrame) -> (int, int):
        end_pos = df.pos.max() - 0.005
        idx = df[df["pos"] >= end_pos].index[0]
        return idx

    def post_process(self, df: pd.DataFrame) -> pd.DataFrame:
        df["time"] /= 1000
        df[["velcom", "vel"]] = self.rpm2ms(df[["velcom", "vel"]])
        df["pos"] = self.pos2m(df["pos"])
        if self.crop_to_traj == True:
            df = df.iloc[0 : self.get_endoftraj_idx(df)]
        df = df.set_index(self.index)
        return df


# %%
if __name__ == "__main__":
    filename = ""  # your filename here
    self = Kollmorgen(filename=filename)
    ds = self.get_xarray()

    # %%
