"""Comprehensive tests for Phase 13 Final Prototype Release Gate, Cross-Stage QA & Traceability."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from cadpy.requirements import parse_aircraft_specification
from cadpy.manufacturing import (
    create_prototype_manufacturing_profile,
    generate_complete_manufacturing_pipeline,
    ManufacturingValidationEngine,
    ManufacturingClassifier,
    FabricationGeometryGenerator,
    SheetNester,
    PrintablePartGenerator,
    get_prototype_laser_balsa_profile,
)
from cadpy.aircraft import generate_aircraft_from_spec
from cadpy.review import EngineeringReviewEngine
from cadpy.build_package import BuildPackageEngine, BuildPart
from cadpy.build_visualization import BuildVisualizationEngine
from cadpy.release_gate import (
    ReleaseGateEngine,
    ReleaseGateResult,
    ReleaseStatus,
    ReleaseGateCheckCategory,
)
from cadpy.pipeline import DesignStudioPipeline

SPEC_PATH = r"c:\Users\samyuktha\OneDrive\Documents\torqwings studio v2\exports\fixed_wing_report\FixedWing_SURVEY_Engineering_Report.md"


def _generate_mfg_entities(cad_res, profile):
    classifier = ManufacturingClassifier(profile)
    mfg_parts = classifier.classify_structural_assembly(cad_res.structural_components)
    fab_geoms, joints = FabricationGeometryGenerator(profile).generate_fabrication_geometries(mfg_parts, cad_res.structural_components)
    nester = SheetNester(profile.laser_cut or get_prototype_laser_balsa_profile())
    sheets = nester.nest_parts(mfg_parts, fab_geoms)
    p_gen = PrintablePartGenerator(profile)
    print_parts, splits = p_gen.generate_printable_parts(mfg_parts, fab_geoms, cad_res.structural_components)
    return mfg_parts, fab_geoms, joints, sheets, print_parts, splits


def test_fw_007_final_release_gate_evaluation(tmp_path):
    """Verify complete release gate evaluation on authoritative FW-007 baseline."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")
    cad_res = generate_aircraft_from_spec(spec)
    profile = create_prototype_manufacturing_profile("FW007_Production_Profile")

    # Export manufacturing pipeline files
    generate_complete_manufacturing_pipeline("FW-007", profile, cad_res.structural_components, output_dir=tmp_path)
    mfg_parts, fab_geoms, joints, sheets, print_parts, splits = _generate_mfg_entities(cad_res, profile)

    val_res = ManufacturingValidationEngine.run_full_validation(
        aircraft_id="FW-007",
        profile=profile,
        structural_components=cad_res.structural_components,
        structural_assembly=cad_res.structural_assembly,
        spec=spec,
        output_dir=tmp_path
    )

    eng_review = EngineeringReviewEngine.execute_review(
        aircraft_id="FW-007",
        version="v1",
        spec=spec,
        cad_result=cad_res,
        structural_components=cad_res.structural_components,
        manufacturing_parts=mfg_parts,
        validation_result=val_res,
        bom=val_res.bom
    )

    build_pkg = BuildPackageEngine.generate_build_package(
        aircraft_id="FW-007",
        version="v1",
        spec=spec,
        manufacturing_parts=mfg_parts,
        joints=joints,
        nested_sheets=sheets,
        printable_parts=print_parts,
        validation_result=val_res,
        engineering_review=eng_review,
        output_dir=tmp_path
    )

    vis_pkg = BuildVisualizationEngine.generate_visualization_package(
        aircraft_id="FW-007",
        version="v1",
        spec=spec,
        build_package=build_pkg,
        structural_components=cad_res.structural_components,
        manufacturing_parts=mfg_parts,
        joints=joints,
        nested_sheets=sheets,
        printable_parts=print_parts,
        engineering_review=eng_review,
        output_dir=tmp_path
    )

    # Execute Phase 13 Release Gate
    rel_res = ReleaseGateEngine.evaluate_release(
        aircraft_id="FW-007",
        version="v1",
        spec=spec,
        cad_result=cad_res,
        structural_components=cad_res.structural_components,
        manufacturing_parts=mfg_parts,
        validation_result=val_res,
        engineering_review=eng_review,
        build_package=build_pkg,
        build_visualization=vis_pkg,
        output_dir=tmp_path
    )

    # 1. Release Decision Verification
    assert rel_res.is_released is True
    assert rel_res.release_status == ReleaseStatus.READY_WITH_WARNINGS.value
    assert len(rel_res.manifest.blocking_issues) == 0
    assert len(rel_res.manifest.warnings) >= 1  # Preserves MTOW conflict notice

    # 2. Cross-Stage Consistency Checks
    checks_by_id = {c.check_id: c for c in rel_res.manifest.checks}
    assert checks_by_id["REL-STAGE-001"].status == "PASS"
    assert checks_by_id["REL-CAD-001"].status == "PASS"
    assert checks_by_id["REL-STR-001"].status == "PASS"
    assert checks_by_id["REL-MFG-001"].status == "PASS"
    assert checks_by_id["REL-BPKG-001"].status == "PASS"
    assert checks_by_id["REL-BPKG-002"].status == "PASS"

    # 3. Release Manifest Export
    rel_manifest_file = tmp_path / "release" / "release_manifest.json"
    assert rel_manifest_file.exists()
    data = json.loads(rel_manifest_file.read_text(encoding="utf-8"))
    assert data["aircraft_id"] == "FW-007"
    assert data["release_status"] == ReleaseStatus.READY_WITH_WARNINGS.value
    assert len(data["checks"]) >= 6

    # 4. Human-readable report format
    assert "PHASE 13 FINAL PROTOTYPE RELEASE GATE REPORT" in rel_res.report_text
    assert "FINAL DECISION: READY_WITH_WARNINGS" in rel_res.report_text


