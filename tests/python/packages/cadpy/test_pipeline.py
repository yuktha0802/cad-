"""Comprehensive tests for Phase 7 Design Studio End-to-End Pipeline Integration."""

import json
import os
from pathlib import Path
import pytest

from cadpy.pipeline import (
    PipelinePhase,
    PhaseState,
    ExecutionMode,
    ArtifactType,
    PhaseExecutionRecord,
    ArtifactRecord,
    ArtifactRegistry,
    DesignVersion,
    PipelineContext,
    DesignStudioPipeline,
)
from cadpy.manufacturing import (
    create_prototype_manufacturing_profile,
    get_prototype_laser_balsa_profile,
    get_prototype_3d_print_profile,
)
from cadpy.requirements import parse_aircraft_specification


SPEC_PATH = r"c:\Users\samyuktha\OneDrive\Documents\torqwings studio v2\exports\fixed_wing_report\FixedWing_SURVEY_Engineering_Report.md"


def test_fw_007_end_to_end_pipeline_execution(tmp_path):
    """Verify that the full Part 1 -> Part 2 pipeline executes cleanly across all 9 phases."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    profile = create_prototype_manufacturing_profile("FW007_Production_Profile")

    ctx = DesignStudioPipeline.execute(
        part1_input=raw_doc,
        aircraft_id="FW-007",
        project_id="PROJ_SURVEY_001",
        version="v1",
        profile=profile,
        output_base_dir=tmp_path
    )

    # 1. Pipeline Status & Phase States
    assert ctx.aircraft_id == "FW-007"
    assert ctx.version == "v1"
    assert len(ctx.errors) == 0
    assert len(ctx.phase_records) == 9

    expected_phases = [
        "PHASE_3_REQUIREMENTS",
        "PHASE_4_CAD",
        "PHASE_5_STRUCTURE",
        "PHASE_6A_MANUFACTURING_MODEL",
        "PHASE_6B_CLASSIFICATION",
        "PHASE_6C_FABRICATION",
        "PHASE_6D_LASER",
        "PHASE_6E_PRINT",
        "PHASE_6F_VALIDATION",
    ]

    for p in expected_phases:
        rec = ctx.phase_records[p]
        assert rec.state in {PhaseState.PASSED.value, PhaseState.WARNING.value}
        assert rec.progress == 1.0

    # 2. Structural & Manufacturing Inventory
    assert len(ctx.structural_components) == 48
    assert len(ctx.manufacturing_parts) == 48
    assert len(ctx.fabrication_geometries) == 48
    assert len(ctx.joints) == 69
    assert len(ctx.laser_sheets) == 3
    assert len(ctx.printable_parts) == 1

    # 3. Phase 6F Validation Status
    assert ctx.validation_result is not None
    assert ctx.validation_result.overall_status == "PASS"
    assert ctx.validation_result.prototype_readiness == "READY"

    # 4. Artifact Registry & Provenance
    assert len(ctx.artifact_registry.artifacts) >= 50
    spec_arts = ctx.artifact_registry.get_by_type(ArtifactType.SPECIFICATION.value)
    assert len(spec_arts) == 1

    dxf_arts = ctx.artifact_registry.get_by_type(ArtifactType.DXF.value)
    assert len(dxf_arts) == 47

    stl_arts = ctx.artifact_registry.get_by_type(ArtifactType.STL.value)
    assert len(stl_arts) == 1

    val_arts = ctx.artifact_registry.get_by_type(ArtifactType.VALIDATION_REPORT.value)
    assert len(val_arts) == 1

    # 5. Pipeline Manifest on Disk
    manifest_file = tmp_path / "FW-007" / "v1" / "pipeline_manifest.json"
    assert manifest_file.exists()
    m_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert m_data["status"] == "PASS"
    assert m_data["prototype_readiness"] == "READY"
    assert m_data["bom_summary"]["total_parts"] == 48
    assert m_data["bom_summary"]["total_joints"] == 69


def test_part1_authoritative_handoff_and_traceability(tmp_path):
    """Verify that Part 1 specification is the authoritative source without manual re-entry."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    ctx = DesignStudioPipeline.execute(
        part1_input=raw_doc,
        aircraft_id="FW-007",
        project_id="PROJ_HANDOFF",
        version="v1",
        output_base_dir=tmp_path
    )

    # Verify that dimensions in CAD result match Part 1 directly
    assert ctx.cad_result.manifest["parameters"]["wing_span"]["value"] == 2000.0
    assert ctx.cad_result.manifest["parameters"]["fuselage_length"]["value"] == 1500.0

    # Traceability query: Trace a wing rib DXF back to structural component
    query = ctx.artifact_registry.query_traceability("FW-007_v1_DXF_RIB-L-001")
    assert query["artifact_type"] == ArtifactType.DXF.value
    assert query["created_from_component"] == "MainWing_Left_Rib_001"
    assert query["version"] == "v1"


