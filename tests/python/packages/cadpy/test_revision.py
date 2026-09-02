"""Comprehensive tests for Phase 9 Engineering Design Revision, Change Detection, and Impact Analysis."""

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
)
from cadpy.pipeline import (
    DesignStudioPipeline,
    PipelinePhase,
    PhaseState,
)
from cadpy.revision import (
    ChangeType,
    ChangeSeverity,
    ImpactCategory,
    RequirementChange,
    RequirementDiffEngine,
    DependencyGraph,
    ImpactAnalysisEngine,
    RevisionManifest,
)

SPEC_PATH = r"c:\Users\samyuktha\OneDrive\Documents\torqwings studio v2\exports\fixed_wing_report\FixedWing_SURVEY_Engineering_Report.md"


def test_unchanged_specification():
    """Verify that comparing identical specifications yields no modified engineering requirements."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    spec_v1 = parse_aircraft_specification(raw_doc, source_name="FW-007_v1")
    spec_v2 = parse_aircraft_specification(raw_doc, source_name="FW-007_v2")

    changes = RequirementDiffEngine.compare_specifications(spec_v1, spec_v2)
    assert len(changes) == 0

    impact = ImpactAnalysisEngine.analyze_impact(changes)
    assert impact.impact_level == ChangeSeverity.INFO.value
    assert impact.summary["change_scope"] == "NO_CHANGES"
    assert len(impact.unaffected_components) > 0


def test_unit_only_normalization():
    """Verify that equivalent values with different units (e.g., 2000 mm vs 2.0 m) are recognized as unchanged."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    spec_v1 = parse_aircraft_specification(raw_doc, source_name="FW-007_v1")
    spec_v2 = parse_aircraft_specification(raw_doc, source_name="FW-007_v2")

    # Change unit from mm to m while scaling value
    spec_v2.wing.span.value = 2.0
    spec_v2.wing.span.unit = "m"

    changes = RequirementDiffEngine.compare_specifications(spec_v1, spec_v2)
    # The normalized numerical value 2000 mm == 2.0 m is identical
    assert len(changes) == 0 or all(c.change_type in [ChangeType.UNCHANGED.value, ChangeType.UNIT_ONLY.value] for c in changes)


def test_explicit_value_change():
    """Verify that a modified geometric value is detected with proper classification and severity."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    spec_v1 = parse_aircraft_specification(raw_doc, source_name="FW-007_v1")
    spec_v2 = parse_aircraft_specification(raw_doc, source_name="FW-007_v2")

    spec_v2.wing.span.value = 2200.0  # 2000 mm -> 2200 mm

    changes = RequirementDiffEngine.compare_specifications(spec_v1, spec_v2)
    assert len(changes) == 1
    c = changes[0]
    assert c.parameter == "wing.span"
    assert c.category == "wing"
    assert c.old_value == 2000.0
    assert c.new_value == 2200.0
    assert c.change_type == ChangeType.MODIFIED.value
    assert c.severity == ChangeSeverity.HIGH.value

    # Human-readable diff
    human_diff = RequirementDiffEngine.format_human_readable_diff(changes)
    assert "Span" in human_diff or "Wingspan" in human_diff
    assert "2000.0 mm → 2200.0 mm" in human_diff


def test_provenance_status_changes():
    """Verify provenance and status transitions (UNKNOWN -> EXPLICIT, EXPLICIT -> CONFLICT)."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    spec_v1 = parse_aircraft_specification(raw_doc, source_name="FW-007_v1")
    spec_v2 = parse_aircraft_specification(raw_doc, source_name="FW-007_v2")

    # 1. UNKNOWN -> EXPLICIT
    spec_v1.identity.author = Requirement(None, "", "Sec 1", "identity", "UNKNOWN")
    spec_v2.identity.author = Requirement("Test Engineer", "", "Sec 1", "identity", "EXPLICIT")

    # 2. EXPLICIT -> CONFLICT
    if hasattr(spec_v2.mass, "MTOW"):
        spec_v1.mass.MTOW.status = "EXPLICIT"
        spec_v2.mass.MTOW.status = "CONFLICT"
    else:
        spec_v1.mass.mtow.status = "EXPLICIT"
        spec_v2.mass.mtow.status = "CONFLICT"

    changes = RequirementDiffEngine.compare_specifications(spec_v1, spec_v2)
    change_map = {c.parameter.lower(): c for c in changes}

    assert "identity.author" in change_map
    assert change_map["identity.author"].change_type in [ChangeType.ADDED.value, ChangeType.STATUS_CHANGED.value, ChangeType.MODIFIED.value]

    assert "mass.mtow" in change_map
    assert change_map["mass.mtow"].change_type == ChangeType.CONFLICT_CHANGED.value


