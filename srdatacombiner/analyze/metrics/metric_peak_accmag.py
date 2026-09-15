"""Peak acceleration magnitude, with the shear/collision classification.

The magnitude is the Euclidean norm of the three accelerometer axes,

    |a| = sqrt(ax^2 + ay^2 + az^2),

and the metric is its maximum over the analysis window of one trial. An event is
classified by the total time the magnitude remains above ``SHEAR_FRACTION`` of
that maximum: longer than ``SHEAR_DURATION`` is a shear event, shorter is a
collision. ``MORTALITY_THRESHOLD`` is the literature value above which mortality
is expected; it is exposed as a constant and is never applied here.

Values are in m/s^2 throughout, the internal unit of this package. Divide by
``G`` to obtain g.
"""

# %%
import numpy as np
import xarray as xr

from srdatacombiner.analyze.metrics.metric_base import MetricBase

G: float = 9.81  # m/s^2

MORTALITY_THRESHOLD_G: float = 95.0
MORTALITY_THRESHOLD: float = MORTALITY_THRESHOLD_G * G  # m/s^2

SHEAR_FRACTION: float = 0.70  # of the peak magnitude
SHEAR_DURATION: float = 7.5e-3  # s; longer is shear, shorter is a collision

ACC_COMPONENTS: tuple[str, ...] = ("accx", "accy", "accz")


def acceleration_magnitude(ds: xr.Dataset) -> xr.DataArray:
    """Euclidean norm of the accelerometer axes.

    Uses the ``accmag`` variable where a reader already supplies it, since some
    probes compute it from more channels than the three Cartesian axes, and
    falls back to the norm of ``accx``, ``accy`` and ``accz``.
    """
    if "accmag" in ds:
        return ds["accmag"]
    missing = [c for c in ACC_COMPONENTS if c not in ds]
    if missing:
        raise KeyError(
            f"cannot form the acceleration magnitude: missing {missing} "
            "and no 'accmag' variable"
        )
    return sum(ds[c] ** 2 for c in ACC_COMPONENTS) ** 0.5


class PeakAccMagMetric(MetricBase):
    """Peak acceleration magnitude per trial, on the ``(strvel, trial)`` grid.

    ``calculate()`` populates ``results`` with three variables:

    ``metric``
        Peak acceleration magnitude, m/s^2.
    ``peaks``
        Time index at which that peak occurs.
    ``duration``
        Total time the magnitude stays at or above ``shear_fraction`` of the
        peak, in seconds.
    ``is_shear``
        True where ``duration`` exceeds ``shear_duration``.

    The peak is located with ``nanargmax``, as in the reference analysis. That
    anchor is unstable above roughly 5 m/s when a trial contains a secondary
    event larger than the strike; see
    :mod:`srdatacombiner.helper_scripts.strike_window` for an alternative to
    test a result against.
    """

    def __init__(
        self,
        ds: xr.Dataset,
        shear_fraction: float = SHEAR_FRACTION,
        shear_duration: float = SHEAR_DURATION,
    ) -> None:
        super().__init__(ds)

        # The metric is the peak sample itself, so the window is a single index.
        self.offset_indices: np.ndarray = np.array([0])

        self.shear_fraction: float = shear_fraction
        self.shear_duration: float = shear_duration
        self.delta_t: float = float(np.mean(np.gradient(ds.time)))

        self.figname: str = "peak_accmag_metric.pdf"
        self.metric_label: str = "Peak acceleration magnitude"

    @property
    def accmag(self) -> xr.DataArray:
        return acceleration_magnitude(self.ds)

    def find_peak(self, ds: xr.Dataset) -> np.ndarray:
        mag = acceleration_magnitude(ds).values
        # A combined dataset is padded with all-NaN trials wherever one probe
        # covers fewer strike velocities than another, so this is the normal
        # case rather than an error. Return no peak and let MetricBase record
        # NaN, as find_peaks does for the other metrics. MetricBase calls
        # find_peak outside its own try block, so raising here would abort the
        # whole sweep.
        if np.all(np.isnan(mag)):
            return np.array([], dtype=int)
        return np.array([int(np.nanargmax(mag))])

    def select_data(self, ds_sel: xr.Dataset, index_peak: int) -> xr.DataArray:
        mag = acceleration_magnitude(ds_sel)
        return mag.isel(time=index_peak + self.offset_indices)

    def calculate_metric(self, da: xr.DataArray) -> float:
        return float(da.max("time").values)

    @staticmethod
    def select_result(res_list: list) -> tuple[float, int]:
        res = np.array(res_list)
        index_max = int(np.argmax(res))
        return res[index_max], index_max

    def calculate(self) -> None:
        super().calculate()

        mag = self.accmag
        peak = self.results["metric"]

        above = mag >= self.shear_fraction * peak
        duration = above.sum("time") * self.delta_t
        # A trial without a peak has no duration either.
        duration = duration.where(peak.notnull())

        self.results["duration"] = duration
        self.results["is_shear"] = duration > self.shear_duration

        self.results["metric"].attrs = {"Unit": "m/s^2"}
        self.results["duration"].attrs = {
            "Unit": "s",
            "Description": (
                f"time at or above {self.shear_fraction:.0%} of the peak magnitude"
            ),
        }
        self.results["is_shear"].attrs = {
            "Description": f"duration exceeds {self.shear_duration * 1e3:.1f} ms"
        }

    def exceeds_mortality_threshold(
        self, threshold: float = MORTALITY_THRESHOLD
    ) -> xr.DataArray:
        """Trials whose peak magnitude exceeds ``threshold`` (m/s^2)."""
        return self.results["metric"] > threshold