def test_design_versioning_and_immutability(tmp_path):
    """Verify that generating v1 and then v2 preserves v1 artifacts and generates v2 separately."""
    raw_doc_v1 = Path(SPEC_PATH).read_text(encoding="utf-8")

    # Generate v1
    ctx_v1 = DesignStudioPipeline.execute(
        part1_input=raw_doc_v1,
        aircraft_id="FW-007",
        version="v1",
        output_base_dir=tmp_path
    )

    # Modify Part 1 for v2 (e.g. wingspan = 2200 mm)
    raw_doc_v2 = raw_doc_v1.replace("2.00 meters", "2.20 meters").replace("2000 mm", "2200 mm")

    # Generate v2
    ctx_v2 = DesignStudioPipeline.execute(
        part1_input=raw_doc_v2,
        aircraft_id="FW-007",
        version="v2",
        output_base_dir=tmp_path
    )

    # 1. Check directories
    v1_dir = tmp_path / "FW-007" / "v1"
    v2_dir = tmp_path / "FW-007" / "v2"

    assert v1_dir.exists()
    assert v2_dir.exists()

    # 2. Check v1 artifacts are untouched
    v1_manifest = json.loads((v1_dir / "pipeline_manifest.json").read_text(encoding="utf-8"))
    v2_manifest = json.loads((v2_dir / "pipeline_manifest.json").read_text(encoding="utf-8"))

    assert v1_manifest["version"] == "v1"
    assert v2_manifest["version"] == "v2"
    assert v1_manifest["fingerprint"] != v2_manifest["fingerprint"]


def test_manufacturing_profile_switching_preserves_geometry(tmp_path):
    """Verify that changing manufacturing profile parameters does not change aircraft CAD geometry."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")

    prof_a = create_prototype_manufacturing_profile("Profile_A")
    prof_b = create_prototype_manufacturing_profile("Profile_B")
    prof_b.laser_cut.kerf = 0.25  # Different kerf

    ctx_a = DesignStudioPipeline.execute(
        part1_input=raw_doc,
        aircraft_id="FW-007",
        version="v1_profA",
        profile=prof_a,
        output_base_dir=tmp_path
    )

    ctx_b = DesignStudioPipeline.execute(
        part1_input=raw_doc,
        aircraft_id="FW-007",
        version="v1_profB",
        profile=prof_b,
        output_base_dir=tmp_path
    )

    # CAD geometry is identical
    assert ctx_a.cad_result.manifest["parameters"]["wing_span"]["value"] == ctx_b.cad_result.manifest["parameters"]["wing_span"]["value"]
    assert ctx_a.cad_result.manifest["parameters"]["fuselage_length"]["value"] == ctx_b.cad_result.manifest["parameters"]["fuselage_length"]["value"]
    assert len(ctx_a.structural_components) == len(ctx_b.structural_components)


def test_phase3_blocking_failure_propagation(tmp_path):
    """Verify that a blocking Phase 3 failure stops downstream execution and marks downstream SKIPPED."""
    # Invalid spec with zero wingspan and missing critical bounds
    broken_spec = "Fixed-Wing UAV Report\n\n## Wing\n- Span: 0 mm\n- Root Chord: 0 mm\n"

    ctx = DesignStudioPipeline.execute(
        part1_input=broken_spec,
        aircraft_id="FW-FAIL",
        version="v1",
        output_base_dir=tmp_path
    )

    assert ctx.phase_records["PHASE_3_REQUIREMENTS"].state == PhaseState.FAILED.value
    assert ctx.phase_records["PHASE_4_CAD"].state == PhaseState.SKIPPED.value
    assert ctx.phase_records["PHASE_5_STRUCTURE"].state == PhaseState.SKIPPED.value
    assert ctx.phase_records["PHASE_6F_VALIDATION"].state == PhaseState.SKIPPED.value


def test_stale_artifact_invalidation_and_fingerprint():
    """Verify that changes in Part 1 content change the pipeline fingerprint."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    profile = create_prototype_manufacturing_profile()

    fp1 = DesignStudioPipeline.compute_fingerprint(raw_doc, profile)
    fp2 = DesignStudioPipeline.compute_fingerprint(raw_doc + "\n# Modified Note\n", profile)
    assert fp1 != fp2
