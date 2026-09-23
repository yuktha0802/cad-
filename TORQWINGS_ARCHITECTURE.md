# TorqWings Design Studio — System Architecture

This document describes the actual, implemented architecture of **TorqWings Design Studio (Part 2: Engineering Specification → Prototype-Ready Aircraft CAD System)**.

---

## 1. System Overview

TorqWings Design Studio is structured as a modular Python and TypeScript/React platform. The backend runtime (`cadpy`) provides the core aerospace parameter normalization, parametric CAD generation, structural synthesis, digital manufacturing decomposition, revision management, and release gate validation. The frontend runtime (`viewer` / `cadjs`) provides interactive 3D WebGL visualization, tree inspection, and exploded build guidance.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           TORQWINGS DESIGN STUDIO                               │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                          Frontend Layer (viewer/)                       │   │
│   │   • React / Vite Web Application                                        │   │
│   │   • CAD Viewer & Design Studio Workbench UI                             │   │
│   │   • cadjs Rendering Engine (Three.js / WebGL / B-Rep Topology)          │   │
│   │   • Multi-mode Visualizer (Assembled, Exploded, Structure, Mfg)         │   │
│   └────────────────────────────────────▲────────────────────────────────────┘   │
│                                        │ HTTP / JSON / STEP / GLB               │
│   ┌────────────────────────────────────▼────────────────────────────────────┐   │
│   │                       Core CAD & Mfg Engine (cadpy)                     │   │
│   │                                                                         │   │
│   │   ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐    │   │
│   │   │ requirements.py  │──►│   aircraft.py    │──►│   structure.py   │    │   │
│   │   │ (Spec & Norm)    │   │   (OML CAD)      │   │   (Airframe)     │    │   │
│   │   └──────────────────┘   └──────────────────┘   └────────┬─────────┘    │   │
│   │                                                          │              │   │
│   │   ┌──────────────────┐   ┌──────────────────┐   ┌────────▼─────────┐    │   │
│   │   │ build_package.py │◄──│   review.py      │◄──│ manufacturing.py │    │   │
│   │   │ (BOM & SOP)      │   │   (Eng Review)   │   │ (Laser / 3D Print│    │   │
│   │   └────────┬─────────┘   └──────────────────┘   └──────────────────┘    │   │
│   │            │                                                            │   │
│   │   ┌────────▼─────────┐   ┌──────────────────┐   ┌──────────────────┐    │   │
│   │   │ visualization.py │──►│ release_gate.py  │──►│   pipeline.py    │    │   │
│   │   │ (3D View States) │   │ (Release QA)     │   │ (Orchestrator)   │    │   │
│   │   └──────────────────┘   └──────────────────┘   └──────────────────┘    │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                        │
│   ┌────────────────────────────────────▼────────────────────────────────────┐   │
│   │                       Artifact & Output Storage                         │   │
│   │   • models/<AIRCRAFT_ID>/v1/ (STEP, STL, DXF, SVG, JSON, MD)            │   │
│   │   • models/<AIRCRAFT_ID>/v1/release/release_manifest.json               │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Inventory

### 2.1. Requirement Ingestion & Normalization
* **Path:** [`packages/cadpy/src/cadpy/requirements.py`](file:///c:/Users/samyuktha/OneDrive/Documents/text-to-cad-main/packages/cadpy/src/cadpy/requirements.py)
* **Responsibility:** Ingests raw Part 1 engineering reports (JSON, Dict, Markdown tables, datasheets); extracts parameters, standardizes units (SI/engineering), calculates derived parameters, detects contradictions, and produces a normalized specification model.
* **Major Classes:** `AircraftSpecification`, `Requirement`, `WingSpec`, `FuselageSpec`, `TailSpec`, `PropulsionSpec`, `MassSpec`, `CGSpec`, `InternalBaysSpec`, `ConfigurationSpec`, `MissionSpec`.
* **Major Functions:** `parse_aircraft_specification()`, `validate_aircraft_specification()`, `derive_values()`, `normalize_unit()`.
* **Inputs:** Raw JSON strings, Python dictionaries, or Markdown text.
* **Outputs:** Validated `AircraftSpecification` instance with provenance tracking.
* **Dependencies:** Standard library (`typing`, `dataclasses`, `json`, `re`, `math`).
* **Current Status:** COMPLETE & VERIFIED.

---

### 2.2. Outer Mold Line (OML) Aircraft CAD Generator
* **Path:** [`packages/cadpy/src/cadpy/aircraft.py`](file:///c:/Users/samyuktha/OneDrive/Documents/text-to-cad-main/packages/cadpy/src/cadpy/aircraft.py)
* **Responsibility:** Converts normalized specifications into watertight 3D solid B-Rep models for wings, fuselage, empennage, propulsion cowls, and internal equipment cavities.
* **Major Classes:** `CADGenerationResult`.
* **Major Functions:** `generate_aircraft_from_spec()`, `generate_aircraft()`, `build_wing()`, `build_fuselage()`, `build_horizontal_tail()`, `build_vertical_tail()`, `build_propulsion()`, `build_internal_envelopes()`, `naca_points()`, `clarky_points()`.
* **Inputs:** `AircraftSpecification` or geometric parameter dictionaries.
* **Outputs:** `CADGenerationResult` containing `build123d.Compound` solids, dimensions, volume properties, and STEP/GLB file paths.
* **Dependencies:** `build123d`, `OpenCASCADE` (via `cadpy.assembly`, `cadpy.render`).
* **Current Status:** COMPLETE & VERIFIED.

---

### 2.3. Structural Airframe Synthesizer
* **Path:** [`packages/cadpy/src/cadpy/structure.py`](file:///c:/Users/samyuktha/OneDrive/Documents/text-to-cad-main/packages/cadpy/src/cadpy/structure.py)
* **Responsibility:** Synthesizes internal load-bearing structural members (bulkheads, formers, longerons, wing ribs, wing spars, tail framework, attachment blocks) constrained by the OML CAD geometry.
* **Major Classes:** `StructuralProfile`, `StructuralComponentMetadata`.
* **Major Functions:** `synthesize_fuselage_structure()`, `synthesize_wing_structure()`, `synthesize_tail_structure()`, `synthesize_vertical_tail_structure()`, `build_wing_fuselage_attachment()`, `validate_structure()`.
* **Inputs:** `AircraftSpecification`, OML aircraft compound solid.
* **Outputs:** Airframe structural solid compound ($48$ solids for FW-007 baseline) and metadata catalog.
* **Dependencies:** `build123d`, `cadpy.aircraft`.
* **Current Status:** COMPLETE & VERIFIED.

---

### 2.4. Digital Manufacturing Decomposition Engine
* **Path:** [`packages/cadpy/src/cadpy/manufacturing.py`](file:///c:/Users/samyuktha/OneDrive/Documents/text-to-cad-main/packages/cadpy/src/cadpy/manufacturing.py)
* **Responsibility:** Classifies structural solids into physical manufacturing domains (planar sheet parts vs. 3D-printable solid brackets), nests flat parts onto standard stock sheets, generates 2D DXF/SVG toolpaths with kerf compensation, produces 3D print STLs, and synthesizes tab-and-slot joint interlocks.
* **Major Classes:** `ManufacturingClassifier`, `SheetNester`, `ManufacturingValidationEngine`, `ThreeDPrintExporter`, `ManufacturingBOM`, `ManufacturingPart`, `ManufacturingSheet`, `ManufacturingJoint`.
* **Major Functions:** `generate_complete_manufacturing_pipeline()`, `export_part_dxf()`, `export_part_svg()`, `export_sheet_dxf()`, `export_sheet_svg()`.
* **Inputs:** Structural airframe compound solid, material thickness profiles.
* **Outputs:** 2D DXF/SVG cut files, nested DXF/SVG sheet layouts, 3D print STL files, manufacturing BOM, joint mate dictionary.
* **Dependencies:** `build123d`, `ezdxf` (or DXF writer), `cadpy.structure`.
* **Current Status:** COMPLETE & VERIFIED.

---

### 2.5. Assembly & Coordinate Frame Engine
* **Path:** [`packages/cadpy/src/cadpy/assembly.py`](file:///c:/Users/samyuktha/OneDrive/Documents/text-to-cad-main/packages/cadpy/src/cadpy/assembly.py)
* **Responsibility:** Defines mating coordinate frames, tab/slot alignment relations, and assembly hierarchy between structural components.
* **Major Classes:** `AssemblyHelper`, `MateRelation`, `MateTarget`.
* **Major Functions:** `add_rigid_frame()`, `add_joint_frame()`, `assembly_mate_payload()`.
* **Inputs:** Individual solid shapes and coordinate frames.
* **Outputs:** Mate constraints and hierarchy graph.
* **Dependencies:** `build123d`.
* **Current Status:** COMPLETE & VERIFIED.

---

### 2.6. Revision Management Engine
* **Path:** [`packages/cadpy/src/cadpy/revision.py`](file:///c:/Users/samyuktha/OneDrive/Documents/text-to-cad-main/packages/cadpy/src/cadpy/revision.py)
* **Responsibility:** Tracks specification changes, builds parameter dependency graphs, calculates downstream impact, invalidates stale artifacts, and preserves immutable revision history.
* **Major Classes:** `RequirementDiffEngine`, `DependencyGraph`, `ImpactAnalysisEngine`, `RevisionManifest`, `RequirementChange`.
* **Inputs:** Baseline `AircraftSpecification` and revised `AircraftSpecification`.
* **Outputs:** `ImpactResult` with invalidated artifact lists and revision manifest.
* **Dependencies:** Standard library.
* **Current Status:** COMPLETE & VERIFIED.

---

### 2.7. Engineering Review Engine
* **Path:** [`packages/cadpy/src/cadpy/review.py`](file:///c:/Users/samyuktha/OneDrive/Documents/text-to-cad-main/packages/cadpy/src/cadpy/review.py)
* **Responsibility:** Conducts formal automated checks for requirement compliance, dimensional tolerances, configuration matching, structural volume integrity, and manufacturing feasibility.
* **Major Classes:** `EngineeringReviewEngine`, `EngineeringReview`, `ComplianceItem`, `RequirementCoverageItem`.
* **Inputs:** `AircraftSpecification`, CAD results, structural results, manufacturing results.
* **Outputs:** `EngineeringReview` result object and `engineering_review.json`.
* **Dependencies:** `cadpy.requirements`, `cadpy.aircraft`, `cadpy.structure`, `cadpy.manufacturing`.
* **Current Status:** COMPLETE & VERIFIED.

---

### 2.8. Prototype Build Package Engine
* **Path:** [`packages/cadpy/src/cadpy/build_package.py`](file:///c:/Users/samyuktha/OneDrive/Documents/text-to-cad-main/packages/cadpy/src/cadpy/build_package.py)
* **Responsibility:** Compiles physical shop-floor prototype packages including itemized BOM, stock schedule, deterministic assembly sequence, and build instructions.
* **Major Classes:** `BuildPackageEngine`, `PrototypeBuildPackage`, `BuildPart`, `AssemblyStep`, `MaterialScheduleItem`.
* **Inputs:** Manufacturing results, assembly sequence, engineering review.
* **Outputs:** `build_instructions.md`, `build_manifest.json`, BOM tables.
* **Dependencies:** Standard library.
* **Current Status:** COMPLETE & VERIFIED.

---

### 2.9. 3D Build Visualization Engine
* **Path:** [`packages/cadpy/src/cadpy/build_visualization.py`](file:///c:/Users/samyuktha/OneDrive/Documents/text-to-cad-main/packages/cadpy/src/cadpy/build_visualization.py)
* **Responsibility:** Generates 3D multi-mode transformation packages for interactive web viewing (Nominal Assembled, Exploded View, Internal Structure, Process-Coded Manufacturing, Isolated Subassembly).
* **Major Classes:** `BuildVisualizationEngine`, `BuildVisualizationPackage`, `ViewerComponent`, `ViewerAssemblyStep`.
* **Inputs:** CAD geometry, structural metadata, manufacturing part classification.
* **Outputs:** `build_visualization.json` (consumed directly by `viewer/`).
* **Dependencies:** Standard library.
* **Current Status:** COMPLETE & VERIFIED.

---

### 2.10. Final Prototype Release Gate Engine
* **Path:** [`packages/cadpy/src/cadpy/release_gate.py`](file:///c:/Users/samyuktha/OneDrive/Documents/text-to-cad-main/packages/cadpy/src/cadpy/release_gate.py)
* **Responsibility:** Enforces cross-stage QA checks across all upstream phases before signing off on prototype release.
* **Major Classes:** `ReleaseGateEngine`, `ReleaseGateResult`, `PrototypeReleaseManifest`, `ReleaseGateCheckItem`.
* **Inputs:** Pipeline execution records, all generated artifacts, engineering review.
* **Outputs:** `release_manifest.json` with final release status (`RELEASE_READY`, `READY_WITH_WARNINGS`, `RELEASE_BLOCKED`).
* **Dependencies:** Standard library.
* **Current Status:** COMPLETE & VERIFIED.

---

### 2.11. End-to-End Pipeline Orchestrator
* **Path:** [`packages/cadpy/src/cadpy/pipeline.py`](file:///c:/Users/samyuktha/OneDrive/Documents/text-to-cad-main/packages/cadpy/src/cadpy/pipeline.py)
* **Responsibility:** Coordinates sequential execution across all 13 phases, manages shared pipeline context, registers artifacts, and handles error recovery.
* **Major Classes:** `DesignStudioPipeline`, `PipelineContext`, `ArtifactRegistry`, `ArtifactRecord`, `PipelinePhase`.
* **Inputs:** Input specification document, target output directory.
* **Outputs:** Fully populated prototype artifact directory (`models/<AIRCRAFT_ID>/v1/`).
* **Dependencies:** All `cadpy` modules.
* **Current Status:** COMPLETE & VERIFIED.

---

### 2.12. Frontend Web Application (CAD Viewer / Design Studio)
* **Path:** [`viewer/`](file:///c:/Users/samyuktha/OneDrive/Documents/text-to-cad-main/viewer/)
* **Responsibility:** Interactive web-based 3D model inspection, assembly tree exploration, exploded view controls, face/edge selection, and manufacturing review.
* **Tech Stack:** React 18, Vite, Three.js, `@torqwings/cadjs`, TailwindCSS / Vanilla CSS.
* **Inputs:** Generated STEP, GLB, DXF, and JSON manifests served via local filesystem backend (`/__cad/*` endpoints) or hosted blob storage.
* **Outputs:** Interactive browser rendering.
* **Current Status:** COMPLETE & VERIFIED.
