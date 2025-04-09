# %%
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

import scipy.integrate as scint
from dataclasses import dataclass
import numpy.typing as npt
from collections.abc import Iterable
import plotly.express as px

pd.options.plotting.backend = "plotly"


# %%
@dataclass
class ODEParams:
    strike_vel: float = 10  # m/s

    # Drivetrain
    accelerated_mass_wo_blade: float = 13.669 + 4  # kg, correction
    motor_torque_constant: float = 2.23  # Nm/A
    motor_max_acc_curr: float = 30  # A
    motor_max_breaking_curr: float = motor_max_acc_curr  # A
    f_mechloss_fitparams: tuple[float] = (0.12279, 1.15088)
    motor_pulley_diameter: float = 122.23e-3  # m

    # Blade & drag
    blade_mass: float = 0.275  # kg
    blade_mass_mounting_arm: float = 1.989  # kg
    blade_height: float = None
    blade_length: float = None
    blade_width: float = None
    blade_cw: float = None
    water_rho: float = 1000
    water_nu: float = 0.89e-6
    f_dragloss_fitparams: tuple[float] = (0.0, 0.0, 0.01357991)

    # Physical positions along movement path
    basin_movement_length: float = 1.9  # m
    basin_pos_impactsite: float = None
    min_measurement_length: float = 0.2

    # Fish
    fish_length: float = 0.25  # Test
    fish_height: float = 0.10  # Test
    fish_mass: float = 0.3  # Test
    fish_cw: float = 0  # 0.8  # Test

    accelerated_mass: float = (
        accelerated_mass_wo_blade + blade_mass_mounting_arm + blade_mass
    )


