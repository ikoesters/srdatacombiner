# %%
from typing import Literal

import matplotlib as mpl
import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt
import numpy as np
from typing import Literal


def set_color_cycler(colorlist: list[str]) -> None:
    mpl.rcParams["axes.prop_cycle"] = mpl.cycler(color=colorlist)


def set_sns_style(style: Literal["whitegrid", "darkgrid"] = "darkgrid") -> None:
    plt.style.use(f"seaborn-v0_8-{style}")


def set_dpi(dpi=200) -> None:
    plt.rcParams["figure.dpi"] = dpi


def reset_style() -> None:
    mpl.rcParams.update(mpl.rcParamsDefault)
    plt.ion()


def set_plot_full_textwidth(height=3, frac_textwidth=1) -> None:

    plt.rcParams["figure.figsize"] = (
        6.5 * frac_textwidth,
        height,
    )  # wider than \textwidth, but yields better results
    plt.rcParams["figure.dpi"] = 200
    plt.rcParams["font.size"] = 11  # +1p as width of figure is increased


def set_latex_cm() -> None:
    # Use Computer Modern
    cmfont = font_manager.FontProperties(
        fname=mpl.get_data_path() + "/fonts/ttf/cmr10.ttf"
    )
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["font.serif"] = cmfont.get_name()
    plt.rcParams["mathtext.fontset"] = "cm"
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["axes.formatter.use_mathtext"] = True


def set_latex_stix() -> None:
    font = font_manager.FontProperties(
        fname=mpl.get_data_path() + "/fonts/ttf/STIXGeneral.ttf"
    )
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["font.serif"] = font.get_name()
    plt.rcParams["mathtext.fontset"] = "stix"
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["axes.formatter.use_mathtext"] = True


def period_xticks(
    data_len,
    xtick_labels=None,
) -> None:
    if xtick_labels is None:
        xtick_labels = [
            r"$0$",
            r"$\frac{1}{2}\pi$",
            r"$\pi$",
            r"$\frac{3}{2}\pi$",
            r"$2\pi$",
        ]
    plt.xticks(
        np.round(np.linspace(0, data_len, len(xtick_labels), endpoint=True)),
        xtick_labels,
    )
    plt.xlim(0, data_len)
    plt.xlabel("Normalized Period [-]")
    # plt.tight_layout()


def plotly_set_output(output: Literal["browser", "notebook"] = "browser") -> None:
    import plotly.io as pio

    pio.renderers.default = output


class Colormaps:
    """Taken from :
    https://www.heavy.ai/blog/12-color-palettes-for-telling-better-stories-with-your-data

    cat: Categorical
    seq: Sequential
    div: Diverging (clear middle point)
    """

    cat_dutch_field = [
        "#e60049",
        "#0bb4ff",
        "#50e991",
        "#e6d800",
        "#9b19f5",
        "#ffa300",
        "#dc0ab4",
        "#b3d4ff",
        "#00bfa0",
    ]
    seq_grey_to_red = [
        "#d7e1ee",
        "#cbd6e4",
        "#bfcbdb",
        "#b3bfd1",
        "#a4a2a8",
        "#df8879",
        "#c86558",
        "#b04238",
        "#991f17",
    ]
    seq_black_to_pink = [
        "#2e2b28",
        "#3b3734",
        "#474440",
        "#54504c",
        "#6b506b",
        "#ab3da9",
        "#de25da",
        "#eb44e8",
        "#ff80ff",
    ]
    div_pink_foam = [
        "#54bebe",
        "#76c8c8",
        "#98d1d1",
        "#badbdb",
        "#dedad2",
        "#e4bcad",
        "#df979e",
        "#d7658b",
        "#c80064",
    ]
    div_salmon_to_aqua = [
        "#e27c7c",
        "#a86464",
        "#6d4b4b",
        "#503f3f",
        "#333333",
        "#3c4e4b",
        "#466964",
        "#599e94",
        "#6cd4c5",
    ]
    div_orange_to_purple = [
        "#ffb400",
        "#d2980d",
        "#a57c1b",
        "#786028",
        "#363445",
        "#48446e",
        "#5e569b",
        "#776bcd",
        "#9080ff",
    ]


# %%
