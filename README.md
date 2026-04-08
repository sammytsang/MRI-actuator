# Three-Chamber Rolling-Diaphragm Pneumatic Motor
### MRI-Compatible Actuator for Endovascular Robotics

> **Project type:** Academic / Poster Presentation  
> **Application domains:** PCI · TAVR · TMVR  
> **Key constraint:** All components must be non-magnetic and MRI-safe

---

## Table of Contents
1. [Clinical Context & Objective](#1-clinical-context--objective)
2. [Mechanical Design & Mathematical Modeling](#2-mechanical-design--mathematical-modeling)
3. [Application & Gear Ratio Selection](#3-application--gear-ratio-selection)
4. [Repository Structure](#4-repository-structure)
5. [Animations & Visuals](#5-animations--visuals)
6. [References](#6-references)

---

## 1. Clinical Context & Objective

Minimally invasive endovascular procedures — including **Percutaneous Coronary Intervention (PCI)**, **Transcatheter Aortic Valve Replacement (TAVR)**, and **Transcatheter Mitral Valve Repair (TMVR)** — increasingly require real-time MRI guidance to improve anatomical visualisation and reduce radiation dose.

However, the strong static magnetic field (≥ 1.5 T) and rapidly switching gradient fields inside an MRI scanner make conventional electric motors completely unsafe. Ferromagnetic components experience violent force and torque, and induced eddy currents corrupt image quality.

**Objective:** Design a fully non-magnetic, pneumatically actuated motor that can:
- Insert and retract a catheter/guidewire at a clinically appropriate speed (**7–10 mm/s**)
- Deliver sufficient axial force (target **2 N**, margin **3–5 N**)
- Operate safely inside or immediately adjacent to an MRI bore

The solution is a **three-chamber rolling-diaphragm swashplate (wavy-track) pneumatic motor** — all structural parts are fabricated from plastics and non-ferrous alloys, with no windings, magnets, or iron cores.

---

## 2. Mechanical Design & Mathematical Modeling

### 2.1 Overview of the Mechanism

The motor converts compressed-air pressure into continuous shaft rotation through three layers:

| Layer | Component | Function |
|-------|-----------|----------|
| 1 | Rolling-diaphragm chambers (×3) | Pressure → vertical thrust |
| 2 | Push rods + wavy internal track | Vertical thrust → tangential force |
| 3 | Main shaft | Tangential force → output torque & rotation |

The **internal guide track** is rigidly coupled to the main shaft. As the three push rods press against the track's sinusoidal surface in sequence, the sloped geometry forces the track — and therefore the shaft — to rotate continuously.

### 2.2 Modeling Assumptions & Key Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Number of chambers | 3 | ~120° apart, three-phase arrangement |
| Supply / effective pressure difference | **2 bar** (200 000 Pa) | Instructor-specified upper limit |
| Chamber inner diameter (calculation basis) | **18.2 mm** | Effective pressure area |
| Rolling-diaphragm diameter | 18.5 mm | 0.3 mm difference treated as tolerance |
| Track profile | `h(θ) = 0.01 sin(2θ + φ)` m | 2 periods per revolution |
| Track total vertical travel | **20 mm** (amplitude = 10 mm) | Peak-to-valley |
| Roller contact radius (reference) | ~24 mm | Centerline of internal track |
| Operating sequence | **H-L-H** | High–Low–High, 120° phasing |

### 2.3 High–Low–High (H-L-H) 120° Sequencing

At any instant, one chamber is **inflated (High)**, the next is **exhausted (Low)**, and the third is **inflated (High)** again — phased exactly 120° apart. This ensures:

- At least **two** push rods are always actively pushing.
- Torque ripple is minimised compared with a single- or two-chamber design.
- Smooth, continuous shaft rotation without dead-centre stall.

```
Phase offset:  φ₁ = 0°   φ₂ = 120°   φ₃ = 240°
State pattern: H           L            H
               (next 120°)
               L           H            H
               (next 120°)
               H           H            L   ...
```

### 2.4 Single-Chamber Thrust

The effective pressure area of one chamber:

$$A = \frac{\pi d^2}{4} = \frac{\pi (0.0182)^2}{4} \approx 2.60 \times 10^{-4} \text{ m}^2$$

Theoretical thrust of one high-pressure chamber:

$$F_H = \Delta P \cdot A = 200{,}000 \times 2.60 \times 10^{-4} \approx \boxed{52.0 \text{ N}}$$

### 2.5 Force-to-Torque Conversion via Virtual Work

The push rods apply a vertical force to the wavy track. Using the **principle of virtual work** for an infinitesimal shaft rotation $d\theta$:

$$F \cdot dh = T \cdot d\theta \quad \Longrightarrow \quad \boxed{T = F \frac{dh}{d\theta}}$$

With the track function $h(\theta) = 0.01\sin(2\theta + \phi)$:

$$\frac{dh}{d\theta} = 0.02\cos(2\theta + \phi) \quad \Rightarrow \quad \max\!\left(\frac{dh}{d\theta}\right) = 0.02 \text{ m/rad}$$

The **total torque** from all three rods (H-L-H, with $F_L \approx 0$):

$$T(\theta) = \sum_{i=1}^{3} F_i(\theta)\,\frac{dh(\theta - \phi_i)}{d\theta}$$

### 2.6 Theoretical Peak Torque

As a first-order estimate with two rods at high pressure:

$$T_{\max} \approx F_H \cdot \max\!\left(\frac{dh}{d\theta}\right) = 52.0 \times 0.02 = \boxed{1.04 \text{ N·m}}$$

Accounting for overall mechanical efficiency (η ≈ 0.6–0.8):

$$T_{\text{usable}} \approx 0.62\text{–}0.83 \text{ N·m}$$

### 2.7 Main-Shaft Speed Estimation

Speed cannot be derived from geometry alone; it requires the supply flow rate $Q$ and the geometric displacement per revolution $V_{\text{rev}}$:

$$n \approx \frac{Q}{V_{\text{rev}}}$$

- Single-chamber displacement per event: $A \times 20\text{ mm} \approx 5.20\text{ mL}$  
- 3 chambers × 2 effective events per revolution → $V_{\text{rev}} \approx 31.2\text{ mL/rev}$

| Supply Flow Rate $Q$ | Predicted Main-Shaft Speed |
|----------------------|---------------------------|
| 0.5 L/min | ~16.0 rpm |
| **1.0 L/min** | **~32.1 rpm** |
| 2.0 L/min | ~64.1 rpm |
| 3.0 L/min | ~96.2 rpm |

> **Design point used below:** $n_{\text{motor}} \approx 32\text{ rpm}$ at $Q = 1.0\text{ L/min}$.

---

## 3. Application & Gear Ratio Selection

### 3.1 Clinical Speed Target

Based on in-vivo endovascular navigation literature, the target catheter advancement speed is **7–10 mm/s**.

| Reference | Reported Speed |
|-----------|---------------|
| In-Vivo Validation of a Novel Robotic Platform for Endovascular Intervention (2023) | 7–10 mm/s average feed rate, 30 mm/s max |
| Portable and Versatile Catheter Robot (2025) | 0.24–24 mm/s guidewire; ~1 mm/s PCI phantom |

### 3.2 Force Requirements

| Level | Force Range | Use Case |
|-------|------------|----------|
| Fine contact / safety | 0.02–0.15 N | Vessel-wall sensing, transseptal approach |
| Advancement / navigation | 0.1–2.0 N | Guidewire/catheter forward insertion |
| Drive margin | 3–5 N | Roller slip, mechanical losses, stiff catheters |

> **Application target:** 2 N · **Capability margin:** 3–5 N

### 3.3 Output-Shaft Speed Required

For a roller of radius $r = 6\text{ mm}$:

$$n_{\text{out}} = \frac{60v}{2\pi r}$$

| Target Speed $v$ | Required Output-Shaft Speed $n_{\text{out}}$ |
|-----------------|---------------------------------------------|
| 7 mm/s | 11.1 rpm |
| 10 mm/s | 15.9 rpm |

### 3.4 Gear Ratio Selection

$$i = \frac{n_{\text{motor}}}{n_{\text{out}}} \Rightarrow i_{(7\text{ mm/s})} \approx \frac{32}{11.1} \approx 2.87, \quad i_{(10\text{ mm/s})} \approx \frac{32}{15.9} \approx 2.01$$

**Required transmission ratio range: ~2.0–2.9**

A **2.5:1 planetary reduction gearbox** is selected (Scheme A):

$$n_{\text{out}} = \frac{32}{2.5} = 12.8\text{ rpm}$$

$$v = \frac{2\pi r \cdot n_{\text{out}}}{60} = \frac{2\pi \times 0.006 \times 12.8}{60} \approx \boxed{8.0\text{ mm/s}}$$

This sits at the **centre of the 7–10 mm/s clinical target range** ✓

### 3.5 Torque Verification

$$T_{\text{out}} \approx T_{\text{motor}} \cdot i \cdot \eta = 1.04 \times 2.5 \times 0.7 \approx 1.82\text{ N·m}$$

| Requirement | Torque Needed | Scheme A Delivers |
|-------------|--------------|-------------------|
| 2 N end force (roller $r=6$ mm) | 0.012 N·m | **1.82 N·m** ✓ |
| 5 N margin force | 0.030 N·m | **1.82 N·m** ✓ |

The gearbox provides a **large torque margin**; its primary role is **speed matching and feed resolution**, not torque amplification.

---

## 4. Repository Structure

```
MRI-actuator/
├── arduino_control/
│   └── motor_control.ino          # Arduino firmware for pneumatic valve timing
├── simulation/
│   ├── 3d_axial_animation.py      # 3D axial simulation of the swashplate mechanism
│   ├── motor_animation.py         # 2D mechanism inference / animation plots
│   └── requirements.txt           # Python dependencies
└── MRI actuator.7z                # Raw Fusion 360 CAD assembly files
```

| File | Description |
|------|-------------|
| `arduino_control/motor_control.ino` | Arduino sketch that manages the **pneumatic solenoid valve timing** for H-L-H sequencing. Controls the 120° phase offsets between the three chambers to produce smooth, continuous shaft rotation. |
| `simulation/3d_axial_animation.py` | Python script that generates a **3D simulation** of the rolling-diaphragm swashplate mechanism, visualising how the three push rods drive the wavy track and main shaft. |
| `simulation/motor_animation.py` | Python script for producing **2D mechanism inference plots** and animations — torque profiles, displacement curves, and phase diagrams. |
| `MRI actuator.7z` | Compressed archive of the complete **Fusion 360 CAD assembly**, including all parts, joints, and rendering configurations. |

---

## 5. Animations & Visuals

> **How to generate the visuals:**  
> 1. Install dependencies: `pip install -r simulation/requirements.txt`  
> 2. Run `python simulation/3d_axial_animation.py` → exports the 3D mechanism GIF/video  
> 3. Run `python simulation/motor_animation.py` → exports the inference/torque-profile plot  
> 4. Record the Fusion 360 assembly animation using **Command + Shift + 5** on macOS  
> 5. Drop the generated files into this directory and update the paths below

### 3D Mechanism Animation

![3D Mechanism Animation](assets/3d_axial_animation.gif)

*Three-chamber rolling-diaphragm swashplate in motion — push rods drive the wavy track, converting linear pneumatic force into continuous shaft rotation.*

### Torque / Inference Plot

![Inference Plot](assets/motor_animation.gif)

*Phase-resolved torque profile showing the H-L-H sequencing contribution from each of the three chambers across one full revolution.*

### Fusion 360 CAD Model

![CAD Assembly](assets/cad_assembly.gif)

*Full CAD assembly render of the MRI-compatible pneumatic motor — non-ferrous materials throughout, designed for operation inside a 1.5 T / 3 T MRI bore.*

---

## 6. References

1. B. Yang *et al.*, "High-Performance Continuous Hydraulic Motor for MR Safe Robotic Teleoperation," *IEEE RA-L*, 2019.
2. E. M. Gosline *et al.*, "In-Vivo Validation of a Novel Robotic Platform for Endovascular Intervention," *IEEE TMRB*, 2023.  
   — *Reported average feed/retraction rate: **7–10 mm/s**; max linear speed: 30 mm/s.*
3. X. Hu *et al.*, "Portable and Versatile Catheter Robot for Image-Guided Cardiovascular Interventions," 2025.  
   — *Peak insertion force: 5.49 N (8F guide catheter); guidewire range: 0.24–24 mm/s.*

---

<details>
<summary>Key Metrics Summary</summary>

| Quantity | Value |
|----------|-------|
| Supply pressure | 2 bar |
| Chamber inner diameter | 18.2 mm |
| Theoretical thrust per chamber | **52.0 N** |
| Theoretical peak torque (main shaft) | **1.04 N·m** |
| Usable torque (η = 0.6–0.8) | 0.62–0.83 N·m |
| Main-shaft speed @ 1.0 L/min | **~32 rpm** |
| Gear ratio | **2.5 : 1** |
| Output-shaft speed | 12.8 rpm |
| Catheter advancement speed | **~8.0 mm/s** |
| Clinical target range | 7–10 mm/s ✓ |

</details>
