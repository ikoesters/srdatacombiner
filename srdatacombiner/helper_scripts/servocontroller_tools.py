# %%
# This file contains functions to convert the data from the servocontroller.
# They are also implemented in the ServoScopePreprocessor class, but can be accessed here as well.
import numpy as np
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots

EFFECTIVE_DIAM = 122.23e-3


def rpm2ms(rpm: float | np.ndarray) -> float | np.ndarray:
    """Calculate the linear velocity in m/s
    given the rpm of the motor using the effective diameter
    of the pulley (defined in outer scope)

    Args:
        rpm (float | np.ndarray): rounds per minute of the motor

    Returns:
        float | np.ndarray: velocity in metres/second
    """
    vel = rpm * (np.pi * EFFECTIVE_DIAM) / 60
    return vel


def ms2rpm(vel_ms: float | np.ndarray) -> float | np.ndarray:
    """Calculate rpm velocity in m/s of the motor
    using the effective diameter
    of the pulley (defined in outer scope)

    Args:
        ms (float | np.ndarray): linear velocity in metres/second

    Returns:
        float | np.ndarray: round per minute of the motor
    """
    rpm = vel_ms * 60 / (np.pi * EFFECTIVE_DIAM)
    return rpm


def pos2m(pos: float | np.ndarray) -> float | np.ndarray:
    """Calculate the position in metres from the home position
    given the position feedback from the servocontroller.

    Args:
        pos (float | np.ndarray): position feedback

    Returns:
        float | np.ndarray: position in metres
    """
    pos /= 2**16
    m = pos * np.pi * EFFECTIVE_DIAM
    return m


def m2pos(m: float | np.ndarray) -> float | np.ndarray:
    """Calculate the position feedback of the servocontroller
    given the distance from the homing position in metres.

    Args:
        m (float | np.ndarray): distance from the homing position in metres

    Returns:
        float | np.ndarray: position feedback
    """
    pos = m / (np.pi * EFFECTIVE_DIAM)
    pos *= 2**16
    return pos


def load_scope_data(
    filename: str, columns, column_names, sep=";", decimal=",", skiprows=[0]
) -> None:
    df = pd.read_csv(
        filename,
        sep=sep,
        decimal=decimal,
        usecols=columns,
        names=column_names,
        skiprows=skiprows,
        # index_col=0,
    )
    df["time"] /= 1000
    df[["velcom", "vel"]] = rpm2ms(df[["velcom", "vel"]])
    df["pos"] = pos2m(df["pos"])
    return df


def plotly_twinx(
    df1,
    df2,
    xaxisname=None,
    y1axisname=None,
    y2axisname=None,
    axistypes=["linear", "linear"],
):
    subfig = make_subplots(specs=[[{"secondary_y": True}]])

    # create two independent figures with px.line each containing data from multiple columns
    fig = px.line(df1)
    fig2 = px.line(df2)

    fig2.update_traces(yaxis="y2")

    subfig.add_traces(fig.data + fig2.data)
    subfig.layout.xaxis.title = xaxisname
    subfig.layout.yaxis.title = y1axisname
    subfig.layout.yaxis.type = axistypes[0]

    subfig.layout.yaxis2.type = axistypes[1]
    subfig.layout.yaxis2.title = y2axisname
    # recoloring is necessary otherwise lines from fig und fig2 would share each color
    # e.g. Linear-, Log- = blue; Linear+, Log+ = red... we don't want this
    subfig.for_each_trace(lambda t: t.update(line=dict(color=t.marker.color)))
    subfig.show()
