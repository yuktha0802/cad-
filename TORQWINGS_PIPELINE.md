# TorqWings CAD Studio — Complete Pipeline Specification

This document details the complete 13-stage automated execution pipeline of **TorqWings CAD Studio (Part 2: Engineering Specification → Prototype-Ready Aircraft CAD System)**.

---

## Pipeline Execution Overview

$$\begin{aligned}
\text{Part 1 Engineering Report} &\longrightarrow \text{Stage 1: Document Ingestion \& Parameter Extraction} \\
&\longrightarrow \text{Stage 2: Model Normalization \& Provenance Tracking} \\
&\longrightarrow \text{Stage 3: Aircraft Configuration Interpretation} \\
&\longrightarrow \text{Stage 4: Outer Mold Line (OML) CAD Solid Generation} \\
&\longrightarrow \text{Stage 5: Internal Structural Synthesis} \\
&\longrightarrow \text{Stage 6: Digital Manufacturing Decomposition} \\
&\longrightarrow \text{Stage 7: Assembly \& Joint Synthesis} \\
&\longrightarrow \text{Stage 8: Dimensional \& Geometric Validation} \\
&\longrightarrow \text{Stage 9: Differential Revision Management} \\
&\longrightarrow \text{Stage 10: Formal Engineering Review Engine} \\
&\longrightarrow \text{Stage 11: Prototype Build Package Compilation} \\
&\longrightarrow \text{Stage 12: 3D Multi-Mode Build Visualization} \\
&\longrightarrow \text{Stage 13: Final Prototype Release Gate QA} \\
&\longrightarrow \textbf{Complete Physical Prototype Package}
\end{aligned}$$

---

## Stage-by-Stage Specifications

### Stage 1: Document Ingestion & Parameter Extraction
* **Input:** Raw Part 1 Engineering Specification (JSON report, dictionary payload, Markdown engineering datasheet).
* **Process:** The ingestion parser (`requirements.py:parse_aircraft_specification`) scans the document text/structure, identifies engineering sections (Wing, Fuselage, Empennage, Propulsion, Mass Properties, Internal Equipment Bays, Mission Targets), and extracts raw numerical values and text tokens.
* **Output:** Intermediate parsed parameter dictionary with original string values, units, and document section references.
* **Validation:** JSON schema compliance and mandatory parameter existence checks.
* **Traceability:** Records source file name, section header, and original value/unit for every extracted parameter.

---

### Stage 2: Model Normalization & Provenance Tracking
* **Input:** Intermediate extracted parameter dictionary.
* **Process:** Standardizes units to canonical SI/engineering units ($m, cm, in \rightarrow mm$; $g, lb \rightarrow kg$; $rad \rightarrow deg$). Computes derived engineering parameters (wing aspect ratio, wing area, mean aerodynamic chord, tail volume ratios). Assigns status tags (`EXPLICIT`, `DERIVED`, `UNKNOWN`, `CONFLICT`).
* **Output:** Strongly-typed `AircraftSpecification` object containing typed sub-specifications (`WingSpec`, `FuselageSpec`, `TailSpec`, `PropulsionSpec`, `MassSpec`, `InternalBaysSpec`).
* **Validation:** Range sanity checks (e.g., span $> 0$, thickness ratios between $0.05$ and $0.30$). Contradiction scanning across multiple document sections.
* **Traceability:** Every parameter maintains an unbroken link to its origin in the Part 1 engineering report.

---

### Stage 3: Aircraft Configuration Interpretation
* **Input:** Normalized `AircraftSpecification`.
* **Process:** Resolves layout topology rules:
  * Wing placement (high-wing, mid-wing, low-wing).
  * Propulsion layout (tractor nose, pusher tail, twin-boom tractor/pusher).
  * Empennage type (conventional T-tail, cruciform, inverted V-tail, twin boom).
  * Internal bay allocation (relative CG-balanced placement of battery, avionics, payload).
* **Output:** Geometric configuration layout blueprint with global coordinate origins.
* **Validation:** Checks structural feasibility of layout (e.g., tractor engine does not collide with nose gear or avionics bay).
* **Traceability:** Configuration parameters mapped to source specification `spec.configuration.*`.

---

