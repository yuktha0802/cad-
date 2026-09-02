"""Phase 7 Design Studio End-to-End Pipeline Orchestration & Artifact Registry.

Orchestrates:
- Phase 3: Requirements Validation
- Phase 4: Parameterized Aircraft CAD
- Phase 5: Airframe Structural Synthesis
- Phase 6A: Manufacturing Data Model
- Phase 6B: Structural Classification
- Phase 6C: Fabrication Geometry & Joints
- Phase 6D: Laser DXF/SVG & Sheet Nesting
- Phase 6E: 3D-Print STL Export & Envelope Checks
- Phase 6F: Manufacturing Validation & Virtual Reassembly
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any

from cadpy.requirements import (
    AircraftSpecification,
    parse_aircraft_specification,
    validate_aircraft_specification,
)
from cadpy.aircraft import (
    CADGenerationResult,
    generate_aircraft_from_spec,
)
from cadpy.structure import (
    StructuralProfile,
)
from cadpy.manufacturing import (
    ManufacturingProcess,
    ManufacturingProfile,
    ManufacturingPart,
    ManufacturingJoint,
    FabricationGeometry,
    ManufacturingSheet,
    PrintablePart,
    PrintSplitRecord,
    ManufacturingBOM,
    VirtualManufacturingAssembly,
    ManufacturingValidationResult,
    ManufacturingClassifier,
    FabricationGeometryGenerator,
    KerfCompensator,
    SheetNester,
    PartSplitter,
    PrintablePartGenerator,
    ThreeDPrintExporter,
    ManufacturingValidationEngine,
    create_prototype_manufacturing_profile,
    get_prototype_laser_balsa_profile,
    get_prototype_3d_print_profile,
)
from cadpy.revision import (
    RequirementDiffEngine,
    ImpactAnalysisEngine,
    RevisionManifest,
    RequirementChange,
    ImpactResult,
)
from cadpy.review import (
    EngineeringReview,
    EngineeringReviewEngine,
    ReviewStatus,
    PrototypeReadiness,
)
from cadpy.build_package import (
    PrototypeBuildPackage,
    BuildPackageEngine,
    BuildReadiness,
)
from cadpy.build_visualization import (
    BuildVisualizationPackage,
    BuildVisualizationEngine,
    BuildProgressStatus,
    ViewMode,
)
from cadpy.release_gate import (
    ReleaseGateEngine,
    ReleaseGateResult,
    PrototypeReleaseManifest,
    ReleaseStatus,
)


class PipelinePhase(str, Enum):
    """All 9 traceable phases in the complete aircraft engineering pipeline."""
    PHASE_3_REQUIREMENTS = "PHASE_3_REQUIREMENTS"
    PHASE_4_CAD = "PHASE_4_CAD"
    PHASE_5_STRUCTURE = "PHASE_5_STRUCTURE"
    PHASE_6A_MANUFACTURING_MODEL = "PHASE_6A_MANUFACTURING_MODEL"
    PHASE_6B_CLASSIFICATION = "PHASE_6B_CLASSIFICATION"
    PHASE_6C_FABRICATION = "PHASE_6C_FABRICATION"
    PHASE_6D_LASER = "PHASE_6D_LASER"
    PHASE_6E_PRINT = "PHASE_6E_PRINT"
    PHASE_6F_VALIDATION = "PHASE_6F_VALIDATION"


class PhaseState(str, Enum):
    """Execution state for each phase in the pipeline."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    WARNING = "WARNING"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


class ExecutionMode(str, Enum):
    """Pipeline execution strategy."""
    FULL_PIPELINE = "FULL_PIPELINE"
    FROM_PHASE = "FROM_PHASE"


class ArtifactType(str, Enum):
    """Categories of versioned pipeline artifacts."""
    SPECIFICATION = "SPECIFICATION"
    CAD_STEP = "CAD_STEP"
    STRUCTURAL_STEP = "STRUCTURAL_STEP"
    MANUFACTURING_MANIFEST = "MANUFACTURING_MANIFEST"
    DXF = "DXF"
    SVG = "SVG"
    STL = "STL"
    THREE_MF = "THREE_MF"
    VALIDATION_REPORT = "VALIDATION_REPORT"
    BOM = "BOM"
    SHEET_LAYOUT = "SHEET_LAYOUT"


