"""Locating the strike inside a probe record, as a sensitivity check.

This module is not the default anchor. The reference analysis anchors its window
on ``int(np.nanargmax(mag))`` and should continue to do so, because identifying
the strike among several acceleration events requires knowing in advance which
one it is, and a field deployment does not have that knowledge. A result resting
on this module would therefore depend on a step unavailable in the field. The
module is intended to show that a conclusion does not depend on the peak-finding
rule. Headline numbers should still come from ``nanargmax``.

Above roughly 6 m/s a trial contains two large acceleration events, and the later
one grows with strike velocity until it exceeds the strike itself. ``nanargmax``
then anchors the window to the wrong event. On the Sensor Fish the standard
deviation of the anchor rises from 0.4 samples at 1-5 m/s to 5.7 samples at
8 m/s; on the RAPID the anchor is unstable over the whole velocity range.

The error this introduces is systematic. Because the rate of misalignment
increases with velocity, a window anchored this way carries a spurious
velocity-dependent signal in the samples preceding the strike, contributed
entirely by the trials that anchored late. A quantity read from that region
measures how often the anchor moved to the later event and carries no
information about the collision.

``strike_peak_index`` anchors to the peak of the first event instead. It
preserves peak-anchored semantics, so existing offsets such as ``peak-3 ..
peak+3`` retain the meaning they had, and it is a drop-in replacement for the
``nanargmax`` call.

Two limitations remain. Events that never separate, meaning that the magnitude
stays above the onset threshold from one event into the next, are treated as a
single event, and the larger of the two determines the anchor. That case is
ambiguous from the magnitude trace alone and is not resolved here. Some
misalignment also persists at the upper end of the velocity range, so pre-anchor
features above 6 m/s remain unresolved.
"""

from __future__ import annotations

import numpy as np

__all__ = ["strike_peak_index", "strike_window"]


def strike_peak_index(mag, frac: float = 0.10, search: int = 4) -> int:
    """Index of the peak of the first acceleration event in ``mag``.

    The onset is the first sample reaching ``frac`` of the record maximum, and
    the anchor is the largest sample within the fixed window of ``search``
    samples that follows it. Relative to ``np.nanargmax`` only the location of
    the peak changes. The analysis windows cut by the callers keep their fixed
    length.

    Expressing the onset as a fraction of the record maximum rather than as an
    absolute threshold keeps the function scale-free across probes of differing
    dynamic range. The record maximum is a stable reference for this purpose,
    since it does not depend on where the peak occurs.

    Parameters
    ----------
    mag : array_like
        Acceleration magnitude for one trial. May contain NaN.
    frac : float
        Onset threshold as a fraction of the record maximum. On blade-strike
        data the result is insensitive to this parameter: 0.10, 0.25 and 0.50
        yield identical anchors, which shows that the onset falls on the rise of
        the strike and not on a precursor.
    search : int
        Upper bound on how far past the onset the peak may lie. The rise occupies
        two to three samples, which makes 4 both the physically motivated value
        and the empirically best one. Substantially larger values approach the
        behaviour of ``nanargmax``.

    Returns
    -------
    int
        Index of the strike peak, or of the global maximum where no sample
        reaches the threshold (an all-NaN or flat record).
    """
    mag = np.asarray(mag, dtype=float)
    peak = np.nanmax(mag)
    if not np.isfinite(peak):
        return int(np.nanargmax(mag))
    above = np.nan_to_num(mag, nan=-np.inf) >= frac * peak
    start = np.flatnonzero(above)
    if start.size == 0:
        return int(np.nanargmax(mag))
    onset = int(start[0])
    stop = min(onset + search, mag.size)
    return onset + int(np.nanargmax(mag[onset:stop]))


def strike_window(mag, offsets, frac: float = 0.10):
    """Sample indices for ``offsets`` around the strike peak, or None.

    Returns None where the window would run past either end of the record or
    would cover a NaN, so that a caller can skip an unusable trial without
    writing the guard itself.

    Examples
    --------
    >>> idx = strike_window(mag, np.arange(-3, 4))
    >>> if idx is not None:
    ...     features = mag[idx]
    """
    mag = np.asarray(mag, dtype=float)
    if np.all(np.isnan(mag)):
        return None
    idx = strike_peak_index(mag, frac=frac) + np.asarray(offsets)
    if idx.min() < 0 or idx.max() >= mag.size or np.isnan(mag[idx]).any():
        return None
    return idx