def test_wing_change_impact():
    """Verify that a wing parameter change affects wing CAD, structure, and manufacturing while fuselage is unaffected."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    spec_v1 = parse_aircraft_specification(raw_doc, source_name="FW-007_v1")
    spec_v2 = parse_aircraft_specification(raw_doc, source_name="FW-007_v2")

    spec_v2.wing.span.value = 2200.0

    changes = RequirementDiffEngine.compare_specifications(spec_v1, spec_v2)
    impact = ImpactAnalysisEngine.analyze_impact(changes)

    # CAD Impact
    assert impact.affected_cad_components["MainWing"] == ImpactCategory.DIRECTLY_AFFECTED.value
    assert impact.affected_cad_components["MainWing_Left"] == ImpactCategory.DIRECTLY_AFFECTED.value
    assert impact.affected_cad_components["Fuselage"] == ImpactCategory.UNAFFECTED.value

    # Structural Impact
    assert impact.affected_structural_components["MainWing_Left_MainSpar"] == ImpactCategory.INDIRECTLY_AFFECTED.value
    assert impact.affected_structural_components["MainWing_Left_Rib_001"] == ImpactCategory.INDIRECTLY_AFFECTED.value
    assert impact.affected_structural_components["Fuselage_Former_001"] == ImpactCategory.UNAFFECTED.value

    # Manufacturing Impact
    assert impact.affected_manufacturing_parts["SPAR-L-MAIN"] == ImpactCategory.INDIRECTLY_AFFECTED.value
    assert impact.affected_manufacturing_parts["RIB-L-001"] == ImpactCategory.INDIRECTLY_AFFECTED.value
    assert impact.affected_manufacturing_parts["FMR-001"] == ImpactCategory.UNAFFECTED.value

    # Summary
    assert impact.impact_level == ChangeSeverity.HIGH.value
    assert impact.requires_user_confirmation is True


def test_fuselage_change_impact():
    """Verify that a fuselage parameter change affects fuselage formers and longerons while wing is unaffected."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    spec_v1 = parse_aircraft_specification(raw_doc, source_name="FW-007_v1")
    spec_v2 = parse_aircraft_specification(raw_doc, source_name="FW-007_v2")

    spec_v2.fuselage.length.value = 1600.0

    changes = RequirementDiffEngine.compare_specifications(spec_v1, spec_v2)
    impact = ImpactAnalysisEngine.analyze_impact(changes)

    # CAD Impact
    assert impact.affected_cad_components["Fuselage"] == ImpactCategory.DIRECTLY_AFFECTED.value
    assert impact.affected_cad_components["MainWing"] == ImpactCategory.UNAFFECTED.value

    # Structural Impact
    assert impact.affected_structural_components["Fuselage_Former_001"] == ImpactCategory.INDIRECTLY_AFFECTED.value
    assert impact.affected_structural_components["Fuselage_Longeron_UpperLeft"] == ImpactCategory.INDIRECTLY_AFFECTED.value
    assert impact.affected_structural_components["MainWing_Left_MainSpar"] == ImpactCategory.UNAFFECTED.value

    # Manufacturing Impact
    assert impact.affected_manufacturing_parts["FMR-001"] == ImpactCategory.INDIRECTLY_AFFECTED.value
    assert impact.affected_manufacturing_parts["LONG-UPPER-L"] == ImpactCategory.INDIRECTLY_AFFECTED.value
    assert impact.affected_manufacturing_parts["RIB-L-001"] == ImpactCategory.UNAFFECTED.value


def test_manufacturing_profile_only_impact():
    """Verify that a manufacturing profile change regenerates manufacturing without affecting CAD or Structure."""
    impact = ImpactAnalysisEngine.analyze_impact([], is_manufacturing_profile_change=True)

    # CAD & Structure unaffected
    for c, stat in impact.affected_cad_components.items():
        assert stat == ImpactCategory.UNAFFECTED.value
    for s, stat in impact.affected_structural_components.items():
        assert stat == ImpactCategory.UNAFFECTED.value

    # Manufacturing parts directly affected
    assert impact.affected_manufacturing_parts["RIB-L-001"] == ImpactCategory.DIRECTLY_AFFECTED.value
    assert impact.can_selectively_regenerate is True
    assert "PHASE_6D_LASER" in impact.selective_scope