@dataclass
class PhaseExecutionRecord:
    """Deterministic record of an individual phase execution."""
    phase: str
    state: str = PhaseState.PENDING.value
    progress: float = 0.0  # 0.0 to 1.0
    duration_sec: float = 0.0
    message: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    artifact_ids: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ArtifactRecord:
    """Versioned, traceable artifact entry in the registry."""
    artifact_id: str
    artifact_type: str
    file_path: str
    phase: str
    source_version: str
    created_from_component: str = ""
    status: str = "VALID"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ArtifactRegistry:
    """Central registry tracking all artifacts produced during pipeline execution."""
    project_id: str
    aircraft_id: str
    version: str
    artifacts: dict[str, ArtifactRecord] = field(default_factory=dict)

    def register_artifact(
        self,
        artifact_id: str,
        artifact_type: str,
        file_path: Path | str,
        phase: str,
        created_from_component: str = "",
        metadata: dict[str, Any] | None = None
    ) -> ArtifactRecord:
        """Register a new output artifact."""
        rec = ArtifactRecord(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            file_path=str(file_path),
            phase=phase,
            source_version=self.version,
            created_from_component=created_from_component,
            metadata=metadata or {}
        )
        self.artifacts[artifact_id] = rec
        return rec

    def get_artifact(self, artifact_id: str) -> ArtifactRecord | None:
        """Retrieve an artifact by ID."""
        return self.artifacts.get(artifact_id)

    def get_by_phase(self, phase: str) -> list[ArtifactRecord]:
        """Retrieve all artifacts produced by a given phase."""
        return [a for a in self.artifacts.values() if a.phase == phase]

    def get_by_type(self, artifact_type: str) -> list[ArtifactRecord]:
        """Retrieve all artifacts of a given type."""
        return [a for a in self.artifacts.values() if a.artifact_type == artifact_type]

    def query_traceability(self, output_artifact_id: str) -> dict[str, Any]:
        """Trace an output artifact back to its fabrication geometry, structural component, CAD, and requirement."""
        art = self.artifacts.get(output_artifact_id)
        if not art:
            return {"error": f"Artifact {output_artifact_id} not found"}
        
        return {
            "artifact_id": art.artifact_id,
            "artifact_type": art.artifact_type,
            "file_path": art.file_path,
            "phase": art.phase,
            "version": art.source_version,
            "created_from_component": art.created_from_component,
            "provenance": art.metadata.get("provenance", {})
        }


@dataclass
class DesignVersion:
    """Immutable design version definition."""
    version_id: str  # e.g., "v1", "v2"
    aircraft_id: str
    specification_hash: str
    manufacturing_profile_name: str
    pipeline_version: str = "1.0.0"
    created_timestamp: float = field(default_factory=time.time)
    output_dir: str = ""
    status: str = "PENDING"


@dataclass
class PipelineContext:
    """Complete context passed across all phases of pipeline execution."""
    project_id: str
    aircraft_id: str
    version: str = "v1"
    parent_version: str = ""
    specification_path: str = ""
    raw_specification_text: str = ""
    parent_specification_text: str = ""
    parsed_spec: AircraftSpecification | None = None
    manufacturing_profile: ManufacturingProfile | None = None
    cad_result: CADGenerationResult | None = None
    structural_components: list[Any] = field(default_factory=list)
    structural_assembly: Any = None
    manufacturing_parts: list[ManufacturingPart] = field(default_factory=list)
    fabrication_geometries: list[FabricationGeometry] = field(default_factory=list)
    joints: list[ManufacturingJoint] = field(default_factory=list)
    laser_sheets: list[ManufacturingSheet] = field(default_factory=list)
    printable_parts: list[PrintablePart] = field(default_factory=list)
    split_records: list[PrintSplitRecord] = field(default_factory=list)
    bom: ManufacturingBOM | None = None
    validation_result: ManufacturingValidationResult | None = None
    artifact_registry: ArtifactRegistry | None = None
    phase_records: dict[str, PhaseExecutionRecord] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    revision_manifest: RevisionManifest | None = None
    engineering_review: EngineeringReview | None = None
    build_package: PrototypeBuildPackage | None = None
    build_visualization: BuildVisualizationPackage | None = None
    release_gate: ReleaseGateResult | None = None
    fingerprint: str = ""
    is_cancelled: bool = False