### Stage 4: Outer Mold Line (OML) CAD Solid Generation
* **Input:** Normalized `AircraftSpecification` and layout blueprint.
* **Process:** Executes B-Rep geometric modeling kernel (`aircraft.py`):
  * Generates airfoil coordinate points (NACA 4-digit analytical equations, Clark Y coordinate database).
  * Lofts wing surfaces with spanwise sweep, dihedral, taper, and geometric twist.
  * Constructs fuselage cross-sectional wire lofts and skins.
  * Generates horizontal and vertical stabilizers.
  * Models propulsion motor cowlings and propeller geometry.
  * Subtracts internal equipment clearance envelopes.
* **Output:** Watertight 3D solid compound (`build123d.Compound`), exported to ISO 10303 STEP (`.step`) and WebGL binary GLB (`.glb`).
* **Validation:** Manifold solid verification, non-zero volume checks, face/edge count assertions, bounding box measurement against specification ($\pm 1.0\text{ mm}$).
* **Traceability:** CAD solid names and face groups correspond to parameter keys (e.g., `MainWing`, `Fuselage`, `HorizontalTail`).

---

### Stage 5: Internal Structural Synthesis
* **Input:** OML CAD solids, material thickness parameters ($3.0\text{ mm}$ default), structural layout rules.
* **Process:** Synthesizes internal load-bearing skeleton (`structure.py`):
  * **Fuselage Structure:** Generates transverse bulkheads/formers along longitudinal stations; notches longitudinal longerons/stringers; constructs forward propulsion firewall.
  * **Wing Structure:** Generates main and rear shear-web spars; places chordwise airfoil ribs with spar slots and lightening cutouts.
  * **Empennage Structure:** Generates stabilizer spars and stabilizer ribs.
  * **Hardpoints:** Generates high-load central wing-fuselage attachment block.
* **Output:** Airframe structural compound containing $48$ individually identifiable solid bodies (for FW-007 baseline) and metadata registry.
* **Validation:** Asserts every structural component has positive non-zero volume ($100\%$ non-degenerate solids).
* **Traceability:** Every structural solid is labeled with a deterministic identifier (`FMR-001`, `RIB-L-003`, `SPAR-MAIN`).

---

### Stage 6: Digital Manufacturing Decomposition
* **Input:** Structural airframe solids compound and fabrication profiles.
* **Process:** Executes manufacturing classification and toolpath generation (`manufacturing.py`):
  * **Classification:** Classifies each solid as **Planar Sheet** (2.5D cutting) or **Volumetric Additive** (3D printing).
  * **Laser Flat Extraction:** Flattens 3D sheet solids into 2D cut profiles with kerf compensation ($0.1\text{ mm}$ offset).
  * **Sheet Nesting:** Nests 2D profiles onto standard $900 \times 600\text{ mm}$ balsa/aeroply sheets using 2D packing algorithms.
  * **3D Print Export:** Meshes complex attachment brackets to watertight STL.
* **Output:**
  * $47$ individual 2D part cut files (`.dxf`, `.svg`).
  * $3$ nested sheet layout files (`.dxf`, `.svg`).
  * $1$ 3D print file (`.stl`).
  * Itemized Manufacturing BOM (`manufacturing_bom.json`).
* **Validation:** Minimum cutting bridge width ($> 1.5\text{ mm}$), sheet boundary containment, 3D print bounding box envelope ($220 \times 220 \times 250\text{ mm}$).
* **Traceability:** 1:1 mapping between structural solid names and manufacturing part IDs.

---

### Stage 7: Assembly & Joint Synthesis
* **Input:** Structural components and manufacturing parts.
* **Process:** Synthesizes parametric tab-and-slot interlocking joints (`assembly.py`):
  * Generates male tabs and female slots at structural intersections (former-longeron, rib-spar).
  * Sets assembly clearance tolerances ($0.1\text{ mm}$).
  * Defines mating coordinate frames and assembly relationships (`MateRelation`).
* **Output:** $69$ interlocking joint mates and hierarchical assembly graph.
* **Validation:** Joint alignment check, slot depth matching, and mate orientation verification.
* **Traceability:** Joint IDs explicitly reference mated part IDs (`JNT_FMR_001_LONG-UPPER-L`).

---

### Stage 8: Dimensional & Geometric Validation
* **Input:** Generated CAD solid, structural model, and source `AircraftSpecification`.
* **Process:** Runs automated dimensional verification (`validators.py`):
  * Measures bounding box wingspan, fuselage length, horizontal tail span, vertical tail height.
  * Compares measured CAD dimensions against specified requirement values.
