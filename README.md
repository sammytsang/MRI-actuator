# MRI-Compatible Pneumatic Rotary Actuator
### Three-Chamber Rolling-Diaphragm Swashplate Motor for Endovascular Catheter Navigation

> **Poster Project — Master's Level Academic Presentation**
> Author: Sam Tsang | MRI Actuator Project

---

## Table of Contents

1. [Project Overview & Clinical Context](#1-project-overview--clinical-context)
2. [Mechanical Design — The 3-Layer Power Transmission Chain](#2-mechanical-design--the-3-layer-power-transmission-chain)
3. [Output Estimation & Mathematical Modeling](#3-output-estimation--mathematical-modeling)
4. [Gear Ratio Selection](#4-gear-ratio-selection)
5. [Simulation & Control](#5-simulation--control)
6. [Repository Structure](#6-repository-structure)
7. [Getting Started](#7-getting-started)

---

## 1. Project Overview & Clinical Context

### The Clinical Problem

Minimally invasive endovascular procedures — including **Percutaneous Coronary Intervention (PCI)**, **Transcatheter Aortic Valve Replacement (TAVR)**, and **Transcatheter Mitral Valve Repair (TMVR)** — increasingly benefit from real-time MRI guidance. MRI provides superior soft-tissue contrast and allows radiation-free, three-dimensional road-mapping of complex vascular anatomy compared to conventional X-ray fluoroscopy.

However, a critical barrier exists: **conventional robotic actuators are incompatible with MRI environments.** Standard electric motors contain ferromagnetic components that are violently attracted to the scanner's superconducting magnet and generate radiofrequency (RF) noise that degrades image quality. There is therefore a strong clinical need for a fully non-magnetic, MRI-safe actuator capable of driving a catheter inside the bore of a clinical MRI scanner.

### Our Approach: Pneumatic Actuation

This project presents an **MRI-compatible pneumatic rotary motor** built entirely from non-magnetic materials (aluminum, PEEK, and acrylic). Compressed air — supplied via long, flexible tubing routed safely out of the scanner room — drives three rolling-diaphragm chambers arranged in a swashplate (axial-piston) configuration. The rotating output shaft advances the catheter through a downstream gear train and lead screw.

### Clinical Performance Targets

| Parameter | Target |
|---|---|
| Catheter linear speed | **7–10 mm/s** |
| Required end-force | **2 N** (minimum) |
| Safety margin force | **3–5 N** |
| Operating pressure | **2 bar** (gauge) |
| MRI compatibility | Fully non-magnetic; RF-transparent |

---

## 2. Mechanical Design — The 3-Layer Power Transmission Chain

### 2.1 Mechanism Overview

The motor converts pneumatic supply pressure into continuous shaft rotation through a **three-stage power transmission chain**:

```
Supply Pressure  →  Vertical Thrust  →  Track Conversion (H-L-H)  →  Main-Shaft Torque
```

Each stage is described below.

### 2.2 Stage 1 — Pneumatic Chamber → Vertical Thrust

Three cylindrical chambers are arranged symmetrically at **0°, 120°, and 240°** around the central shaft axis. Each chamber contains a rolling diaphragm that seals pressurised air against a piston face. When a solenoid valve opens, the gauge pressure acts on the full piston area, generating a pure axial (vertical) thrust force directed along the shaft axis.

- **Chamber diameter:** 18.2 mm → effective bore area = 260 mm²
- **Supply pressure:** 2 bar = 200 kPa
- **Thrust per chamber (F):** `F = P × A = 200,000 Pa × 260×10⁻⁶ m² ≈` **52.0 N**

### 2.3 Stage 2 — Track Conversion (High-Low-High Cam Profile)

Each piston terminates in a cam follower that bears against the swashplate (a disc tilted at angle *α* relative to the shaft plane). As the shaft rotates, the follower's instantaneous height traces a sinusoidal profile — rising over the high lobe (`H`), passing through the low point (`L`), and rising again — giving the characteristic **H-L-H** sequence. This converts axial piston displacement into an angular moment arm that drives the plate to rotate.

The key geometric parameter is the rate of height change with shaft angle:

$$\frac{dh}{dθ} = r \tan(α)$$

where *r* is the radial distance from the shaft centre to the follower contact point, and *α* is the swashplate tilt angle.

### 2.4 Stage 3 — Main-Shaft Torque Output

Only **one** solenoid valve is energised at any instant (120°-phased commutation). The active piston's vertical thrust acts through the instantaneous moment arm to produce net shaft torque. The 120° phasing ensures at least one chamber is always in its power stroke, delivering smooth, continuous torque.

### 2.5 CAD Model

The Fusion 360 assembly (`MRI actuator.7z`) contains the full parametric model of the motor, including the swashplate, chamber bodies, piston rods, and output shaft.

> ![Motor Assembly](docs/images/motor_assembly.gif)
> *Figure 1 — (**Placeholder** — record a screen capture of the Fusion 360 animation and save as `docs/images/motor_assembly.gif`) Animated render of the three-chamber swashplate motor. The translucent housing reveals the three pistons firing sequentially as the swashplate rotates.*

> ![Exploded View](docs/images/motor_exploded.png)
> *Figure 2 — (**Placeholder** — export an exploded-view screenshot from Fusion 360 and save as `docs/images/motor_exploded.png`) Exploded CAD view showing (left to right): chamber body, rolling diaphragm, piston, cam follower, swashplate, output shaft, and end cap.*

---

## 3. Output Estimation & Mathematical Modeling

### 3.1 Core Virtual-Work Equation

The core virtual-work equation is:

$$\boxed{T = F \cdot \frac{dh}{dθ}}$$

where:
- `T` = output torque (N·m)
- `F` = axial thrust force per chamber (N)
- `dh/dθ` = instantaneous slope of the swashplate cam profile (m/rad)

### 3.2 Theoretical Output — Key Numbers

| Quantity | Symbol | Value |
|---|---|---|
| Supply pressure | *P* | **2 bar** = 200 kPa |
| Chamber bore diameter | *D* | **18.2 mm** |
| Effective piston area | *A* | **260 mm²** |
| Theoretical thrust/chamber | *F* | **52.0 N** |
| Cam moment arm (`dh/dθ`) | — | **0.02 m/rad** |
| Theoretical peak torque | *T* | **1.04 N·m** |

$$T_{\text{peak}} = F \times \frac{dh}{d\theta} = 52.0\,\text{N} \times 0.02\,\text{m/rad} = \mathbf{1.04\,\text{N·m}}$$

### 3.3 Speed Estimation from Flow Rate

Motor speed depends on the volumetric flow rate supplied to each chamber. For a given flow rate *Q* (L/min), the shaft speed *n* (rpm) is estimated by:

$$n = \frac{Q}{3 \times V_{\text{stroke}}} \times 1000$$

where `V_stroke` is the displacement volume per chamber per cycle (mL).

| Flow Rate (L/min) | Estimated Speed (rpm) |
|---|---|
| 0.5 | ~16 |
| **1.0** | **~32** |
| 1.5 | ~48 |
| 2.0 | ~64 |

> **Design operating point:** `1.0 L/min → ~32 rpm` at the motor output shaft.

---

## 4. Gear Ratio Selection

### 4.1 Catheter Speed Requirement

Working from the motor operating point of **~32 rpm** (§3.3), a downstream gear reduction steps the speed down to match the catheter advance target. A friction-roller drive wheel of radius **r = 6 mm** converts output shaft rotation to linear catheter motion:

$$v_{\text{catheter}} = 2\pi r \cdot \frac{n_{\text{output}}}{60}$$

The goal is to land within the **7–10 mm/s** clinical window.

### 4.2 Scheme A — Selected Design: 2.5:1 Ratio

| Parameter | Value |
|---|---|
| Motor speed | **32 rpm** |
| Gear ratio | **2.5 : 1** |
| Output shaft speed | **12.8 rpm** |
| Drive roller radius | 6 mm |
| Linear catheter speed | **8.0 mm/s** ✅ |

$$v_{\text{catheter}} = 2\pi \times 0.006\,\text{m} \times \frac{12.8}{60}\,\text{rev/s} \approx \mathbf{8.0\,\text{mm/s}}$$

> **Scheme A with a 2.5:1 ratio and a 6 mm drive roller delivers ~8.0 mm/s — perfectly centred within the 7–10 mm/s clinical target window.**

### 4.3 Rationale for Scheme A

- **Simplicity:** A single-stage planetary or spur reduction achieves 2.5:1 without stacking multiple stages, minimising backlash and assembly complexity.
- **Safety margin:** At 52 N thrust and 1.04 N·m peak torque, the motor far exceeds the 2 N end-force requirement even after efficiency losses (~60–70% for pneumatic systems), providing the required **3–5 N safety margin**.
- **MRI footprint:** A compact single-stage gearhead is mechanically simple and avoids ferromagnetic materials.

---

## 5. Simulation & Control

### 5.1 Python Kinematic Simulations

Two Python scripts visualise the motor kinematics in real time. They require only `numpy` and `matplotlib`.

#### Install dependencies

```bash
cd simulation
pip install -r requirements.txt
```

#### `3d_axial_animation.py` — 3-D Swashplate Visualisation

Renders a full 3-D animation of the axial-piston swashplate mechanism. A translucent cyan swashplate disk rotates continuously while three colour-coded piston rods (Blue = A, Green = B, Red = C) reciprocate in sequence. The active (pressurised) piston lights up in its cylinder colour; inactive pistons turn grey.

```bash
python simulation/3d_axial_animation.py
```

> ![3D Axial Animation](docs/images/3d_axial_screenshot.png)
> *Figure 3 — (**Placeholder** — run the script, take a screenshot, and save as `docs/images/3d_axial_screenshot.png`) Screenshot of the 3-D swashplate animation. Swashplate (cyan) spins while pistons A/B/C fire sequentially.*

#### `motor_animation.py` — 2-D Timing Diagram & Mechanical View

Opens a three-panel figure:

| Panel | Content |
|---|---|
| Top | Sinusoidal piston-position waveforms (120° phase offsets) |
| Middle | Square-wave solenoid valve commutation timing diagram |
| Bottom | 2-D mechanical animation — spinning rotor + three radial pistons |

A vertical "now" cursor sweeps across the top two panels in sync with the rotor angle shown in the bottom panel.

```bash
python simulation/motor_animation.py
```

> ![Motor Animation](docs/images/motor_animation_screenshot.png)
> *Figure 4 — (**Placeholder** — run the script, take a screenshot, and save as `docs/images/motor_animation_screenshot.png`) Three-panel simulation. Top: piston displacement. Middle: valve timing (H-L-H commutation). Bottom: 2-D mechanical animation.*

### 5.2 Arduino Valve Control (`arduino_control/motor_control.ino`)

The Arduino sketch implements the **120° H-L-H commutation** logic for the three solenoid valves in a non-blocking manner using `millis()`.

#### Hardware wiring

| Arduino Pin | Connection |
|---|---|
| `D2` | Valve A solenoid driver (MOSFET gate / relay coil) |
| `D3` | Valve B solenoid driver |
| `D4` | Valve C solenoid driver |

#### Timing

```
Full revolution  : 1.5 s
Phase per valve  : 0.5 s   (= 1/3 of cycle)
Sequence         : A → B → C → A → …
```

The `PHASE_DURATION_MS` variable can be adjusted at runtime (e.g., via a potentiometer on `A0`) to change motor speed without modifying the firmware:

```cpp
// Example: map a speed potentiometer to 0.2–2 s phase duration
int speedPot = analogRead(A0);
PHASE_DURATION_MS = map(speedPot, 0, 1023, 200, 2000);
```

#### Upload

1. Open `arduino_control/motor_control.ino` in the [Arduino IDE](https://www.arduino.cc/en/software).
2. Select your board (e.g., **Arduino Uno**) and the correct COM/USB port.
3. Click **Upload** (▶).
4. Open **Serial Monitor** at **9600 baud** to observe phase transitions in real time.

---

## 6. Repository Structure

```
MRI-actuator/
├── MRI actuator.7z          # Fusion 360 CAD assembly (full parametric model)
├── arduino_control/
│   └── motor_control.ino    # Non-blocking 3-phase solenoid valve controller
├── simulation/
│   ├── 3d_axial_animation.py  # 3-D swashplate / axial-piston animation
│   ├── motor_animation.py     # 2-D timing diagram + mechanical animation
│   └── requirements.txt       # Python dependencies (numpy, matplotlib)
├── docs/
│   └── images/              # Figures for README (add screenshots/renders here)
│       ├── motor_assembly.gif         # Fusion 360 animation (placeholder)
│       ├── motor_exploded.png         # Exploded CAD view (placeholder)
│       ├── 3d_axial_screenshot.png    # Python 3-D animation screenshot (placeholder)
│       └── motor_animation_screenshot.png  # Python 2-D animation screenshot (placeholder)
└── README.md
```

---

## 7. Getting Started

### Prerequisites

- Python ≥ 3.8
- Arduino IDE (for uploading `motor_control.ino`)
- 7-Zip or p7zip (to extract `MRI actuator.7z`)
- Autodesk Fusion 360 (to open and inspect the CAD model)

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/sammytsang/MRI-actuator.git
cd MRI-actuator

# 2. Install Python dependencies
pip install -r simulation/requirements.txt

# 3. Run the 3-D swashplate animation
python simulation/3d_axial_animation.py

# 4. Run the 2-D timing diagram / mechanical animation
python simulation/motor_animation.py

# 5. Extract the CAD files (requires 7-Zip)
7z x "MRI actuator.7z"
```

---

## Key Performance Summary

| Metric | Value |
|---|---|
| Operating pressure | 2 bar |
| Chamber bore diameter | 18.2 mm |
| Thrust per chamber | **52.0 N** |
| Peak motor torque | **1.04 N·m** |
| Motor speed (@ 1 L/min) | **~32 rpm** |
| Gear ratio (Scheme A) | **2.5 : 1** |
| Output shaft speed | **12.8 rpm** |
| Catheter linear speed | **~8.0 mm/s** ✅ |
| Clinical target speed | 7–10 mm/s |
| End-force (minimum) | 2 N |
| Safety margin | 3–5 N |

---

*MRI Actuator Project — Sam Tsang. All CAD files, simulation scripts, and firmware are provided for academic research purposes.*
