# %%
import numpy as np
import srdatacombiner.helper_scripts.servocontroller_tools as st
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import xarray as xr

import scipy.stats as stats


pd.options.plotting.backend = "plotly"
# %%
savefile = Path("../../../data/ode/all_data.netcdf4")

ds = xr.open_dataset(savefile)
# %%
ds = ds.where(ds.index < (ds.pos.argmax("index")))

# %% Make Dataset from constant velocity part
idx_obl_losses = [
    [530, 7400],
    [700, 3600],
    [700, 2400],
    [700, 1800],
    [700, 1400],
    [700, 1200],
    [700, 1000],
]
cvel_ds = []
for v in range(7):
    val = ds.sel(index=slice(*idx_obl_losses[v]), strvel=v).mean("index")
    cvel_ds.append(val)
cvel_ds = xr.concat(cvel_ds, dim="strvel")

# %% Lin Reg of consumed current during constant velocity over strike velocities
slope, intercept, r_value, _, _ = stats.linregress(
    range(1, 8), cvel_ds.curr.sel(blade=0)
)
print(f"{slope=:.4f} {intercept=:.4f} {r_value=:.4f}")


# %%
def mech_losses(vel, slope=0.12279, intercept=1.15088):
    return vel * slope + intercept


# %% Make Dataset from Acceleration
idx_obl_acc = [
    [0, 180],
    [0, 250],
    [0, 320],
    [0, 390],
    [0, 460],
    [0, 530],
    [0, 600],
]  # starts at 3ms

acc_ds = []
for i, v in enumerate(range(2, 9)):
    val = ds[["curr", "vel"]].sel(index=slice(*idx_obl_acc[i]), strvel=v)
    acc_ds.append(val)
acc_ds = xr.concat(acc_ds, dim="strvel")

# %% Compute Mass
EFFECTIVE_DIAM = 122.23e-3  # m
TORQUE_CONSTANT = 2.23  # Nm/A
SAMPLE_RATE = 4000  # Hz
losses_ds = acc_ds.sel(blade=0)

losses_ds["curr"] -= mech_losses(losses_ds.vel)
losses_ds["force"] = TORQUE_CONSTANT * losses_ds.curr / (EFFECTIVE_DIAM / 2)
mass = (
    (losses_ds.force / (losses_ds.vel.diff("index") * SAMPLE_RATE).median("index"))
    .median("index")
    .mean("strvel")
)

# %% Check if acceleration is indeed repeatable and linear
acc_linreg = []
for _, v in enumerate(range(0, 6)):
    slope, intercept, r_value, _, _ = stats.linregress(
        range(len(losses_ds.vel.sel(strvel=v).dropna("index"))),
        losses_ds.vel.sel(strvel=v).dropna("index"),
    )
    acc_linreg.append([slope, intercept, r_value])
acc_linreg = pd.DataFrame(acc_linreg, columns=["slope", "intercept", "r_value"])
acc_linreg.std()

# %% Compare computed masses against design data
trans_parts = "timing_belt 2xclampling_plate cart_plate 4xlinear_bearings 2x45brackets blade_arm 10mmblade 30mmblade".split()
mass_trans_parts = [1.45, 0.24, 1.86, 1.6, 0.210, 1.989, 0.275, 0.470]
rot_parts = "motor motor_coupling motor_pulley bushing_motor_pulley diverter_pulley bushing_div_pulley".split()
mass_rot_parts = [0.68, 0.89, 1.15, 0.36, 0.23, 0.26]  # equivalent translatory mass

df_trans = pd.DataFrame(mass_trans_parts, index=trans_parts, columns=["mass"])
df_rot = pd.DataFrame(mass_rot_parts, index=rot_parts, columns=["mass"])

m_wo = (
    df_rot.sum()
    + df_trans.sum()
    - df_trans.loc[["10mmblade", "30mmblade", "blade_arm"]].sum()
)
m_thin = df_rot.sum() + df_trans.sum() - df_trans.loc[["30mmblade"]].sum()
m_thick = df_rot.sum() + df_trans.sum() - df_trans.loc[["30mmblade"]].sum()
# %%
m_thin_from_data = mass.values + df_trans.loc[["blade_arm", "10mmblade"]].sum().values
m_thick_from_data = mass.values + df_trans.loc[["blade_arm", "30mmblade"]].sum().values

f_thin = m_thin_from_data * acc_ds.vel.sel(blade=1).diff("index") * SAMPLE_RATE
curr_accel = f_thin / TORQUE_CONSTANT * (EFFECTIVE_DIAM / 2)
(acc_ds.curr.sel(blade=1) - curr_accel - mech_losses(acc_ds.vel.sel(blade=1))).median(
    "index"
).plot()


def acc_force(vel: xr.Dataset, mass, sample_rate: int = 4000) -> xr.Dataset:
    return mass * vel.differentiate("index") * sample_rate


def acc_curr(force, torque_const=2.25, pulley_diam=122.23e-3):
    return force / torque_const * (pulley_diam / 2)


# %%
acc_thin = acc_curr(acc_force(acc_ds.vel.sel(blade=1), m_thin_from_data))
acc_thick = acc_curr(acc_force(acc_ds.vel.sel(blade=2), m_thick_from_data))

# %%

coefficients = np.polyfit(
    range(cvel_ds.sizes["strvel"]),
    (cvel_ds.curr.sel(blade=2) - cvel_ds.curr.sel(blade=0)),
    3,
)  # 2 indicates a second-order polynomial
poly_function = np.poly1d(coefficients)
pure_v2_fct = np.poly1d([coefficients[0], 0, 0])
plt.plot(range(7), (cvel_ds.curr.sel(blade=2) - cvel_ds.curr.sel(blade=0)))
plt.plot(range(7), poly_function(range(7)))
# plt.plot(range(7), pure_v2_fct(range(7)))


def drag(vel, coefficients):
    poly_function = np.poly1d(coefficients)
    return poly_function(vel)


def drag_10mmblade(vel):
    coefficients = [0.0, 0.0, 0.01357991]
    return drag(vel, coefficients)


def drag_30mmblade(vel):
    coefficients = [0.0, 0.0, 0.02494718]
    return drag(vel, coefficients)


# %%
curr_remainder = (
    ds.curr.sel(blade=1)
    - acc_curr(acc_force(ds.vel.sel(blade=1), m_thick_from_data))
    - mech_losses(ds.vel.sel(blade=1))
    - drag_10mmblade(ds.vel.sel(blade=1))
)
for v in range(9):
    plt.plot(ds.vel.sel(blade=1, strvel=v), curr_remainder.sel(strvel=v))
# %%
losses = [
    acc_curr(acc_force(ds.vel.sel(blade=1), m_thick_from_data)),
    mech_losses(ds.vel.sel(blade=1)),
    xr.DataArray(drag_10mmblade(ds.vel.sel(blade=1)), dims=["strvel", "index"]),
]
losses = xr.concat(losses, dim="loss")
# %%
for v in range(9):
    # plt.plot(ds.curr.sel(blade=1, strvel=v))
    l = losses.sel(strvel=5)
    plt.plot(l.sel(loss=0))
    plt.plot(l.sel(loss=1))
    plt.plot(l.sel(loss=2))
# %%
for v in range(9):
    # plt.plot(ds.curr.sel(blade=1, strvel=v))
    loss = losses.sel(strvel=5)
    for l in range(2):
        loss.sel(loss=l).plot()
    plt.show()