class StrikeODE:
    def __init__(self, odeparams: ODEParams) -> None:
        self.p = odeparams
        self.f_mechloss_fct = np.poly1d(self.p.f_mechloss_fitparams)
        self.f_blade_dragloss_fct = np.poly1d(self.p.f_dragloss_fitparams)
        self.odeint_start: list = [0.01]  # m
        self.odeint_time: float = 1  # s
        self.odeint_ntimesteps: int = 1000
        self.motor_pgain: float = 0.1

    def force_drag_blade(self, vel: Iterable[int] | int) -> Iterable[int] | int:
        if any(
            arg is None
            for arg in (self.p.blade_cw, self.p.blade_height, self.p.blade_length)
        ):
            return self.f_blade_dragloss_fct(vel)

        A_blade = self.p.blade_height * self.p.blade_length
        return self.p.blade_cw * A_blade * self.p.water_rho / 2 * vel**2

    def force_drag_fish(self, vel: Iterable[int] | int) -> Iterable[int] | int:
        A_fish = self.p.fish_height * self.p.fish_length
        return self.p.fish_cw * A_fish * self.p.water_rho / 2 * vel**2

    def force_motor(self, curr: Iterable[int] | int) -> Iterable[int] | int:
        return curr * self.p.motor_torque_constant / (self.p.motor_pulley_diameter / 2)

    def force_mechloss(self, vel: Iterable[int] | int) -> Iterable[int] | int:
        return self.f_mechloss_fct(vel)

    def motor_vel_control(self, vel: Iterable[int] | int) -> Iterable[int] | int:
        vel_res = vel - self.p.strike_vel
        return vel_res * self.p.accelerated_mass * self.motor_pgain

    def dist_left_for_const_vel(self, dfa: pd.DataFrame, dfc: pd.DataFrame) -> float:
        acc_decc_dist = dfa["pos"].max() + dfc["pos"].max()
        cval_dist = self.p.basin_movement_length - acc_decc_dist
        if cval_dist < self.p.min_measurement_length:
            cval_dist = self.p.min_measurement_length
        return cval_dist

    def cut_df_below_val(
        self, df: pd.DataFrame, variable: str, value: float
    ) -> pd.DataFrame:
        return df[df[variable] <= value].reset_index(drop=True)

    def solve_all(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        dfa = self.solveA()
        dfb = self.solveB()
        dfc = self.solveC()
        return dfa, dfb, dfc

    def main(self) -> pd.DataFrame:
        dfa, dfb, dfc = self.solve_all()

        dfa = self.cut_df_below_val(dfa, "vel", self.p.strike_vel)
        dfc = self.cut_df_below_val(dfc, "vel", self.p.strike_vel)
        dfc[["pos"]] -= dfc[["pos"]].values[0]

        cval_dist = self.dist_left_for_const_vel(dfa=dfa, dfc=dfc)
        dfb = self.cut_df_below_val(dfb, "pos", cval_dist)

        dfges = self.combine_traj(dfa=dfa, dfb=dfb, dfc=dfc)

        return dfges

    def combine_traj(
        self, dfa: pd.DataFrame, dfb: pd.DataFrame, dfc: pd.DataFrame
    ) -> pd.DataFrame:
        dfb[["time", "pos"]] += dfa[["time", "pos"]].values[-1]
        dfc[["time", "pos"]] += dfb[["time", "pos"]].values[-1]
        dfges = pd.concat([dfa, dfb, dfc], ignore_index=True).reset_index(drop=True)
        return dfges

    @staticmethod
    def vel2dist_travelled(time, vel):
        return np.cumsum(vel * np.gradient(time))

    def sol2dataframe(
        self,
        array: npt.NDArray,
        columns=("time", "pos", "vel", "curr"),
    ) -> pd.DataFrame:
        return pd.DataFrame(array, columns=columns)

    def comp_additional_values(self, time: npt.NDArray, vel: npt.NDArray, current):
        dist = self.vel2dist_travelled(time, vel.flatten())
        if type(current) == int:
            current = np.repeat([current], self.odeint_ntimesteps)
        comb_array = np.hstack(
            [
                time[:, np.newaxis],
                dist[:, np.newaxis],
                vel.T,
                current[:, np.newaxis],
            ]
        )
        return comb_array

    def dvdtA(self, t, v: float):
        return (
            self.force_motor(curr=self.p.motor_max_acc_curr)
            - self.force_mechloss(vel=v)
            - self.force_drag_blade(vel=v)
        ) / self.p.accelerated_mass

    def solveA(self) -> npt.NDArray:
        sol = scint.solve_ivp(
            self.dvdtA,
            y0=self.odeint_start,
            t_span=(0, self.odeint_time),
            t_eval=np.linspace(0, self.odeint_time, self.odeint_ntimesteps),
        )
        comb_array = self.comp_additional_values(
            sol.t, sol.y, self.p.motor_max_acc_curr
        )
        df = self.sol2dataframe(comb_array)
        return df

    def dvdtB(self, t, v: float):
        motor_curr = self.motor_vel_control(vel=v)
        return (
            self.force_motor(curr=motor_curr)
            - self.force_mechloss(vel=v)
            - self.force_drag_blade(vel=v)
            # - self.force_drag_fish(vel=v)
        ) / self.p.accelerated_mass

    def solveB(self) -> npt.NDArray:
        sol = scint.solve_ivp(
            self.dvdtB,
            y0=[self.p.strike_vel],
            t_span=(0, self.odeint_time),
            t_eval=np.linspace(0, self.odeint_time, self.odeint_ntimesteps),
        )
        comb_array = self.comp_additional_values(
            sol.t, sol.y, self.p.motor_max_acc_curr
        )
        df = self.sol2dataframe(comb_array)
        return df

    def dvdtC(self, t, v: float):
        return (
            self.force_motor(curr=self.p.motor_max_breaking_curr)
            + self.force_mechloss(vel=v)
            + self.force_drag_blade(vel=v)
        ) / self.p.accelerated_mass

    def solveC(self) -> npt.NDArray:
        sol = scint.solve_ivp(
            self.dvdtC,
            y0=self.odeint_start,
            t_span=(0, self.odeint_time),
            t_eval=np.linspace(0, self.odeint_time, self.odeint_ntimesteps),
        )
        comb_array = self.comp_additional_values(
            sol.t, np.flip(sol.y), self.p.motor_max_breaking_curr
        )
        df = self.sol2dataframe(comb_array)
        return df


# %%
s = StrikeODE(ODEParams())
df = s.main()
px.line(df, x="pos", y="vel")
# %%
a = s.solveA()
b = s.solveB()
c = s.solveC()
# %%
