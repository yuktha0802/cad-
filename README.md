<div align="center">

# TorqWings CAD Studio
### Part 2: Engineering Specification → Prototype-Ready Aircraft CAD System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](pyproject.toml)
[![STEP](https://img.shields.io/badge/STEP-ISO%2010303-4A5568?style=for-the-badge)](TORQWINGS_CAD_STUDIO.md)
[![Manufacturing](https://img.shields.io/badge/Manufacturing-DXF%20%2F%20SVG%20%2F%20STL-green?style=for-the-badge)](TORQWINGS_CAD_STUDIO.md)
[![Release Gate](https://img.shields.io/badge/Release%20Gate-Automated%20QA-orange?style=for-the-badge)](TORQWINGS_STATUS.md)

[Canonical Documentation](TORQWINGS_CAD_STUDIO.md) | [Architecture](TORQWINGS_ARCHITECTURE.md) | [Pipeline](TORQWINGS_PIPELINE.md) | [Status](TORQWINGS_STATUS.md)

</div>

---

## 📌 Executive Summary

**TorqWings CAD Studio** is an integrated engineering-driven aircraft CAD, structural synthesis, and prototype manufacturing platform. The platform automates the transition from multi-disciplinary conceptual UAV/aircraft engineering design specifications into complete, verified 3D CAD solid models, synthesized internal airframe structures, classified digital manufacturing packages (laser cutting, 3D printing), deterministic assembly instructions, interactive 3D visualization, and strict final prototype release gates.

The system serves as **Part 2** of the end-to-end TorqWings aerospace workflow, ingesting engineering requirements produced by **Part 1** (Engineering Design & Requirement Synthesis) and transforming them into production-ready physical prototype data packages.

```
PART 1: Engineering Design & Requirement Synthesis
        ↓ (Engineering Specification / JSON / Markdown)
PART 2: TorqWings CAD Studio
        ↓ Document Ingestion & Parameter Extraction
        ↓ Normalized Engineering Parameter Model (EXPLICIT / DERIVED / CONFLICT)
        ↓ Outer Mold Line (OML) Aircraft CAD Solid Generation
        ↓ Internal Structural Synthesis (Formers, Longerons, Ribs, Spars)
        ↓ Digital Manufacturing Decomposition (Laser DXF/SVG, 3D Print STL)
        ↓ Assembly & Interlocking Tab/Slot Joint Synthesis
        ↓ Dimensional & Configuration Validation
        ↓ Formal Engineering Review Engine
        ↓ Prototype Build Package & Shop-Floor SOP (BOM, build_instructions.md)
        ↓ 3D Multi-Mode Build Visualization (Assembled, Exploded, Structure, Mfg)
        ↓ Final Prototype Release Gate QA (release_manifest.json)
        ↓
Physical Prototype Fabrication (Laser Cutting, 3D Printing, Bench Assembly)
```

---

## 🗂️ Canonical Documentation

| Document | Purpose |
| :--- | :--- |
| **[TORQWINGS_CAD_STUDIO.md](TORQWINGS_CAD_STUDIO.md)** | **Primary Canonical Engineering Document:** Comprehensive 26-section specification covering system overview, identity, workflow, engines, FW-007 baseline, warnings, limitations, and boundaries. |
| **[TORQWINGS_ARCHITECTURE.md](TORQWINGS_ARCHITECTURE.md)** | **System Architecture:** Detailed component breakdown of `cadpy` engines, frontend viewer, classes, functions, inputs, outputs, and dependencies. |
| **[TORQWINGS_PIPELINE.md](TORQWINGS_PIPELINE.md)** | **Pipeline Specification:** Stage-by-stage guide covering INPUT, PROCESS, OUTPUT, VALIDATION, and TRACEABILITY for all 13 pipeline phases. |
| **[TORQWINGS_STATUS.md](TORQWINGS_STATUS.md)** | **Development & Acceptance Status:** Phase 1–13 completion sign-off and FW-007 acceptance campaign test reports. |

---

## ✈️ Verified Baseline: FW-007 Test Aircraft

The platform is continuously verified against the **FW-007** baseline aircraft (Twin-Boom / Conventional Fixed-Wing UAV):
* **Wingspan:** $2000.0\text{ mm}$ ($2.0\text{ m}$)
* **Fuselage Length:** $1500.0\text{ mm}$ ($1.5\text{ m}$)
* **Horizontal Tail Span:** $500.0\text{ mm}$ ($0.5\text{ m}$)
* **Vertical Tail Height:** $400.0\text{ mm}$ ($0.4\text{ m}$)
* **Propulsion:** APC $12 \times 6\text{E}$ propeller ($304.8\text{ mm}$ diameter), tractor configuration.
* **Synthesized Airframe Structure:** $48$ individually modeled structural solids.
* **Classified Manufacturing Parts:** $48$ physical parts ($47$ laser-cut balsa/aeroply parts + $1$ 3D-printed PETG/PLA wing bracket).
* **Structural Joints:** $69$ interlocking tab-and-slot joint mates.
* **Laser Cutting Stock:** $3$ nested $900 \times 600\text{ mm}$ sheets.
* **Assembly Steps:** $5$ sequential assembly stages documented in `build_instructions.md`.
* **Release Gate State:** `READY_WITH_WARNINGS` (Preserves known Part 1 MTOW requirement conflict of $5.5\text{ kg}$ vs $11.0\text{ kg}$).

---

## ⚠️ Important Engineering Boundaries

> [!CAUTION]
> **What the System Does NOT Claim:**
> * **No CFD / Aerodynamic Optimization:** Geometry is generated from input specifications; it does not perform fluid dynamics simulation.
> * **No FEA / Structural Safety Certification:** Structural solids are geometrically synthesized; finite element stress analysis must be performed in external FEA packages.
> * **No Airworthiness or Flight Certification:** Prototype-ready indicates validation for benchtop digital manufacturing; **it does not certify airworthiness or manned flight safety**.
> * **No Synthetic Value Guessing:** Conflicting or omitted requirements remain `CONFLICT` or `UNKNOWN` and are explicitly reported.

---

## 💻 Quick Start & Usage

### 1. Environment Setup
```powershell
# Create virtual environment and install CAD dependencies
python -m venv .venv
.\.venv\Scripts\activate
pip install -e packages/cadpy
```

### 2. Execute End-to-End Pipeline
```python
from cadpy.pipeline import DesignStudioPipeline

pipeline = DesignStudioPipeline()
result = pipeline.run(
    specification_path="models/TW-FW-20260921-215327/specification.json",
    output_dir="models/TW-FW-20260921-215327/v1"
)

print(f"Release Status: {result.release_manifest.release_status}")
```

### 3. Launch CAD Studio / CAD Viewer Frontend
```bash
npm --prefix viewer install
npm --prefix viewer run dev -- --host 127.0.0.1
```
Open the browser at `http://127.0.0.1:5173/?dir=models&file=TW-FW-20260921-215327/TW-FW-20260921-215327_complete_aircraft.step`.

---

## 🧰 Underlying Skills & Agent Capabilities

TorqWings CAD Studio is built upon modular CAD, robotics, and manufacturing agent skills located in `skills/`:

| Skill | Description | Location |
| :--- | :--- | :--- |
| **CAD** | Parametric 3D solid modeling kernel with STEP, STL, 3MF, and GLB export. | [`skills/cad`](skills/cad/SKILL.md) |
| **CAD Viewer** | Interactive browser workbench for 3D inspection and review. | [`skills/cad-viewer`](skills/cad-viewer/SKILL.md) |
| **DXF** | 2D CAD profile generator for laser, waterjet, and plasma cutting. | [`skills/dxf`](skills/dxf/SKILL.md) |
| **G-code** | Mesh slicing and toolpath generation for FDM 3D printers. | [`skills/gcode`](skills/gcode/SKILL.md) |
| **URDF / SRDF / SDF** | Robot kinematics, physics, and MoveIt2 simulation models. | [`skills/urdf`](skills/urdf/SKILL.md) |

---

## 👥 Organization

* **Project:** TorqWings CAD Studio
* **Team:** TorqWings Team
* **Domain:** `torqwings.com`
* **License:** MIT License
