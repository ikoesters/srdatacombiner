# %%
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from scipy.signal import find_peaks
from scipy.stats import mstats

plt.style.use("seaborn-v0_8-whitegrid")


class MetricBase:
    def __init__(self, ds: xr.Dataset) -> None:
        self.ds = ds

        self.da_res: xr.DataArray = xr.DataArray(
            np.nan,
            coords=[ds.strvel, ds.trial],
            dims=["strvel", "trial"],
        )
        self.da_peaks: xr.DataArray = self.da_res.copy()

        self.savepath: Path = Path("figs")
        self.savepath.mkdir(parents=True, exist_ok=True)

        self.metric_label: str
        self.offset_indices: np.ndarray

    def calculate(self) -> None:
        for v in self.ds.strvel:
            for t in self.ds.trial:
                ds_sel = self.ds.sel(strvel=v, trial=t)
                index_peaks = self.find_peak(ds_sel)
                try:
                    res_list = []
                    for p in index_peaks:
                        selected_data = self.select_data(ds_sel, p)
                        res = self.calculate_metric(selected_data)
                        res_list.append(res)
                    sel_res, p_index = self.select_result(res_list)
                    index_peak = index_peaks[p_index]
                except (IndexError, ValueError):
                    sel_res = np.nan
                    index_peak = np.nan
                self.da_res.loc[dict(trial=t, strvel=v)] = sel_res
                self.da_peaks.loc[dict(trial=t, strvel=v)] = index_peak
        self.results = xr.Dataset({"metric": self.da_res, "peaks": self.da_peaks})
        self.results = self.add_metadata(self.results)

    def find_peak(self, da: xr.DataArray) -> np.ndarray:
        raise NotImplementedError

    def select_data(self, ds_sel, index_peak: int) -> xr.Dataset:
        # Select the data around the peak
        indices_window = index_peak + self.offset_indices
        ds_sel = ds_sel.isel(time=indices_window)
        return ds_sel

    def calculate_metric(self, da: xr.DataArray) -> np.ndarray:
        raise NotImplementedError

    def select_result(self, res_list: list) -> tuple[float, int]:
        raise NotImplementedError

    def add_metadata(self, ds: xr.Dataset) -> None:
        ds.attrs["metric"] = self.metric_label
        return ds

    def get_percentile(self, ds: xr.Dataset, percentile) -> np.ndarray:
        return np.nanpercentile(ds, percentile, axis=1)

    def get_percentiles(
        self, ds: xr.Dataset, percentiles
    ) -> tuple[np.ndarray, np.ndarray]:
        return [self.get_percentile(ds, p) for p in percentiles]

    def plot(self) -> tuple[plt.Figure, plt.Axes]:
        fig, ax = plt.subplots()
        ax.set_xlabel("Velocity Strike Rig (m/s)")
        ax.set_ylabel("Velocity Model (m/s)")

        # Plot the median of the metric
        ax.plot(
            self.ds.strvel,
            self.da_res.median("trial"),
            label=self.metric_label,
            color="r",
        )

        # Plot the ground truth line
        ax.plot(
            range(1, 9),
            range(1, 9),
            color="k",
            linestyle="--",
            label="Ground Truth",
        )

        # # Fill the envelope
        # ax.fill_between(
        #     self.ds.strvel,
        #     *self.get_percentiles(self.da_res, [10, 90]),
        #     color="r",
        #     alpha=0.15,
        #     label=f"80% Confidence Envelope (n={len(self.da_res.trial)})",
        # )

        # Fill the envelope
        ax.fill_between(
            self.ds.strvel,
            *self.get_percentiles(self.da_res, [2.5, 97.5]),
            color="r",
            alpha=0.15,
            label=f"95% Confidence Envelope (n={len(self.da_res.trial)})",
        )

        ax.legend(frameon=True)
        fig.tight_layout()
        # fig.savefig(self.savepath, dpi=300)
        return fig, ax

    def plot_conf_range(self) -> tuple[plt.Figure, plt.Axes]:
        fig, ax = plt.subplots()
        ax.set_xlabel("Velocity Strike Rig (m/s)")
        ax.set_ylabel("Velocity Model (m/s)")

        # Plot the median of the metric
        ax.plot(
            self.ds.strvel,
            self.ds.strvel,
            label="Ground Truth",
            color="k",
            linestyle="--",
        )

        lower_bound, upper_bound = self.get_percentiles(self.da_res, [10, 90])

        ax.plot(
            self.ds.strvel,
            upper_bound - lower_bound,
            label="80% Confidence Range",
            color="b",
            linestyle="-.",
        )

        lower_bound, upper_bound = self.get_percentiles(self.da_res, [2.5, 97.5])
        # Plot the difference between upper and lower bound
        ax.plot(
            self.ds.strvel,
            upper_bound - lower_bound,
            label="95% Confidence Range",
            color="b",
        )
        # Fill the envelope
        ax.fill_between(
            self.ds.strvel,
            *self.get_percentiles(self.da_res, [10, 90]),
            color="grey",
            alpha=0.2,
            label=f"80% Confidence Envelope (n={len(self.da_res.trial)})",
        )

        # Fill the envelope
        ax.fill_between(
            self.ds.strvel,
            *self.get_percentiles(self.da_res, [2.5, 97.5]),
            color="grey",
            alpha=0.2,
            label=f"95% Confidence Envelope (n={len(self.da_res.trial)})",
        )

        ax.legend(frameon=True)
        fig.tight_layout()
        return fig, ax


# %%
