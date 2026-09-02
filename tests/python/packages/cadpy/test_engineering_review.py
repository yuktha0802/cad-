"""Comprehensive tests for Phase 10 Engineering Design Review, Requirement Compliance & Prototype Readiness."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from cadpy.requirements import (
    AircraftSpecification,
    Requirement,
    parse_aircraft_specification,
)
from cadpy.manufacturing import (
    create_prototype_manufacturing_profile,
    generate_complete_manufacturing_pipeline,
    ManufacturingValidationEngine,
    ManufacturingClassifier,
)
from cadpy.aircraft import generate_aircraft_from_spec
from cadpy.pipeline import (
    DesignStudioPipeline,
)
from cadpy.review import (
    EngineeringReview,
    EngineeringReviewEngine,
    ReviewStatus,
    PrototypeReadiness,
    CoverageStage,
)

SPEC_PATH = r"c:\Users\samyuktha\OneDrive\Documents\torqwings studio v2\exports\fixed_wing_report\FixedWing_SURVEY_Engineering_Report.md"


def test_fw_007_full_engineering_review(tmp_path):
    """Verify complete engineering review execution on authoritative FW-007 baseline."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")
    cad_res = generate_aircraft_from_spec(spec)
    profile = create_prototype_manufacturing_profile("FW007_Production_Profile")

    # Generate manufacturing pipeline
    generate_complete_manufacturing_pipeline(
        aircraft_id="FW-007",
        profile=profile,
        structural_components=cad_res.structural_components,
        output_dir=tmp_path
    )

    val_res = ManufacturingValidationEngine.run_full_validation(
        aircraft_id="FW-007",
        profile=profile,
        structural_components=cad_res.structural_components,
        structural_assembly=cad_res.structural_assembly,
        spec=spec,
        output_dir=tmp_path
    )
    mfg_parts = ManufacturingClassifier(profile).classify_structural_assembly(cad_res.structural_components)
    bom = val_res.bom

    review = EngineeringReviewEngine.execute_review(
        aircraft_id="FW-007",
        version="v1",
        spec=spec,
        cad_result=cad_res,
        structural_components=cad_res.structural_components,
        manufacturing_parts=mfg_parts,
        validation_result=val_res,
        bom=bom
    )

    # 1. Status Aggregation
    assert review.overall_status in ["PASS", "PASS WITH WARNINGS"]
    assert review.prototype_status in [PrototypeReadiness.READY.value, PrototypeReadiness.READY_WITH_WARNINGS.value]

    # 2. Geometry Compliance
    assert len(review.geometry_compliance) >= 4
    geom_map = {item.parameter: item for item in review.geometry_compliance}
    assert geom_map["Wingspan"].status == ReviewStatus.PASS.value
    assert geom_map["Fuselage Length"].status == ReviewStatus.PASS.value

    # 3. Configuration Compliance
    cfg_map = {item.parameter: item for item in review.configuration_compliance}
    assert cfg_map["Wing Position"].status == ReviewStatus.PASS.value
    assert cfg_map["Propulsion Layout"].status == ReviewStatus.PASS.value

    # 4. Component Existence
    comp_map = {item.parameter: item for item in review.component_existence}
    assert comp_map["Structural Solid Count"].status == ReviewStatus.PASS.value
    assert comp_map["Manufacturing Parts Count"].status == ReviewStatus.PASS.value

    # 5. Mass Conflict Detection
    mass_map = {item.parameter: item for item in review.mass_review}
    assert "Takeoff Mass (MTOW)" in mass_map
    assert mass_map["Takeoff Mass (MTOW)"].status == ReviewStatus.CONFLICT.value

    # 6. CG Review (Not Verifiable without complete inertia)
    cg_item = review.cg_review[0]
    assert cg_item.status == ReviewStatus.NOT_VERIFIABLE.value

    # 7. Summary Verification
    assert review.summary["total_items_reviewed"] >= 15
    assert len(review.blocking_failures) == 0


def test_dimensional_failure_blocking(tmp_path):
    """Verify that a dimensional mismatch creates a blocking failure and sets prototype status to NOT_READY."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")
    cad_res = generate_aircraft_from_spec(spec)
    profile = create_prototype_manufacturing_profile("FW007_Production_Profile")

    val_res = ManufacturingValidationEngine.run_full_validation(
        aircraft_id="FW-007",
        profile=profile,
        structural_components=cad_res.structural_components,
        structural_assembly=cad_res.structural_assembly,
        spec=spec,
        output_dir=tmp_path
    )

    # Intentionally drift the measured wingspan by 50mm
    val_res.virtual_assembly.critical_dimensions["wingspan"] = 2050.0

    review = EngineeringReviewEngine.execute_review(
        aircraft_id="FW-007",
        version="v1",
        spec=spec,
        cad_result=cad_res,
        structural_components=cad_res.structural_components,
        manufacturing_parts=[1] * 48,
        validation_result=val_res
    )

    assert review.overall_status == ReviewStatus.FAIL.value
    assert review.prototype_status == PrototypeReadiness.NOT_READY.value
    assert len(review.blocking_failures) > 0
    assert any("Wingspan" in f for f in review.blocking_failures)


def test_partial_pipeline_incomplete():
    """Verify that if pipeline stages are missing, engineering review reports INCOMPLETE / NOT_READY."""
    review = EngineeringReviewEngine.execute_review(
        aircraft_id="FW-007",
        version="v1",
        spec=None,
        cad_result=None,
        structural_components=[],
        manufacturing_parts=[],
        validation_result=None
    )

    assert review.overall_status == ReviewStatus.INCOMPLETE.value
    assert review.prototype_status == PrototypeReadiness.NOT_READY.value
    assert len(review.blocking_failures) > 0


def test_non_verifiable_requirement_handling():
    """Verify that operational requirements without CAD geometry are classified as NOT_DIRECTLY_VERIFIABLE without failing."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")

    review = EngineeringReview(aircraft_id="FW-007", version="v1")
    EngineeringReviewEngine._review_requirement_coverage(spec, review)

    cov_map = {item.parameter: item for item in review.requirement_coverage}
    assert "mission.category" in cov_map
    assert cov_map["mission.category"].status == CoverageStage.NOT_DIRECTLY_VERIFIABLE.value


def test_pipeline_generates_engineering_review_artifact(tmp_path):
    """Verify that running the full pipeline generates engineering_review.json and registers the artifact."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    profile = create_prototype_manufacturing_profile("FW007_Production_Profile")

    ctx = DesignStudioPipeline.execute(
        part1_input=raw_doc,
        aircraft_id="FW-007",
        project_id="PROJ_001",
        version="v1",
        profile=profile,
        output_base_dir=tmp_path
    )

    # 1. Review Object attached to context
    assert ctx.engineering_review is not None
    assert ctx.engineering_review.overall_status in ["PASS", "PASS WITH WARNINGS"]

    # 2. JSON File Generated
    review_json = tmp_path / "FW-007" / "v1" / "engineering_review.json"
    assert review_json.exists()
    rev_data = json.loads(review_json.read_text(encoding="utf-8"))
    assert rev_data["aircraft_id"] == "FW-007"
    assert "geometry_compliance" in rev_data
    assert "configuration_compliance" in rev_data
    assert "mass_review" in rev_data

    # 3. Embedded in pipeline_manifest.json
    manifest_json = tmp_path / "FW-007" / "v1" / "pipeline_manifest.json"
    manifest_data = json.loads(manifest_json.read_text(encoding="utf-8"))
    assert "engineering_review_summary" in manifest_data
    assert manifest_data["engineering_review_summary"]["overall_status"] == ctx.engineering_review.overall_status