def test_controlled_missing_artifact_release_block(tmp_path):
    """Verify that a missing required release artifact triggers RELEASE_BLOCKED."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")
    cad_res = generate_aircraft_from_spec(spec)
    profile = create_prototype_manufacturing_profile("FW007_Production_Profile")

    mfg_parts, fab_geoms, joints, sheets, print_parts, splits = _generate_mfg_entities(cad_res, profile)

    val_res = ManufacturingValidationEngine.run_full_validation(
        aircraft_id="FW-007",
        profile=profile,
        structural_components=cad_res.structural_components,
        structural_assembly=cad_res.structural_assembly,
        spec=spec,
        output_dir=tmp_path
    )
    eng_review = EngineeringReviewEngine.execute_review(
        aircraft_id="FW-007",
        version="v1",
        spec=spec,
        cad_result=cad_res,
        structural_components=cad_res.structural_components,
        manufacturing_parts=mfg_parts,
        validation_result=val_res,
        bom=val_res.bom
    )

    build_pkg = BuildPackageEngine.generate_build_package(
        aircraft_id="FW-007",
        version="v1",
        spec=spec,
        manufacturing_parts=mfg_parts,
        joints=joints,
        nested_sheets=sheets,
        printable_parts=print_parts,
        validation_result=val_res,
        engineering_review=eng_review,
        output_dir=tmp_path
    )

    # Invalidate build package validation to simulate missing artifact failure
    build_pkg.build_validation.is_valid = False
    build_pkg.build_validation.warnings.append("Missing required fabrication artifact: Sheet_01.dxf")

    rel_res = ReleaseGateEngine.evaluate_release(
        aircraft_id="FW-007",
        version="v1",
        spec=spec,
        cad_result=cad_res,
        structural_components=cad_res.structural_components,
        manufacturing_parts=mfg_parts,
        validation_result=val_res,
        engineering_review=eng_review,
        build_package=build_pkg,
        output_dir=tmp_path
    )

    assert rel_res.is_released is False
    assert rel_res.release_status == ReleaseStatus.RELEASE_BLOCKED.value
    assert len(rel_res.manifest.blocking_issues) > 0


def test_duplicate_part_id_release_block(tmp_path):
    """Verify that duplicate physical part IDs trigger RELEASE_BLOCKED."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")
    cad_res = generate_aircraft_from_spec(spec)
    profile = create_prototype_manufacturing_profile("FW007_Production_Profile")

    mfg_parts, fab_geoms, joints, sheets, print_parts, splits = _generate_mfg_entities(cad_res, profile)
    val_res = ManufacturingValidationEngine.run_full_validation(
        aircraft_id="FW-007",
        profile=profile,
        structural_components=cad_res.structural_components,
        structural_assembly=cad_res.structural_assembly,
        spec=spec,
        output_dir=tmp_path
    )
    eng_review = EngineeringReviewEngine.execute_review(
        aircraft_id="FW-007",
        version="v1",
        spec=spec,
        cad_result=cad_res,
        structural_components=cad_res.structural_components,
        manufacturing_parts=mfg_parts,
        validation_result=val_res,
        bom=val_res.bom
    )

    build_pkg = BuildPackageEngine.generate_build_package(
        aircraft_id="FW-007",
        version="v1",
        spec=spec,
        manufacturing_parts=mfg_parts,
        joints=joints,
        nested_sheets=sheets,
        printable_parts=print_parts,
        validation_result=val_res,
        engineering_review=eng_review,
        output_dir=tmp_path
    )

    # Inject duplicate part
    import copy
    dup_part = copy.deepcopy(build_pkg.parts[0])
    build_pkg.parts.append(dup_part)

    rel_res = ReleaseGateEngine.evaluate_release(
        aircraft_id="FW-007",
        version="v1",
        spec=spec,
        cad_result=cad_res,
        structural_components=cad_res.structural_components,
        manufacturing_parts=mfg_parts,
        validation_result=val_res,
        engineering_review=eng_review,
        build_package=build_pkg,
        output_dir=tmp_path
    )

    assert rel_res.is_released is False
    assert rel_res.release_status == ReleaseStatus.RELEASE_BLOCKED.value
    assert any("duplicate" in issue.lower() for issue in rel_res.manifest.blocking_issues)


def test_full_pipeline_end_to_end_release_gate_integration(tmp_path):
    """Verify that DesignStudioPipeline executes Phase 13 and records release manifest."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    profile = create_prototype_manufacturing_profile("FW007_Production_Profile")

    ctx = DesignStudioPipeline.execute(
        part1_input=raw_doc,
        aircraft_id="FW-007",
        version="v1",
        profile=profile,
        output_base_dir=tmp_path
    )

    # Pipeline output verification
    assert ctx.release_gate is not None
    assert ctx.release_gate.is_released is True
    assert ctx.release_gate.release_status == ReleaseStatus.READY_WITH_WARNINGS.value

    # Artifact registration verification
    assert ctx.artifact_registry.get_artifact(f"FW-007_v1_RELEASE_MANIFEST") is not None or f"FW-007_v1_RELEASE_MANIFEST" in ctx.artifact_registry.artifacts

    # Pipeline manifest summary verification
    manifest_file = tmp_path / "FW-007" / "v1" / "pipeline_manifest.json"
    assert manifest_file.exists()
    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert "release_gate_summary" in manifest_data
    assert manifest_data["release_gate_summary"]["release_status"] == ReleaseStatus.READY_WITH_WARNINGS.value
    assert manifest_data["release_gate_summary"]["is_released"] is True