* **Output:** `validation_report.json` with numerical deviation table.
* **Validation:** Asserts deviations are within strict engineering tolerances ($\pm 1.0\text{ mm}$ for span/surfaces; $\pm 35.0\text{ mm}$ for multi-station fuselage lofts).
* **Traceability:** Each validation line points directly to the corresponding `spec.wing.span` or `spec.fuselage.length`.

---

### Stage 9: Differential Revision Management
* **Input:** Previous specification baseline vs. current incoming specification.
* **Process:** Compares parameters via `RequirementDiffEngine` (`revision.py`):
  * Detects modified, added, or deleted requirements.
  * Traverses `DependencyGraph` to identify affected downstream subsystems.
  * Selectively marks outdated CAD, structural, or laser sheet artifacts as `STALE`.
* **Output:** `revision_manifest.json` with change impact score and invalidation list.
* **Validation:** Asserts immutable revision versioning (`v1`, `v2`) without overwriting previous releases.
* **Traceability:** Revision history links each engineering change to the exact modified requirement.

---

### Stage 10: Formal Engineering Review Engine
* **Input:** Validated specification, CAD solid, structural airframe, manufacturing package, and mass properties.
* **Process:** Conducts comprehensive engineering review across 8 categories (`review.py`):
  * Requirement compliance, requirement coverage, geometry tolerances, configuration match, component existence, structural volume, manufacturing feasibility, and mass/CG review.
* **Output:** `engineering_review.json` with overall score (`PASS`, `PASS WITH WARNINGS`, `FAIL`).
* **Validation:** Evaluates all blocking checks; records non-blocking engineering warnings and unresolvable parameters.
* **Traceability:** Unbroken links to source requirements and generated components.

---

### Stage 11: Prototype Build Package Compilation
* **Input:** Manufacturing parts catalog, nested sheets, joint relationships, and engineering review.
* **Process:** Compiles shop-floor fabrication package (`build_package.py`):
  * Generates itemized Bill of Materials (BOM).
  * Generates raw material stock schedules (sheet counts, filament mass).
  * Generates step-by-step Standard Operating Procedures (SOP) for bench assembly.
* **Output:**
  * `build_instructions.md` (Human-readable shop assembly manual).
  * `build_manifest.json` (Machine-readable build inventory).
* **Validation:** Asserts zero orphan or duplicate part IDs; verifies all BOM items exist on physical cut sheets or print files.
* **Traceability:** Every instruction step explicitly lists component IDs and required joint interfaces.

---

### Stage 12: 3D Multi-Mode Build Visualization
* **Input:** CAD assembly solids, structural components, and manufacturing metadata.
* **Process:** Computes multi-state 3D coordinate transformations (`build_visualization.py`):
  * `ASSEMBLED`: Nominal flight configuration.
  * `EXPLODED`: Radial displacement along subassembly vectors for joint inspection.
  * `STRUCTURE`: X-ray skin revealing internal ribs, spars, and formers.
  * `MANUFACTURING`: Material process color-coding.
  * `PARTS`: Isolated individual part inspection.
  * `SUBASSEMBLY`: Isolated subassembly trees.
* **Output:** `build_visualization.json` (consumed by frontend `viewer/` and `cadjs`).
* **Validation:** Verified bounding transformations and matrix invertibility.
* **Traceability:** Visualization nodes reference canonical Part IDs.

---

### Stage 13: Final Prototype Release Gate QA
* **Input:** Execution records, generated artifacts, validation summaries, and engineering review from Stages 1–12.
* **Process:** Performs final cross-stage QA audit (`release_gate.py`):
  * Verifies existence and non-zero byte size of all required physical release files.
  * Asserts consistency between CAD dimensions, structural counts, manufacturing parts, and BOM.
  * Evaluates blocking failure criteria.
* **Output:** `release_manifest.json` with official release sign-off:
  * `RELEASE_READY` / `READY_WITH_WARNINGS` / `RELEASE_BLOCKED`.
* **Validation:** Gate blocks release if any critical engineering invariant fails.
* **Traceability:** Release manifest records cryptographic hashes, timestamps, and full cross-stage traceability summaries.
