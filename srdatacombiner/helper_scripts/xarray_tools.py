# %%
import xarray as xr
import pandas as pd
from pathlib import Path
from datetime import datetime
import re


def df2ds(df: pd.DataFrame) -> xr.Dataset:
    return xr.Dataset.from_dataframe(df)


def ds2df(ds: xr.Dataset, drop_index=True) -> pd.DataFrame:
    return ds.to_dataframe().reset_index(drop=drop_index)


def to_csv(ds, index, drop_cols=[], **kwargs) -> None | str:
    df = ds2df(ds, drop_index=False)
    df.drop(columns=drop_cols, inplace=True)
    df.set_index(index, inplace=True)
    df.to_csv(**kwargs)


def assign_datavar_info(
    ds: xr.Dataset, units_dict: dict[str, list | tuple | str], infonames: list[str]
) -> None:
    units_dict = expand_units_dict(varnames=list(ds.variables), units_dict=units_dict)
    for key, vals in units_dict.items():
        if isinstance(vals, str):
            vals = [vals]
        for attr_name, val in zip(infonames, vals):
            if val is not None:
                assign_datavar_attr(ds, key, attr_name, val)
    return ds


def expand_units_dict(
    varnames: list[str], units_dict: dict[str, str]
) -> dict[str, str]:
    exp_dict = {}
    for re_pattern, unit in units_dict.items():
        exp_dict |= {var: unit for var in varnames if re.search(re_pattern, var)}
    return exp_dict


def assign_datavar_attr(ds: xr.Dataset, datavar: str, attr_name: str, value) -> None:
    ds[datavar].attrs[attr_name] = value


def assign_global_attrs_from_dict(ds: xr.Dataset, attr_dict: dict) -> xr.Dataset:
    return ds.assign_attrs(attr_dict)


def set_attr_timestamp(
    ds: xr.Dataset, descr_str: str = "Xarray creation time"
) -> xr.Dataset:
    attr_dict = {}
    attr_dict[descr_str] = datetime.now().isoformat()
    return assign_global_attrs_from_dict(ds, attr_dict)


def save_as_h5(
    ds: xr.Dataset | xr.DataArray,
    folder: str,
    filename: str | Path,
    compress: bool = True,
    compress_level=1,
) -> None:
    if type(ds) == xr.DataArray:
        ds = ds.to_dataset()
    if compress == True:
        comp = dict(zlib=True, complevel=compress_level)
        encoding = {var: comp for var in ds.data_vars}
    else:
        encoding = {}
    ds.to_netcdf(
        Path(folder) / f"{filename}.h5",
        engine="h5netcdf",
        format="NETCDF4",
        encoding=encoding,
    )


# %%
