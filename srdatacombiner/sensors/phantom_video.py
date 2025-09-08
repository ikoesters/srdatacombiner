# %%
import dask.array as np
import xarray as xr
import pims
from pathlib import Path


class PhantomVideo:
    filename_extension: str = ".cine"

    def __init__(
        self, filename: str, varname: str, return_dask_ds: bool = True
    ) -> None:
        self.filename = filename
        self.varname = varname
        self.return_dask_ds = return_dask_ds

        self.film: pims.Cine = pims.open(str(filename))
        self.xname = "x"
        self.yname = "y"
        self.timename = "time"

    def get_stacked_arrays(self) -> list:
        return np.stack(
            [self.film.get_frame(i) for i in range(self.film.image_count)],
            axis=0,
        )

    def stacked_arrays_to_xarray(self, stacked_arrays: list) -> xr.DataArray:
        da = xr.DataArray(
            data=stacked_arrays,
            dims=[self.timename, self.yname, self.xname],
            coords={
                self.timename: np.arange(
                    0,
                    self.film.image_count / self.film.frame_rate,
                    1 / self.film.frame_rate,
                ),
                self.xname: np.arange(self.film.frame_shape[0]),
                self.yname: np.arange(self.film.frame_shape[1]),
            },
        )
        da = da.rename(self.varname)
        return da

    def rechunk(self, da: xr.DataArray, chunks_arg="auto") -> xr.DataArray:
        return da.chunk(chunks=chunks_arg)

    def normalize(self, da: xr.DataArray) -> xr.DataArray:
        da = da.astype("float32")
        da = da / 1012  # da.max()
        return da

    def get_xarray(self) -> xr.DataArray:
        stacked_arrays = self.get_stacked_arrays()
        da = self.stacked_arrays_to_xarray(stacked_arrays)
        da = self.rechunk(da)
        da = self.normalize(da)
        return da


class DualVideo(PhantomVideo):
    def __init__(self, filename: str | Path) -> None:
        if isinstance(filename, str):
            filename = Path(filename)
        filename_below = filename.name.replace("CamSide", "CamBelow")
        filename_side = filename.name.replace("CamBelow", "CamSide")
        self.camb = super(filename_below, varname="cam_below")
        self.cams = super(filename_side, varname="cam_side")

        self.camb.xname = "xb"
        self.camb.yname = "yb"
        self.cams.xname = "xs"
        self.cams.yname = "ys"

    def get_xarray(self) -> xr.Dataset:
        dab = self.camb.get_xarray()
        das = self.cams.get_xarray()
        ds = xr.merge([dab, das])
        ds = ds.chunk("auto")
        return ds


# %%
if __name__ == "__main__":
    pass