def test_metadata_only_change_impact():
    """Verify that metadata-only changes (author, title) have zero CAD, Structure, and Manufacturing impact."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    spec_v1 = parse_aircraft_specification(raw_doc, source_name="FW-007_v1")
    spec_v2 = parse_aircraft_specification(raw_doc, source_name="FW-007_v2")

    spec_v2.identity.author.value = "Lead Aero Architect"
    spec_v2.identity.title.value = "Updated UAV Specification"

    changes = RequirementDiffEngine.compare_specifications(spec_v1, spec_v2)
    impact = ImpactAnalysisEngine.analyze_impact(changes)

    assert impact.summary["total_cad_affected"] == 0
    assert impact.summary["total_structural_affected"] == 0
    assert impact.summary["total_manufacturing_affected"] == 0
    assert impact.can_selectively_regenerate is True


def test_version_immutability(tmp_path):
    """Verify that generating v2 does not mutate v1 artifacts, manifest, or directory state."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    profile = create_prototype_manufacturing_profile("FW007_Production_Profile")

    # 1. Execute v1
    ctx_v1 = DesignStudioPipeline.execute(
        part1_input=raw_doc,
        aircraft_id="FW-007",
        project_id="PROJ_001",
        version="v1",
        profile=profile,
        output_base_dir=tmp_path
    )

    v1_manifest_path = tmp_path / "FW-007" / "v1" / "pipeline_manifest.json"
    assert v1_manifest_path.exists()
    v1_manifest_text = v1_manifest_path.read_text(encoding="utf-8")

    # 2. Modify specification for v2
    raw_doc_v2 = raw_doc.replace("2.00 meters", "2.10 meters")

    ctx_v2 = DesignStudioPipeline.execute(
        part1_input=raw_doc_v2,
        aircraft_id="FW-007",
        project_id="PROJ_001",
        version="v2",
        parent_version="v1",
        parent_spec_text=raw_doc,
        profile=profile,
        output_base_dir=tmp_path
    )

    # 3. Verify v1 remains unchanged
    v1_manifest_text_after = v1_manifest_path.read_text(encoding="utf-8")
    assert v1_manifest_text == v1_manifest_text_after

    # 4. Verify v2 has distinct output directory and revision manifest
    v2_manifest_path = tmp_path / "FW-007" / "v2" / "pipeline_manifest.json"
    v2_rev_manifest_path = tmp_path / "FW-007" / "v2" / "revision_manifest.json"
    assert v2_manifest_path.exists()
    assert v2_rev_manifest_path.exists()

    rev_data = json.loads(v2_rev_manifest_path.read_text(encoding="utf-8"))
    assert rev_data["parent_version"] == "v1"
    assert rev_data["version"] == "v2"
    assert rev_data["changes_count"] >= 1


def test_failed_revision_isolation(tmp_path):
    """Verify that an invalid v2 revision fails cleanly while v1 remains valid and usable."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    profile = create_prototype_manufacturing_profile("FW007_Production_Profile")

    # 1. Generate v1
    ctx_v1 = DesignStudioPipeline.execute(
        part1_input=raw_doc,
        aircraft_id="FW-007",
        version="v1",
        profile=profile,
        output_base_dir=tmp_path
    )
    assert ctx_v1.validation_result.overall_status == "PASS"

    # 2. Generate invalid v2 (negative span causing failure)
    raw_doc_invalid = raw_doc.replace("2.00 meters", "-5.00 meters")
    ctx_v2 = DesignStudioPipeline.execute(
        part1_input=raw_doc_invalid,
        aircraft_id="FW-007",
        version="v2",
        parent_version="v1",
        parent_spec_text=raw_doc,
        profile=profile,
        output_base_dir=tmp_path
    )

    # v2 failed
    assert len(ctx_v2.errors) > 0
    assert ctx_v2.phase_records["PHASE_3_REQUIREMENTS"].state == PhaseState.FAILED.value or ctx_v2.phase_records["PHASE_4_CAD"].state in [PhaseState.FAILED.value, PhaseState.SKIPPED.value]

    # v1 is still intact and valid
    v1_manifest = json.loads((tmp_path / "FW-007" / "v1" / "pipeline_manifest.json").read_text(encoding="utf-8"))
    assert v1_manifest["status"] == "PASS"
    assert v1_manifest["prototype_readiness"] == "READY"
