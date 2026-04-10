"""
kinematics_analysis.py
======================
Generates a 2-panel academic-poster-quality dashboard visualising the
mathematical models for the 3-cylinder MRI-compatible pneumatic motor.

Panel 1 – Torque Ripple & 3-Phase Sequencing
    Shows individual piston torque contributions and the smooth total
    output torque as a function of main-shaft angle (0–360°).

Panel 2 – Flow Rate vs. Catheter Advancement Speed
    Maps supply flow rate to catheter linear speed via the motor and
    2.5 : 1 gearbox, with a clinical target zone highlighted.

Usage
-----
    python simulation/kinematics_analysis.py

Output
------
    simulation/poster_dashboard.png   (also displayed interactively)

Author: Sam Tsang (MRI Actuator Project)
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ---------------------------------------------------------------------------
# Output path (always relative to this script's directory)
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PNG = os.path.join(SCRIPT_DIR, "poster_dashboard.png")

# ---------------------------------------------------------------------------
# Figure layout – wide 2-panel figure suitable for an academic poster
# ---------------------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle(
    "MRI-Compatible Pneumatic Motor — Kinematics Analysis",
    fontsize=18,
    fontweight="bold",
    y=1.01,
)

# ---------------------------------------------------------------------------
# Subplot 1: Torque Ripple & 3-Phase Sequencing (FIXED SWASHPLATE KINEMATICS)
# ---------------------------------------------------------------------------
# Angular domain
theta_deg = np.linspace(0, 360, 1800)
theta_rad = np.deg2rad(theta_deg)

# Physical constants
F_ACTIVE = 52.0  # N  – pneumatic thrust force per piston

# Three pistons offset by 120° each
PISTON_OFFSETS_DEG = [0, 120, 240]
PISTON_LABELS = ["A", "B", "C"]
PISTON_COLORS = ["#2196F3", "#4CAF50", "#F44336"]  # Blue, Green, Red

# Swashplate kinematics: z = A * [1 - cos(theta - phi)]
# Derivative (slope) dh/dtheta = A * sin(theta - phi)
A_kinematic = 0.020  # Kinematic multiplier to achieve ~1.04 N.m peak

torque_per_piston = []
for phi_deg in PISTON_OFFSETS_DEG:
    phi_rad = np.deg2rad(phi_deg)
    
    # Torque = Force * dh/dtheta
    dh_dtheta = A_kinematic * np.sin(theta_rad - phi_rad)
    torque_i = F_ACTIVE * dh_dtheta

    # Active window: 180° power stroke (valves open for the full upward slope)
    angular_offset = (theta_deg - phi_deg) % 360.0
    active_mask = angular_offset <= 180.0
    torque_per_piston.append(np.where(active_mask, torque_i, 0.0))

total_torque = np.sum(torque_per_piston, axis=0)
avg_torque = float(np.mean(total_torque))
PEAK_TORQUE = float(np.max(total_torque))

# Individual piston contributions (dashed)
for torque_i, label, color in zip(torque_per_piston, PISTON_LABELS, PISTON_COLORS):
    ax1.plot(
        theta_deg,
        torque_i,
        color=color,
        linestyle="--",
        linewidth=1.5,
        label=f"Piston {label}",
        alpha=0.85,
    )

# Total output torque (thick solid)
ax1.plot(
    theta_deg,
    total_torque,
    color="black",
    linewidth=2.8,
    label="Total Output Torque",
    zorder=5,
)

# Reference horizontal lines
ax1.axhline(
    avg_torque,
    color="dimgray",
    linestyle="--",
    linewidth=1.3,
    label=f"Average Torque ({avg_torque:.2f} N·m)",
)
ax1.axhline(
    PEAK_TORQUE,
    color="darkorange",
    linestyle="--",
    linewidth=1.3,
    label=f"Theoretical Peak ({PEAK_TORQUE:.2f} N·m)",
)

ax1.set_xlim(0, 360)
ax1.set_xticks(range(0, 361, 60))
ax1.set_xlabel("Main Shaft Angle (degrees)", fontsize=14)
ax1.set_ylabel("Torque (N·m)", fontsize=14)
ax1.set_title("Torque Ripple & 3-Phase Sequencing", fontsize=15, fontweight="bold")
ax1.legend(fontsize=12, loc="lower right")
ax1.grid(True, linestyle="--", alpha=0.45)

# ---------------------------------------------------------------------------
# Subplot 2: Flow Rate vs. Catheter Advancement Speed
# ---------------------------------------------------------------------------
# Supply flow rate sweep
Q = np.linspace(0.5, 3.5, 400)  # L/min

# Motor parameters
# V_REV = π/4 × bore² × stroke × cylinders ≈ π/4 × (12mm)² × 10mm × 3 ≈ 31.2 mL/rev
V_REV = 31.2        # mL/rev  – total swept volume per revolution (from piston geometry)
GEAR_RATIO = 2.5    # motor turns : output turns
# R_CATHETER is the radius of the capstan/roller that converts shaft rotation
# to linear catheter motion; 6 mm is the design specification for this prototype.
R_CATHETER = 6.0    # mm  – capstan / roller radius (design specification)

# Kinematics chain:
#   Motor RPM  n      = Q [L/min] × 1000 [mL/L]  /  V_rev [mL/rev]
#   Output RPM n_out  = n  /  gear_ratio
#   Catheter speed v  = 2π · r · n_out / 60     [mm/s]
motor_rpm = Q * 1000.0 / V_REV
output_rpm = motor_rpm / GEAR_RATIO
v_catheter = 2.0 * np.pi * R_CATHETER * output_rpm / 60.0

# Main line – 2.5 : 1 gearbox
ax2.plot(Q, v_catheter, color="#2196F3", linewidth=2.5, label="2.5 : 1 Gearbox")

# Clinical target zone: 7–10 mm/s (shaded green band)
ax2.axhspan(
    7.0,
    10.0,
    alpha=0.18,
    color="green",
    label="Clinical Target Zone (7–10 mm/s)",
)
# Explicit boundary lines for the band
ax2.axhline(7.0, color="green", linestyle=":", linewidth=1.0, alpha=0.7)
ax2.axhline(10.0, color="green", linestyle=":", linewidth=1.0, alpha=0.7)

# Operating point at Q = 1.0 L/min
Q_OP = 1.0  # L/min
v_op = 2.0 * np.pi * R_CATHETER * (Q_OP * 1000.0 / V_REV / GEAR_RATIO) / 60.0
ax2.plot(
    Q_OP,
    v_op,
    "o",
    color="#F44336",
    markersize=9,
    zorder=6,
    label=f"Operating Point: Q = {Q_OP} L/min → {v_op:.1f} mm/s",
)

ax2.set_xlim(0.5, 3.5)
ax2.set_xlabel("Supply Flow Rate (L/min)", fontsize=14)
ax2.set_ylabel("Catheter Linear Speed (mm/s)", fontsize=14)
ax2.set_title(
    "Flow Rate vs. Catheter Advancement Speed", fontsize=15, fontweight="bold"
)
ax2.legend(fontsize=12, loc="upper left")
ax2.grid(True, linestyle="--", alpha=0.45)

# ---------------------------------------------------------------------------
# Save and display
# ---------------------------------------------------------------------------
plt.tight_layout()
plt.savefig(OUTPUT_PNG, dpi=150, bbox_inches="tight")
print(f"Figure saved → {OUTPUT_PNG}")
plt.show()