# %%
import struct
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from numpy.typing import ArrayLike

from srdatacombiner.helper_scripts import xarray_tools
from srdatacombiner.sensors.sensors import Sensors

plt.style.use("seaborn-v0_8-whitegrid")


class Taltech(Sensors):
    def __init__(self, filename: str, resample_rate: int = None) -> None:
        self.filename = Path(filename)
        self.fmt: str
        self.fs: int
        self.units_dict: dict
        self.column_names_raw: list
        self.column_names_selected: list

        super().__init__(filename, resample_rate=resample_rate)
        self.infolist: list[str] = ["Unit", "Range", "Sensor"]
        self.col_rename_dict = {}

    def get_raw_data(self) -> pd.DataFrame:
        with open(self.filename.as_posix(), mode="r+b") as f:
            binary_data = f.read()
        len_fmt = struct.calcsize(self.fmt)
        max_accept_len = (len(binary_data) // len_fmt) * len_fmt
        bin_new = binary_data[0:max_accept_len]
        iter = struct.iter_unpack(self.fmt, bin_new)
        data = [x for x in iter]
        data = pd.DataFrame(data, columns=self.column_names_raw)
        data = data.astype("float")
        data = data.iloc[1:]
        return data

    def post_process(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.set_index("time")
        return df

    def _create_timestamps_from_fs(self, data: pd.DataFrame) -> pd.Series:
        try:  # rounding removes floating point errors
            timestamps = np.round((data["index"] - 1) / self.fs, 10)
        except KeyError:
            timestamps = np.round((data.index - 1) / self.fs, 10)
        return timestamps

    def calculate_acc_mag(self, data: pd.DataFrame) -> pd.Series:
        return np.linalg.norm(data[["accx", "accy", "accz"]], axis=-1)


class BDS(Taltech):
    def __init__(self, filename: str, resample_rate: int = None) -> None:
        self.fmt: str
        self.fs: int
        self.column_names_raw: list[str]

        super().__init__(filename, resample_rate=resample_rate)
        self.units_dict = {
            "time": "s",
            "p": ("mBar", "+/- 2000", "TE Connectivity MS5837-2BA"),
            "acc": ("m/s^2", "+/- 160", "Bosch BNO055"),
            "gyro": ("rad/s", None, "Bosch BNO055"),
        }

    def calculate_average_pressure(self, data: pd.DataFrame) -> ArrayLike:
        """Calculate the average pressure from the three pressure sensors.
        Compute the difference between array and shifted array. Maskes columnn that fails
        the threshold test in both shifts. Returns the median of the masked array.

        Args:
            data (pd.DataFrame): Data dataframe with columns p1, p2, p3

        Returns:
            ArrayLike: Median pressure
        """
        arr = data[["p1", "p2", "p3"]].values

        def column_difference(arr: np.ndarray, shift: int) -> np.ndarray:
            return arr - np.roll(arr, axis=1, shift=shift)

        diff1 = column_difference(arr, shift=1)
        diff2 = column_difference(arr, shift=2)

        def above_thresh(diff: np.ndarray) -> np.ndarray:
            return np.where(np.median(np.abs(diff), axis=0) > 10, np.NAN, 1)

        at1 = above_thresh(diff1)
        at2 = above_thresh(diff2)

        masked_arr = arr.T[~np.isnan(np.vstack((at1, at2))).all(0)].T
        return np.nanmean(masked_arr, axis=1)

    def post_process(self, data: pd.DataFrame) -> pd.DataFrame:
        data["time"] = self._create_timestamps_from_fs(data)
        data["pres"] = self.calculate_average_pressure(data)
        data["accmag"] = self.calculate_acc_mag(data)
        data = data[self.column_names_selected]
        data = super().post_process(data)
        return data


class BDS100(BDS):
    sample_rate: int = 100
    filename_extension: str = ".txt"

    def __init__(self, filename: str, resample_rate: int = None) -> None:
        """
        This class processes BDS measurements at 100 Hz.
        """
        super().__init__(filename, resample_rate=resample_rate)
        self.fmt = "HI22f4B"  # format string to set byteorder
        self.fs = 100
        self.column_names_raw = [
            "sample rate",
            "time",
            "p1",
            "t1",
            "p2",
            "t2",
            "p3",
            "t3",
            "eul head",
            "eul roll",
            "eul pitch",
            "quat w",
            "quatx",
            "quaty",
            "quatz",
            "magx",
            "magy",
            "magz",
            "accx",
            "accy",
            "accz",
            "gyrox",
            "gyroy",
            "gyroz",
            "calmag",
            "calacc",
            "calgyro",
            "calimu",
        ]
        self.column_names_selected = [
            "time",
            "p1",
            "p2",
            "p3",
            "pres",
            "accx",
            "accy",
            "accz",
            "accmag",
            "quat w",
            "quatx",
            "quaty",
            "quatz",
            "absaccx",
            "absaccy",
            "absaccz",
            "gyrox",
            "gyroy",
            "gyroz",
            "magx",
            "magy",
            "magz",
        ]

    def post_process(self, data: pd.DataFrame) -> pd.DataFrame:
        data = self._absolute_orientation(data)
        data = super().post_process(data)
        return data

    def _absolute_orientation(self, data: pd.DataFrame) -> pd.DataFrame:
        import quaternion

        # Translate body acc with earths mag field to abs reference frame
        quat_ref_frame = quaternion.as_quat_array(
            data[["quat w", "quatx", "quaty", "quatz"]]
        )

        abs_acc = np.zeros((0, 3))
        for idx, q in enumerate(quat_ref_frame):
            acc = quaternion.rotate_vectors(q, data.loc[idx + 1, "accx":"accz"])
            abs_acc = np.vstack((abs_acc, acc))
        # abs_acc[:, 2] -= 9.81
        data.insert(5, "absaccx", abs_acc[:, 0])
        data.insert(6, "absaccy", abs_acc[:, 1])
        data.insert(7, "absaccz", abs_acc[:, 2])
        return data


class BDS250(BDS):
    sample_rate: int = 250
    filename_extension: str = ".txt"

    def __init__(self, filename: str, resample_rate: int = None) -> None:
        """
        This class processes BDS measurements at 250 Hz.
        """
        super().__init__(filename, resample_rate=resample_rate)
        self.fmt = "HI12f4B"
        self.fs = 250
        self.column_names_raw = [
            "samplerate",
            "time",
            "p1",
            "t1",
            "p2",
            "t2",
            "p3",
            "t3",
            "accx",
            "accy",
            "accz",
            "gyrox",
            "gyroy",
            "gyroz",
            "calmag",
            "calacc",
            "calgyro",
            "calimu",
        ]
        self.column_names_selected = [
            "time",
            "p1",
            "p2",
            "p3",
            "pres",
            "accx",
            "accy",
            "accz",
            "accmag",
            "gyrox",
            "gyroy",
            "gyroz",
        ]


class RAPID(Taltech):
    def __init__(self, filename: str, calibration_folder: str = None) -> None:
        self.calibration_folder = calibration_folder

        self.gain_list: list
        super().__init__(filename)

        self.gain = pd.Series(self.gain_list, index=self.column_names_raw)

    def load_calibration(self) -> pd.DataFrame:
        df = pd.DataFrame()
        for file in Path(self.calibration_folder).glob("*.txt"):
            df_tmp = pd.read_csv(
                str(file), sep=" =", header=None, index_col=0, engine="python"
            ).T
            df_tmp *= 9.81  # convert g to m/s^2
            df = pd.concat([df, df_tmp])
        df.reset_index(drop=True)
        return df

    def _calibration_fct(
        self, data: pd.Series, offset_odd: float, offset_even: float
    ) -> pd.DataFrame:
        data.iloc[::2] -= offset_even
        data.iloc[1::2] -= offset_odd
        return data

    def calibrate_accel(self, data: pd.DataFrame, calib_avg: pd.DataFrame) -> None:
        data["accx"] = self._calibration_fct(
            data["accx"], calib_avg["oX"], calib_avg["eX"]
        )
        data["accy"] = self._calibration_fct(
            data["accy"], calib_avg["oY"], calib_avg["eY"]
        )
        data["accz"] = self._calibration_fct(
            data["accz"], calib_avg["oZ"], calib_avg["eZ"]
        )
        return data

    def apply_gain(self, data: pd.DataFrame) -> pd.DataFrame:
        return data * self.gain

    def post_process(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.calibration_folder is not None:
            calib_df = self.load_calibration()
            df = self.calibrate_accel(df, calib_avg=calib_df.median())
        df = self.apply_gain(df)
        df["time"] = self._create_timestamps_from_fs(df)
        df["accmag"] = self.calculate_acc_mag(df)
        df = df[self.column_names_selected]
        df = super().post_process(df)
        return df


class RAPIDv1(RAPID):
    sample_rate: int = 2048
    filename_extension: str = ".txt"

    def __init__(
        self,
        filename: str,
        calibration_folder: str = None,
    ) -> None:
        """
        This class processes EDF Prototype measurements at 2048 Hz.
        """
        self.fmt = ">5hx"
        self.fs = 2048
        self.gain_list = [1, 1, 1, 1, 0.1]
        self.column_names_raw = ["index", "accx", "accy", "accz", "pres"]
        super().__init__(filename, calibration_folder)

        self.column_names_selected = ["time", "pres", "accx", "accy", "accz", "accmag"]
        self.units_dict = {
            "time": "s",
            "pres": ("mBar", "+/- 2000", "TE Connectivity MS5837-2BA"),
            "acc": ("m/s^2", "+/- 3924 (=400g)", "STMicroelectronics H3LIS331DL"),
            "accmag": (
                "m/s^2",
                "+/- sqrt(3)*3924 = +/- 6797",
                "STMicroelectronics H3LIS331DL",
            ),
        }

    def _create_timestamps_from_fs(self, data: pd.DataFrame) -> pd.Series:
        return data.index / self.fs


class RAPIDv3_IMP(RAPID):
    sample_rate: int = 2000
    filename_extension: str = ".IMP"

    def __init__(
        self,
        filename: str,
        calibration_folder: str = None,
    ) -> None:
        super().__init__(filename, calibration_folder)
        self.fs = 2000  # in reality 100 Hz, but index follows hig sensor
        self.fmt = ">I9hH2hx"
        self.gain_list = [
            1,
            0.005,
            0.005,
            0.005,
            0.1,
            0.1,
            0.1,
            0.1,
            0.1,
            0.1,
            0.1,
            0.01,
            0.01,
        ]
        self.column_names_raw = [
            "index",
            "accx",
            "accy",
            "accz",
            "gyrox",
            "gyroy",
            "gyroz",
            "magx",
            "magy",
            "magz",
            "pres",
            "temp",
            "bat",
        ]
        self.column_names_selected = [
            "time",
            "pres",
            "accx",
            "accy",
            "accz",
            "accmag",
            "gyrox",
            "gyroy",
            "gyroz",
            "magx",
            "magy",
            "magz",
        ]
        self.units_dict = {
            "time": "s",
            "pres": ("mBar", "+/- 2000", "TE Connectivity MS5837-2BA"),
            "acc.+imp": ("m/s^2", "+/- 160", "Bosch BMX160"),
            "gyro.": ("deg/s", "+/- 2000", "Bosch BMX160"),
            "mag.": ("µT", None, "Bosch BMX160"),
        }
        self.col_rename_dict = {
            "accx": "accximp",
            "accy": "accyimp",
            "accz": "acczimp",
            "accmag": "accmagimp",
        }


class RAPIDv3_HIG(RAPID):
    sample_rate: int = 2000
    filename_extension: str = ".HIG"

    def __init__(
        self,
        filename: str,
        calibration_folder: str = None,
    ) -> None:
        super().__init__(filename, calibration_folder)
        self.fmt = ">I3hx"
        self.gain_list = [
            1,
            0.981,
            0.981,
            0.981,
        ]  # FIXME: This implies g is used here, however is in m/s
        self.column_names_raw = ["index", "accx", "accy", "accz"]
        self.column_names_selected = ["time", "accx", "accy", "accz", "accmag"]
        self.units_dict = {
            "time": "s",
            "acc.+hig": ("m/s^2", "+/- 4000", "STMicroelectronics H3LIS331DL"),
        }


class RAPIDv3:
    def __init__(
        self,
        filename: str | Path,
        calibration_folder: str | Path = None,
        interpolate_method: str | Path = "linear",
    ) -> None:
        self.interpolate_method = interpolate_method
        filename = Path(filename)

        filename_HIG = filename.with_suffix(".HIG")
        filename_IMP = filename.with_suffix(".IMP")

        self.hig = RAPIDv3_HIG(filename_HIG, calibration_folder)
        self.imp = RAPIDv3_IMP(filename_IMP, calibration_folder)

    def get_df(self) -> pd.DataFrame:
        ds = self.get_xarray()
        df = xarray_tools.ds2df(ds)
        return df

    def get_xarray(self) -> xr.Dataset:
        dsimp = self.imp.get_xarray()
        dshig = self.hig.get_xarray()
        dsimp = dsimp.interp_like(dshig, method=self.interpolate_method)
        ds = xr.merge([dsimp, dshig])
        return ds


class Microtag(Sensors):
    sample_rate: int = 100
    filename_extension: str = ".txt"

    def __init__(self, filename) -> None:
        super().__init__(filename)
        self.column_names = [
            "time",
            "bat",
            "pres",
            "temp",
            "accx",
            "accy",
            "accz",
            "gyrox",
            "gyroy",
            "gyroz",
            "magx",
            "magy",
            "magz",
        ]
        self.infolist: list[str] = ["Unit", "Range", "Sensor"]
        self.units_dict = {
            "bat": ("V", None, None),
            "pres": ("mBar", "+/- 2000", "TE Connectivity MS5837-2BA"),
            "temp": ("C", None, None),
            "acc": ("m/s^2", "+/- 160", "Bosch BMX160"),
            "gyro": ("rad/s", "+/- 2000", "Bosch BMX160"),
            "mag": ("µT", None, "Bosch BMX160"),
        }

    def convert_timestamp(self, df: pd.DataFrame) -> pd.DataFrame:
        df["time"] -= df["time"].iloc[0]
        df["time"] /= 1000
        return df

    def get_raw_data(self) -> pd.DataFrame:
        df = pd.read_csv(self.filename, names=self.column_names)
        return df

    def post_process(self, df) -> pd.DataFrame:
        df = self.convert_timestamp(df)
        df = df.set_index("time")
        df["accmag"] = self.calculate_magnitude(df["accx"], df["accy"], df["accz"])
        return df


# %%
if __name__ == "__main__":
    import plotly.express as px

    filename = ""  # your filename here
    self = Microtag(filename=filename)
    self.get_xarray()
    df = self.get_df()
    ds = self.get_xarray()
    # %%