class DesignStudioPipeline:
    """Central orchestrator for the Part 1 -> Part 2 engineering and manufacturing pipeline."""

    PIPELINE_VERSION = "1.0.0"

    PHASE_SEQUENCE = [
        PipelinePhase.PHASE_3_REQUIREMENTS,
        PipelinePhase.PHASE_4_CAD,
        PipelinePhase.PHASE_5_STRUCTURE,
        PipelinePhase.PHASE_6A_MANUFACTURING_MODEL,
        PipelinePhase.PHASE_6B_CLASSIFICATION,
        PipelinePhase.PHASE_6C_FABRICATION,
        PipelinePhase.PHASE_6D_LASER,
        PipelinePhase.PHASE_6E_PRINT,
        PipelinePhase.PHASE_6F_VALIDATION,
    ]

    PHASE_DEPENDENCIES = {
        PipelinePhase.PHASE_3_REQUIREMENTS: [],
        PipelinePhase.PHASE_4_CAD: [PipelinePhase.PHASE_3_REQUIREMENTS],
        PipelinePhase.PHASE_5_STRUCTURE: [PipelinePhase.PHASE_4_CAD],
        PipelinePhase.PHASE_6A_MANUFACTURING_MODEL: [PipelinePhase.PHASE_3_REQUIREMENTS],
        PipelinePhase.PHASE_6B_CLASSIFICATION: [PipelinePhase.PHASE_6A_MANUFACTURING_MODEL, PipelinePhase.PHASE_5_STRUCTURE],
        PipelinePhase.PHASE_6C_FABRICATION: [PipelinePhase.PHASE_6B_CLASSIFICATION],
        PipelinePhase.PHASE_6D_LASER: [PipelinePhase.PHASE_6C_FABRICATION],
        PipelinePhase.PHASE_6E_PRINT: [PipelinePhase.PHASE_6C_FABRICATION, PipelinePhase.PHASE_6B_CLASSIFICATION],
        PipelinePhase.PHASE_6F_VALIDATION: [PipelinePhase.PHASE_6D_LASER, PipelinePhase.PHASE_6E_PRINT],
    }

    @classmethod
    def compute_fingerprint(cls, spec_text: str, profile: ManufacturingProfile) -> str:
        """Compute deterministic input fingerprint for caching and invalidation."""
        hasher = hashlib.sha256()
        hasher.update(spec_text.strip().encode("utf-8"))
        hasher.update(profile.name.encode("utf-8"))
        hasher.update(str(profile.laser_cut.kerf if profile.laser_cut else 0.15).encode("utf-8"))
        hasher.update(str(profile.three_d_print.printer_bed_x if profile.three_d_print else 220.0).encode("utf-8"))
        hasher.update(cls.PIPELINE_VERSION.encode("utf-8"))
        return hasher.hexdigest()

    @classmethod
    def execute(
        cls,
        part1_input: str | Path,
        aircraft_id: str = "FW-007",
        project_id: str = "DEFAULT_PROJECT",
        version: str = "v1",
        parent_version: str = "",
        parent_spec_text: str = "",
        profile: ManufacturingProfile | None = None,
        output_base_dir: str | Path = "outputs",
        from_phase: PipelinePhase | None = None,
        cached_context: PipelineContext | None = None
    ) -> PipelineContext:
        """Execute the complete Design Studio pipeline end-to-end with traceability, versioning, and validation."""
        start_time = time.time()
        
        # 1. Resolve Part 1 Input text
        if isinstance(part1_input, (str, Path)) and os.path.exists(str(part1_input)):
            spec_path = str(part1_input)
            spec_text = Path(part1_input).read_text(encoding="utf-8")
        else:
            spec_path = "IN_MEMORY"
            spec_text = str(part1_input)

        if not profile:
            profile = create_prototype_manufacturing_profile(f"{aircraft_id}_Production_Profile")

        fingerprint = cls.compute_fingerprint(spec_text, profile)

        # 2. Setup Versioned Directory Structure
        versioned_out = Path(output_base_dir) / aircraft_id / version
        versioned_out.mkdir(parents=True, exist_ok=True)

        # 3. Setup or Resume Pipeline Context
        if cached_context and cached_context.fingerprint == fingerprint and from_phase:
            ctx = cached_context
            ctx.version = version
            ctx.parent_version = parent_version
            ctx.parent_specification_text = parent_spec_text
        else:
            registry = ArtifactRegistry(project_id=project_id, aircraft_id=aircraft_id, version=version)
            ctx = PipelineContext(
                project_id=project_id,
                aircraft_id=aircraft_id,
                version=version,
                parent_version=parent_version,
                specification_path=spec_path,
                raw_specification_text=spec_text,
                parent_specification_text=parent_spec_text,
                manufacturing_profile=profile,
                artifact_registry=registry,
                fingerprint=fingerprint
            )
            for p in cls.PHASE_SEQUENCE:
                ctx.phase_records[p.value] = PhaseExecutionRecord(phase=p.value, state=PhaseState.PENDING.value)

        # Save Specification Artifact
        spec_artifact_path = versioned_out / "specification.md"
        spec_artifact_path.write_text(spec_text, encoding="utf-8")
        ctx.artifact_registry.register_artifact(
            artifact_id=f"{aircraft_id}_{version}_SPEC",
            artifact_type=ArtifactType.SPECIFICATION.value,
            file_path=spec_artifact_path,
            phase=PipelinePhase.PHASE_3_REQUIREMENTS.value,
            metadata={"source": spec_path, "fingerprint": fingerprint}
        )

        # 4. Execute Phases with Dependency Resolution
        should_run = (from_phase is None)

        for phase in cls.PHASE_SEQUENCE:
            if not should_run:
                if phase == from_phase:
                    should_run = True
                else:
                    continue

            # Check dependencies
            deps = cls.PHASE_DEPENDENCIES[phase]
            failed_deps = [d for d in deps if ctx.phase_records[d.value].state in {PhaseState.FAILED.value, PhaseState.SKIPPED.value, PhaseState.CANCELLED.value}]
            if failed_deps:
                rec = ctx.phase_records[phase.value]
                rec.state = PhaseState.SKIPPED.value
                rec.message = f"Skipped due to failed/skipped upstream dependencies: {[d.value for d in failed_deps]}"
                continue

            rec = ctx.phase_records[phase.value]
            rec.state = PhaseState.RUNNING.value
            p_start = time.time()

            try:
                if phase == PipelinePhase.PHASE_3_REQUIREMENTS:
                    cls._run_phase_3(ctx, versioned_out)
                elif phase == PipelinePhase.PHASE_4_CAD:
                    cls._run_phase_4(ctx, versioned_out)
                elif phase == PipelinePhase.PHASE_5_STRUCTURE:
                    cls._run_phase_5(ctx, versioned_out)
                elif phase == PipelinePhase.PHASE_6A_MANUFACTURING_MODEL:
                    cls._run_phase_6a(ctx, versioned_out)
                elif phase == PipelinePhase.PHASE_6B_CLASSIFICATION:
                    cls._run_phase_6b(ctx, versioned_out)
                elif phase == PipelinePhase.PHASE_6C_FABRICATION:
                    cls._run_phase_6c(ctx, versioned_out)
                elif phase == PipelinePhase.PHASE_6D_LASER:
                    cls._run_phase_6d(ctx, versioned_out)
                elif phase == PipelinePhase.PHASE_6E_PRINT:
                    cls._run_phase_6e(ctx, versioned_out)
                elif phase == PipelinePhase.PHASE_6F_VALIDATION:
                    cls._run_phase_6f(ctx, versioned_out)

                rec.duration_sec = round(time.time() - p_start, 3)
                rec.progress = 1.0
                if rec.errors:
                    rec.state = PhaseState.FAILED.value
                elif rec.warnings:
                    rec.state = PhaseState.WARNING.value
                else:
                    rec.state = PhaseState.PASSED.value

            except Exception as e:
                rec.duration_sec = round(time.time() - p_start, 3)
                rec.state = PhaseState.FAILED.value
                rec.errors.append(str(e))
                ctx.errors.append(f"{phase.value} execution failed: {str(e)}")

        # 5. Write Execution Summary & Manifest
        cls._write_pipeline_manifest(ctx, versioned_out, time.time() - start_time)

        return ctx

    @classmethod
    def _run_phase_3(cls, ctx: PipelineContext, out_dir: Path):
        rec = ctx.phase_records[PipelinePhase.PHASE_3_REQUIREMENTS.value]
        spec = parse_aircraft_specification(ctx.raw_specification_text, source_name=ctx.aircraft_id)
        ctx.parsed_spec = spec
        val_errors = validate_aircraft_specification(spec)

        for w in spec.conflicts:
            rec.warnings.append(w)
            ctx.warnings.append(w)

        if val_errors:
            for err in val_errors:
                rec.errors.append(err)
                ctx.errors.append(err)
            rec.message = f"Phase 3 validation failed with {len(val_errors)} blocking errors"
        else:
            rec.message = f"Phase 3 parsed and validated specification for '{ctx.aircraft_id}' successfully"

    @classmethod
    def _run_phase_4(cls, ctx: PipelineContext, out_dir: Path):
        rec = ctx.phase_records[PipelinePhase.PHASE_4_CAD.value]
        cad_dir = out_dir / "cad"
        cad_dir.mkdir(parents=True, exist_ok=True)
        step_path = cad_dir / f"{ctx.aircraft_id}_complete_aircraft.step"

        res = generate_aircraft_from_spec(ctx.parsed_spec)
        ctx.cad_result = res

        from build123d import export_step
        if res.assembly:
            export_step(res.assembly, str(step_path))
        
        params = res.manifest.get("parameters", {}) if isinstance(res.manifest, dict) else {}
        span_val = params.get("wing_span", {}).get("value", 2000.0)
        fuse_val = params.get("fuselage_length", {}).get("value", 1500.0)

        if step_path.exists():
            art = ctx.artifact_registry.register_artifact(
                artifact_id=f"{ctx.aircraft_id}_{ctx.version}_CAD_STEP",
                artifact_type=ArtifactType.CAD_STEP.value,
                file_path=step_path,
                phase=PipelinePhase.PHASE_4_CAD.value,
                created_from_component="AIRCRAFT_ASSEMBLY",
                metadata={"wingspan": span_val, "fuselage_length": fuse_val}
            )
            rec.artifact_ids.append(art.artifact_id)

        rec.message = f"Phase 4 generated parameterized CAD with {len(res.structural_components)} components"

    @classmethod
    def _run_phase_5(cls, ctx: PipelineContext, out_dir: Path):
        rec = ctx.phase_records[PipelinePhase.PHASE_5_STRUCTURE.value]
        struct_dir = out_dir / "structure"
        struct_dir.mkdir(parents=True, exist_ok=True)
        step_path = struct_dir / f"{ctx.aircraft_id}_structural_airframe.step"

        ctx.structural_components = ctx.cad_result.structural_components
        ctx.structural_assembly = ctx.cad_result.assembly

        if hasattr(ctx.cad_result, "export_step") and step_path:
            # Save structural step
            art = ctx.artifact_registry.register_artifact(
                artifact_id=f"{ctx.aircraft_id}_{ctx.version}_STRUCT_STEP",
                artifact_type=ArtifactType.STRUCTURAL_STEP.value,
                file_path=step_path,
                phase=PipelinePhase.PHASE_5_STRUCTURE.value,
                created_from_component="STRUCTURAL_ASSEMBLY",
                metadata={"component_count": len(ctx.structural_components)}
            )
            rec.artifact_ids.append(art.artifact_id)

        rec.message = f"Phase 5 synthesized airframe with {len(ctx.structural_components)} structural solids"

    @classmethod
    def _run_phase_6a(cls, ctx: PipelineContext, out_dir: Path):
        rec = ctx.phase_records[PipelinePhase.PHASE_6A_MANUFACTURING_MODEL.value]
        rec.message = f"Phase 6A initialized manufacturing profile '{ctx.manufacturing_profile.name}' with {len(ctx.manufacturing_profile.materials)} materials"

    @classmethod
    def _run_phase_6b(cls, ctx: PipelineContext, out_dir: Path):
        rec = ctx.phase_records[PipelinePhase.PHASE_6B_CLASSIFICATION.value]
        classifier = ManufacturingClassifier(ctx.manufacturing_profile)
        parts = classifier.classify_structural_assembly(ctx.structural_components)
        ctx.manufacturing_parts = parts
        rec.message = f"Phase 6B classified {len(parts)} parts ({sum(1 for p in parts if p.manufacturing_process == ManufacturingProcess.LASER_CUT)} laser, {sum(1 for p in parts if p.manufacturing_process == ManufacturingProcess.THREE_D_PRINT)} 3D-print)"

    @classmethod
    def _run_phase_6c(cls, ctx: PipelineContext, out_dir: Path):
        rec = ctx.phase_records[PipelinePhase.PHASE_6C_FABRICATION.value]
        generator = FabricationGeometryGenerator(ctx.manufacturing_profile)
        geoms, joints = generator.generate_fabrication_geometries(ctx.manufacturing_parts, ctx.structural_components)
        ctx.fabrication_geometries = geoms
        ctx.joints = joints
        rec.message = f"Phase 6C generated {len(geoms)} fabrication geometries and {len(joints)} tab/slot joints"

    @classmethod
    def _run_phase_6d(cls, ctx: PipelineContext, out_dir: Path):
        rec = ctx.phase_records[PipelinePhase.PHASE_6D_LASER.value]
        laser_dir = out_dir / "laser"
        parts_dir = laser_dir / "parts"
        sheets_dir = laser_dir / "sheets"
        parts_dir.mkdir(parents=True, exist_ok=True)
        sheets_dir.mkdir(parents=True, exist_ok=True)

        nester = SheetNester(ctx.manufacturing_profile.laser_cut or get_prototype_laser_balsa_profile())
        sheets = nester.nest_parts(ctx.manufacturing_parts, ctx.fabrication_geometries)
        ctx.laser_sheets = sheets

        # Export DXFs and register artifacts
        from cadpy.manufacturing import export_part_dxf, export_part_svg, export_sheet_dxf, export_sheet_svg
        for g in ctx.fabrication_geometries:
            p = next(x for x in ctx.manufacturing_parts if x.part_id == g.part_id)
            if p.manufacturing_process == ManufacturingProcess.LASER_CUT:
                dxf_path = parts_dir / f"{p.part_id}.dxf"
                svg_path = parts_dir / f"{p.part_id}.svg"
                export_part_dxf(g.part_id, g.boundary_2d, dxf_path)
                export_part_svg(g.part_id, g.boundary_2d, svg_path)
                art_dxf = ctx.artifact_registry.register_artifact(
                    artifact_id=f"{ctx.aircraft_id}_{ctx.version}_DXF_{p.part_id}",
                    artifact_type=ArtifactType.DXF.value,
                    file_path=dxf_path,
                    phase=PipelinePhase.PHASE_6D_LASER.value,
                    created_from_component=p.source_structural_component_id,
                    metadata={"provenance": {"requirement": p.component_type, "material": str(p.material)}}
                )
                rec.artifact_ids.append(art_dxf.artifact_id)

        for s in sheets:
            s_dxf = sheets_dir / f"{s.sheet_id}.dxf"
            s_svg = sheets_dir / f"{s.sheet_id}.svg"
            export_sheet_dxf(s, s_dxf)
            export_sheet_svg(s, s_svg)
            art_s = ctx.artifact_registry.register_artifact(
                artifact_id=f"{ctx.aircraft_id}_{ctx.version}_SHEET_{s.sheet_id}",
                artifact_type=ArtifactType.SHEET_LAYOUT.value,
                file_path=s_dxf,
                phase=PipelinePhase.PHASE_6D_LASER.value,
                metadata={"placed_parts": len(s.parts), "utilization": s.utilization}
            )
            rec.artifact_ids.append(art_s.artifact_id)

        rec.message = f"Phase 6D generated DXF/SVGs across {len(sheets)} nested stock sheets"

    @classmethod
    def _run_phase_6e(cls, ctx: PipelineContext, out_dir: Path):
        rec = ctx.phase_records[PipelinePhase.PHASE_6E_PRINT.value]
        print_dir = out_dir / "print"
        print_dir.mkdir(parents=True, exist_ok=True)

        p_gen = PrintablePartGenerator(ctx.manufacturing_profile)
        p_parts, splits = p_gen.generate_printable_parts(ctx.manufacturing_parts, ctx.fabrication_geometries, ctx.structural_components)
        ctx.printable_parts = p_parts
        ctx.split_records = splits

        for p in p_parts:
            stl_path = print_dir / f"{p.print_part_id}.stl"
            ThreeDPrintExporter.export_stl(p, stl_path)
            art = ctx.artifact_registry.register_artifact(
                artifact_id=f"{ctx.aircraft_id}_{ctx.version}_STL_{p.print_part_id}",
                artifact_type=ArtifactType.STL.value,
                file_path=stl_path,
                phase=PipelinePhase.PHASE_6E_PRINT.value,
                created_from_component=p.source_structural_component_id,
                metadata={"dimensions": p.print_dimensions, "material": p.material}
            )
            rec.artifact_ids.append(art.artifact_id)

        rec.message = f"Phase 6E exported {len(p_parts)} 3D-printable STLs with {len(splits)} envelope splits"

    @classmethod
    def _run_phase_6f(cls, ctx: PipelineContext, out_dir: Path):
        rec = ctx.phase_records[PipelinePhase.PHASE_6F_VALIDATION.value]
        val_dir = out_dir / "validation"
        val_dir.mkdir(parents=True, exist_ok=True)

        val_res = ManufacturingValidationEngine.run_full_validation(
            aircraft_id=ctx.aircraft_id,
            profile=ctx.manufacturing_profile,
            structural_components=ctx.structural_components,
            structural_assembly=ctx.structural_assembly,
            spec=ctx.parsed_spec,
            output_dir=val_dir
        )
        ctx.validation_result = val_res
        ctx.bom = val_res.bom

        # Register BOM and Validation Report artifacts
        val_json = val_dir / f"{ctx.aircraft_id}_manufacturing" / "manufacturing_validation.json"
        if val_json.exists():
            art_val = ctx.artifact_registry.register_artifact(
                artifact_id=f"{ctx.aircraft_id}_{ctx.version}_VAL_REPORT",
                artifact_type=ArtifactType.VALIDATION_REPORT.value,
                file_path=val_json,
                phase=PipelinePhase.PHASE_6F_VALIDATION.value,
                metadata={"overall_status": val_res.overall_status, "prototype_readiness": val_res.prototype_readiness}
            )
            rec.artifact_ids.append(art_val.artifact_id)

        rec.message = f"Phase 6F complete: {val_res.overall_status} (Prototype Readiness: {val_res.prototype_readiness})"
        if val_res.overall_status == "FAIL":
            for e in val_res.errors:
                rec.errors.append(e)

    @classmethod
    def _write_pipeline_manifest(cls, ctx: PipelineContext, out_dir: Path, total_duration: float):
        """Write machine-readable pipeline execution summary."""
        manifest = {
            "project_id": ctx.project_id,
            "aircraft_id": ctx.aircraft_id,
            "version": ctx.version,
            "pipeline_version": cls.PIPELINE_VERSION,
            "fingerprint": ctx.fingerprint,
            "total_duration_sec": round(total_duration, 3),
            "status": "PASS" if not ctx.errors else "FAIL",
            "prototype_readiness": ctx.validation_result.prototype_readiness if ctx.validation_result else "NOT_READY",
            "phases": {
                p: {
                    "state": rec.state,
                    "progress": rec.progress,
                    "duration_sec": rec.duration_sec,
                    "message": rec.message,
                    "errors": rec.errors,
                    "warnings": rec.warnings,
                    "artifacts": rec.artifact_ids,
                }
                for p, rec in ctx.phase_records.items()
            },
            "artifacts_count": len(ctx.artifact_registry.artifacts),
            "bom_summary": {
                "total_parts": ctx.bom.total_parts if ctx.bom else 0,
                "laser_cut": ctx.bom.laser_cut_count if ctx.bom else 0,
                "three_d_print": ctx.bom.three_d_print_count if ctx.bom else 0,
                "total_joints": ctx.bom.total_joints if ctx.bom else 0,
                "total_sheets": ctx.bom.total_sheets if ctx.bom else 0,
                "estimated_total_mass_g": ctx.bom.estimated_total_mass_g if ctx.bom else None,
            },
            "validation_summary": {
                "overall_status": ctx.validation_result.overall_status if ctx.validation_result else "NOT_RUN",
                "prototype_readiness": ctx.validation_result.prototype_readiness if ctx.validation_result else "NOT_READY",
                "gates": {
                    "completeness": ctx.validation_result.completeness_status if ctx.validation_result else "NOT_RUN",
                    "traceability": ctx.validation_result.traceability_status if ctx.validation_result else "NOT_RUN",
                    "laser": ctx.validation_result.laser_status if ctx.validation_result else "NOT_RUN",
                    "printing": ctx.validation_result.printing_status if ctx.validation_result else "NOT_RUN",
                    "joints": ctx.validation_result.joints_status if ctx.validation_result else "NOT_RUN",
                    "dimensions": ctx.validation_result.dimensions_status if ctx.validation_result else "NOT_RUN",
                    "symmetry": ctx.validation_result.symmetry_status if ctx.validation_result else "NOT_RUN",
                    "bays": ctx.validation_result.bays_status if ctx.validation_result else "NOT_RUN",
                    "propulsion": ctx.validation_result.propulsion_status if ctx.validation_result else "NOT_RUN",
                    "reassembly": ctx.validation_result.reassembly_status if ctx.validation_result else "NOT_RUN",
                } if ctx.validation_result else {},
            }
        }

        # Check for Revision Manifest if parent_version is specified or parent spec exists
        parent_spec = None
        if ctx.parent_specification_text:
            try:
                parent_spec = parse_aircraft_specification(ctx.parent_specification_text, source_name=f"{ctx.aircraft_id}_{ctx.parent_version}")
            except Exception:
                pass
        elif ctx.parent_version:
            parent_dir = out_dir.parent / ctx.parent_version
            parent_spec_file = parent_dir / "specification.md"
            if parent_spec_file.exists():
                try:
                    parent_text = parent_spec_file.read_text(encoding="utf-8")
                    parent_spec = parse_aircraft_specification(parent_text, source_name=f"{ctx.aircraft_id}_{ctx.parent_version}")
                except Exception:
                    pass

        if parent_spec and ctx.parsed_spec:
            changes = RequirementDiffEngine.compare_specifications(parent_spec, ctx.parsed_spec)
            impact = ImpactAnalysisEngine.analyze_impact(changes)

            rev_manifest = RevisionManifest(
                aircraft_id=ctx.aircraft_id,
                version=ctx.version,
                parent_version=ctx.parent_version,
                changes=[c.to_dict() for c in changes],
                impact_summary=impact.summary,
                affected_components_count=impact.summary.get("total_cad_affected", 0) + impact.summary.get("total_structural_affected", 0),
                unaffected_components_count=len(impact.unaffected_components),
                selective_regeneration_used=impact.can_selectively_regenerate,
                created_artifacts=[a.artifact_id for a in ctx.artifact_registry.artifacts.values()],
                pipeline_status="PASS" if not ctx.errors else "FAIL",
                validation_status=ctx.validation_result.overall_status if ctx.validation_result else "NOT_RUN",
                prototype_readiness=ctx.validation_result.prototype_readiness if ctx.validation_result else "NOT_READY"
            )
            ctx.revision_manifest = rev_manifest

            rev_path = out_dir / "revision_manifest.json"
            rev_path.write_text(json.dumps(rev_manifest.to_dict(), indent=2), encoding="utf-8")

            ctx.artifact_registry.register_artifact(
                artifact_id=f"{ctx.aircraft_id}_{ctx.version}_REVISION_MANIFEST",
                artifact_type="REVISION_MANIFEST",
                file_path=rev_path,
                phase=PipelinePhase.PHASE_3_REQUIREMENTS.value,
                metadata={"parent_version": ctx.parent_version, "changes_count": len(changes)}
            )

            manifest["revision_summary"] = rev_manifest.to_dict()

        # Execute Phase 10 Engineering Review
        review = EngineeringReviewEngine.execute_review(
            aircraft_id=ctx.aircraft_id,
            version=ctx.version,
            spec=ctx.parsed_spec,
            cad_result=ctx.cad_result,
            structural_components=ctx.structural_components,
            manufacturing_parts=ctx.manufacturing_parts,
            validation_result=ctx.validation_result,
            bom=ctx.bom
        )
        ctx.engineering_review = review

        review_path = out_dir / "engineering_review.json"
        review_path.write_text(json.dumps(review.to_dict(), indent=2), encoding="utf-8")

        ctx.artifact_registry.register_artifact(
            artifact_id=f"{ctx.aircraft_id}_{ctx.version}_ENG_REVIEW",
            artifact_type="ENGINEERING_REVIEW",
            file_path=review_path,
            phase=PipelinePhase.PHASE_6F_VALIDATION.value,
            metadata={"overall_status": review.overall_status, "prototype_status": review.prototype_status}
        )

        manifest["engineering_review_summary"] = {
            "overall_status": review.overall_status,
            "prototype_status": review.prototype_status,
            "warnings_count": len(review.warnings),
            "conflicts_count": len(review.conflicts),
            "blocking_failures_count": len(review.blocking_failures),
            "summary": review.summary,
        }

        # Execute Phase 11 Prototype Build Package Generation
        build_pkg = BuildPackageEngine.generate_build_package(
            aircraft_id=ctx.aircraft_id,
            version=ctx.version,
            spec=ctx.parsed_spec,
            manufacturing_parts=ctx.manufacturing_parts,
            joints=ctx.joints,
            nested_sheets=ctx.laser_sheets,
            printable_parts=ctx.printable_parts,
            validation_result=ctx.validation_result,
            engineering_review=review,
            output_dir=out_dir
        )
        ctx.build_package = build_pkg

        ctx.artifact_registry.register_artifact(
            artifact_id=f"{ctx.aircraft_id}_{ctx.version}_BUILD_PACKAGE",
            artifact_type="PROTOTYPE_BUILD_PACKAGE",
            file_path=out_dir / "build_manifest.json",
            phase=PipelinePhase.PHASE_6F_VALIDATION.value,
            metadata={
                "prototype_readiness": build_pkg.prototype_readiness,
                "parts_count": len(build_pkg.parts),
                "laser_sheets_count": len(build_pkg.laser_sheets),
            }
        )

        manifest["build_package_summary"] = {
            "prototype_readiness": build_pkg.prototype_readiness,
            "parts_count": len(build_pkg.parts),
            "laser_parts_count": sum(1 for p in build_pkg.parts if p.manufacturing_process == "LASER_CUT"),
            "printable_parts_count": sum(1 for p in build_pkg.parts if p.manufacturing_process == "THREE_D_PRINT"),
            "joints_count": len(build_pkg.joints),
            "sheets_count": len(build_pkg.laser_sheets),
            "assembly_steps_count": len(build_pkg.assembly_steps),
            "summary": build_pkg.summary,
        }

        # Execute Phase 12 3D Build Visualization Package Generation
        vis_pkg = BuildVisualizationEngine.generate_visualization_package(
            aircraft_id=ctx.aircraft_id,
            version=ctx.version,
            spec=ctx.parsed_spec,
            build_package=build_pkg,
            structural_components=ctx.structural_components,
            manufacturing_parts=ctx.manufacturing_parts,
            joints=ctx.joints,
            nested_sheets=ctx.laser_sheets,
            printable_parts=ctx.printable_parts,
            engineering_review=review,
            parent_version=ctx.parent_version if ctx.parent_version else None,
            output_dir=out_dir
        )
        ctx.build_visualization = vis_pkg

        ctx.artifact_registry.register_artifact(
            artifact_id=f"{ctx.aircraft_id}_{ctx.version}_BUILD_VISUALIZATION",
            artifact_type="BUILD_VISUALIZATION_PACKAGE",
            file_path=out_dir / "visualization" / "build_visualization.json",
            phase=PipelinePhase.PHASE_6F_VALIDATION.value,
            metadata={
                "view_modes_count": len(vis_pkg.view_modes),
                "components_count": len(vis_pkg.components),
                "steps_count": len(vis_pkg.steps),
                "joints_count": len(vis_pkg.joints),
            }
        )

        manifest["build_visualization_summary"] = {
            "components_count": len(vis_pkg.components),
            "laser_parts_count": vis_pkg.summary.get("laser_parts_count", 0),
            "printable_parts_count": vis_pkg.summary.get("printable_parts_count", 0),
            "steps_count": len(vis_pkg.steps),
            "joints_count": len(vis_pkg.joints),
            "sheets_count": len(vis_pkg.sheets),
            "view_modes": vis_pkg.view_modes,
            "build_progress": vis_pkg.build_progress,
            "summary": vis_pkg.summary,
        }

        # Execute Phase 13 Final Prototype Release Gate
        rel_res = ReleaseGateEngine.evaluate_release(
            aircraft_id=ctx.aircraft_id,
            version=ctx.version,
            spec=ctx.parsed_spec,
            cad_result=ctx.cad_result,
            structural_components=ctx.structural_components,
            manufacturing_parts=ctx.manufacturing_parts,
            validation_result=ctx.validation_result,
            engineering_review=review,
            build_package=build_pkg,
            build_visualization=vis_pkg,
            output_dir=out_dir,
            parent_version=ctx.parent_version if ctx.parent_version else None
        )
        ctx.release_gate = rel_res

        ctx.artifact_registry.register_artifact(
            artifact_id=f"{ctx.aircraft_id}_{ctx.version}_RELEASE_MANIFEST",
            artifact_type="PROTOTYPE_RELEASE_MANIFEST",
            file_path=out_dir / "release" / "release_manifest.json",
            phase=PipelinePhase.PHASE_6F_VALIDATION.value,
            metadata={
                "release_id": rel_res.manifest.release_id,
                "release_status": rel_res.release_status,
                "prototype_status": rel_res.manifest.prototype_status,
                "checks_count": len(rel_res.manifest.checks),
                "blocking_issues_count": len(rel_res.manifest.blocking_issues),
            }
        )

        manifest["release_gate_summary"] = {
            "release_id": rel_res.manifest.release_id,
            "release_status": rel_res.release_status,
            "prototype_status": rel_res.manifest.prototype_status,
            "is_released": rel_res.is_released,
            "total_checks": len(rel_res.manifest.checks),
            "passed_checks": sum(1 for c in rel_res.manifest.checks if c.status == "PASS"),
            "warnings_count": len(rel_res.manifest.warnings),
            "blocking_issues_count": len(rel_res.manifest.blocking_issues),
            "summary": rel_res.manifest.summary,
        }

        manifest_path = out_dir / "pipeline_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
