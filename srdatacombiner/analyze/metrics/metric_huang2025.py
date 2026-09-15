# %%
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from scipy.signal import find_peaks

from srdatacombiner.analyze.metrics.metric_base import MetricBase
from srdatacombiner.analyze.metrics.metric_peak_accmag import (
    G,
    MORTALITY_THRESHOLD_G,
)


class MvMetricHuang2025(MetricBase):
    def __init__(self, ds: xr.Dataset) -> None:
        super().__init__(ds)

        self.offset_indices: np.ndarray = np.array(range(-3, 3 + 1))
        # The 95 g event threshold of Deng et al. (2010), the same value the
        # peak acceleration magnitude metric uses.
        self.peak_height: float = MORTALITY_THRESHOLD_G * G  # m/s^2
        self.peak_distance: int = 7

        self.delta_t: float = np.mean(np.gradient(ds.time))

        self.figname: str = "acc_metric.pdf"
        self.metric_label: str = "Huang2025 Mv Metric"

    def calculate_metric(self, ds: xr.Dataset) -> np.ndarray:
        ds_acc_sum = ds.sum("time")
        ds_accmag = self.euclidean_norm(ds_acc_sum)
        ds_accmag = ds_accmag * self.delta_t
        res = ds_accmag.values
        return res

    def select_data(self, ds_sel, index_peak: int) -> xr.Dataset:
        ds_sel = super().select_data(ds_sel, index_peak)
        ds_acc = ds_sel[["accx", "accy", "accz"]]
        return ds_acc

    def find_peak(self, ds: xr.Dataset) -> np.ndarray:
        index_peak, _ = find_peaks(
            ds.accmag, height=self.peak_height, distance=self.peak_distance
        )
        return index_peak

    @staticmethod
    def euclidean_norm(ds: xr.Dataset) -> xr.DataArray:
        return (ds["accx"] ** 2 + ds["accy"] ** 2 + ds["accz"] ** 2) ** 0.5

    @staticmethod
    def select_result(res_list: list) -> [float, int]:
        # Select the result with the maximum value
        res_list = np.array(res_list)
        index_max = np.argmax(res_list)
        sel_res = res_list[index_max]
        return sel_res, index_max


class MpMetricHuang2025(MetricBase):
    def __init__(
        self,
        ds: xr.Dataset,
        peak_da: xr.DataArray,
    ) -> None:
        super().__init__(ds)
        self.dx = np.mean(np.gradient(ds.time))
        peak_da = peak_da.rename("peaks")
        self.ds = xr.merge([ds, peak_da])

        self.p1_offset_indices: np.ndarray = np.array(range(-7, -3 + 1))
        self.p2_offset_indices: np.ndarray = np.array(range(-2, 2 + 1))

        self.rho_h20: float = 998  # kg/m^3
        self.mbar_to_pa: float = 100  # Pa/mBar

        self.figname: str = "pres_metric.pdf"
        self.metric_label: str = "Huang2025 Mp Metric"

    def find_peak(self, ds: xr.Dataset) -> int:
        idx_slice = ds["peaks"].item() + self.p2_offset_indices
        if not np.isnan(idx_slice).any():
            idx_slice = idx_slice.astype(int)
            p2_peak = ds["pres"].isel(time=idx_slice).argmax("time")
        else:
            p2_peak = np.nan
        return [p2_peak]

    @staticmethod
    def select_result(res_list: list) -> [float, int]:
        # Just unpack the list to int
        sel_res = res_list[0]
        return sel_res, 0

    def calculate_p1(self, ds_pres: xr.Dataset, acc_peak: int) -> np.ndarray:
        indices_window = self.p1_offset_indices + acc_peak
        p1 = ds_pres.isel(time=indices_window).mean("time")
        return p1

    def calculate_p2(self, ds_pres: xr.Dataset, acc_peak: int) -> np.ndarray:
        indices_window = self.p2_offset_indices + acc_peak
        p2 = ds_pres.isel(time=indices_window).max("time")
        return p2

    def calculate_p_metric(self, p1: float, p2: float) -> float:
        return np.sqrt(2 * self.mbar_to_pa / self.rho_h20 * np.abs(p2 - p1))

    def calculate_metric(
        self, sel_data: tuple[xr.DataArray, xr.DataArray]
    ) -> np.ndarray:
        sel_ds, acc_peak = sel_data
        p1 = self.calculate_p1(sel_ds, acc_peak)
        p2 = self.calculate_p2(sel_ds, acc_peak)
        res = self.calculate_p_metric(p1, p2)
        return res

    @staticmethod
    def select_data(ds_sel, _) -> tuple[xr.DataArray, xr.DataArray]:
        acc_peak = ds_sel["peaks"].item()
        if acc_peak != np.nan:
            acc_peak = int(acc_peak)
        ds_sel = ds_sel["pres"]
        return ds_sel, acc_peak


class MetricHuang2025(MetricBase):
    def __init__(self, ds: xr.Dataset) -> None:
        super().__init__(ds)
        self.mv = MvMetricHuang2025(ds)
        self.ds = ds

        self.figname: str = "huang2025_metrics.pdf"
        self.metric_label: str = "Huang2025 Metrics"

    def calculate(self):
        self.mv.calculate()
        self.mp = MpMetricHuang2025(self.ds, self.mv.results.peaks)
        self.mp.calculate()


# %%
if __name__ == "__main__":
    data_dir = Path(__file__).parents[3] / "data" / "combined_data"

    ds = xr.open_dataset(
        data_dir / "24_07_26_ATS_9.5mmBlade_1mpsSteps_1to8mps_30N.h5"
    )
    metrics = MetricHuang2025(ds)
    metrics.calculate()

    # %%
    fig, ax = metrics.mv.plot()
    fig.savefig(metrics.mv.figure_path(), dpi=300)

    # %%
    fig, ax = metrics.mp.plot()
    fig.savefig(metrics.mp.figure_path(), dpi=300)

    # %%
    metrics.mv.results.metric.std("trial").plot()
    print(metrics.mv.results.metric.std("trial").mean())
