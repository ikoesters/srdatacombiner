# %%
from dataclasses import dataclass
import plotly.express as px
from srdatacombiner.helper_scripts.Strike_Trajectory_Estimation.ode import StrikeODE


# %%
@dataclass
class ODEParams:
    strike_vel: float = 10  # m/s

    # Drivetrain
    accelerated_mass_wo_blade: float = 13.669 + 4 - 3  # -12# kg, correction
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


# %%
s = StrikeODE(ODEParams())
df = s.main()
px.line(df, x="pos", y="vel")
