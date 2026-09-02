"""Comprehensive tests for Phase 11 Prototype Build Package & Physical Assembly Preparation."""

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
    get_prototype_laser_balsa_profile,
    PrintablePartGenerator,
)
from cadpy.aircraft import generate_aircraft_from_spec
from cadpy.pipeline import DesignStudioPipeline
from cadpy.review import EngineeringReviewEngine
from cadpy.build_package import (
    BuildPackageEngine,
    PrototypeBuildPackage,
    BuildReadiness,
    BuildPart,
)

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


def test_fw_007_build_package_generation(tmp_path):
    """Verify complete prototype build package generation on authoritative FW-007 baseline."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")
    cad_res = generate_aircraft_from_spec(spec)
    profile = create_prototype_manufacturing_profile("FW007_Production_Profile")

    # Manufacturing pipeline
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

    pkg = BuildPackageEngine.generate_build_package(
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

    # 1. Part Inventory Verification
    assert len(pkg.parts) == 48
    laser_parts = [p for p in pkg.parts if p.manufacturing_process == "LASER_CUT"]
    print_parts_list = [p for p in pkg.parts if p.manufacturing_process == "THREE_D_PRINT"]
    assert len(laser_parts) == 47
    assert len(print_parts_list) == 1

    # 2. Material Schedule Verification
    assert len(pkg.materials) >= 2
    mat_names = {m.material for m in pkg.materials}
    assert any(m in mat_names for m in ["Balsa_3mm", "BALSA_3MM", "Aeroply_3mm", "PLYWOOD_3MM"])

    # 3. Joint Mapping Verification
    assert len(pkg.joints) == 69
    assert all(j.joint_type == "TAB_SLOT" for j in pkg.joints)

    # 4. Subassemblies & Assembly Sequence Verification
    assert "Fuselage" in pkg.subassemblies
    assert "MainWing_Left" in pkg.subassemblies
    assert "MainWing_Right" in pkg.subassemblies
    assert len(pkg.assembly_steps) == 5
    assert pkg.assembly_steps[0].title == "Fuselage Primary Framework Assembly"
    assert pkg.assembly_steps[-1].title == "Final Airframe Integration & Wing Attachment"

    # 5. Build Validation Integrity
    assert pkg.build_validation.is_valid is True
    assert pkg.prototype_readiness in [BuildReadiness.READY.value, BuildReadiness.READY_WITH_WARNINGS.value]

    # 6. File Outputs Generated
    manifest_path = tmp_path / "build_manifest.json"
    instructions_path = tmp_path / "build_instructions.md"
    assert manifest_path.exists()
    assert instructions_path.exists()
    inst_text = instructions_path.read_text(encoding="utf-8")
    assert "PROTOTYPE BUILD & ASSEMBLY INSTRUCTIONS" in inst_text
    assert "Fuselage Primary Framework Assembly" in inst_text


def test_missing_fabrication_artifact_detection(tmp_path):
    """Verify that a missing fabrication artifact marks build validation as invalid and NOT_READY."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")
    cad_res = generate_aircraft_from_spec(spec)
    profile = create_prototype_manufacturing_profile("FW007_Production_Profile")

    mfg_parts, fab_geoms, joints, sheets, print_parts, splits = _generate_mfg_entities(cad_res, profile)

    # Empty out nested sheets to simulate missing fabrication outputs
    pkg = BuildPackageEngine.generate_build_package(
        aircraft_id="FW-007",
        version="v1",
        spec=spec,
        manufacturing_parts=mfg_parts,
        joints=joints,
        nested_sheets=[],
        printable_parts=print_parts,
        output_dir=tmp_path
    )

    assert pkg.build_validation.is_valid is False
    assert pkg.prototype_readiness == BuildReadiness.NOT_READY.value
    assert len(pkg.build_validation.missing_artifacts) > 0


def test_duplicate_part_id_detection(tmp_path):
    """Verify that duplicate part identifiers are detected as blocking build validation errors."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")
    cad_res = generate_aircraft_from_spec(spec)
    profile = create_prototype_manufacturing_profile("FW007_Production_Profile")

    mfg_parts, fab_geoms, joints, sheets, print_parts, splits = _generate_mfg_entities(cad_res, profile)

    # Inject a duplicate part ID into the manufacturing parts
    mfg_parts_with_dup = list(mfg_parts)
    mfg_parts_with_dup.append(mfg_parts[0])

    pkg = BuildPackageEngine.generate_build_package(
        aircraft_id="FW-007",
        version="v1",
        spec=spec,
        manufacturing_parts=mfg_parts_with_dup,
        joints=joints,
        nested_sheets=sheets,
        printable_parts=print_parts,
        output_dir=tmp_path
    )

    assert pkg.build_validation.is_valid is False
    assert pkg.prototype_readiness == BuildReadiness.NOT_READY.value
    assert len(pkg.build_validation.duplicate_part_ids) > 0


def test_full_pipeline_generates_build_package_artifacts(tmp_path):
    """Verify that full pipeline execution automatically registers build package artifacts."""
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

    assert ctx.build_package is not None
    assert len(ctx.build_package.parts) == 48
    assert len(ctx.build_package.joints) == 69
    assert ctx.build_package.prototype_readiness in [BuildReadiness.READY.value, BuildReadiness.READY_WITH_WARNINGS.value]

    # Verify artifacts in manifest
    manifest_path = tmp_path / "FW-007" / "v1" / "pipeline_manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "build_package_summary" in data
    assert data["build_package_summary"]["parts_count"] == 48
    assert data["build_package_summary"]["laser_parts_count"] == 47
    assert data["build_package_summary"]["printable_parts_count"] == 1
    assert data["build_package_summary"]["joints_count"] == 69
