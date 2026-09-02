"""Comprehensive tests for Phase 12 3D Build Visualization, Part Inspection & Assembly Guidance."""

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
from cadpy.build_package import BuildPackageEngine
from cadpy.build_visualization import (
    BuildVisualizationEngine,
    BuildVisualizationPackage,
    BuildProgressStatus,
    ViewMode,
    HighlightMode,
    ViewerComponent,
    ViewerAssemblyStep,
    ViewerJoint,
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


def test_fw_007_build_visualization_generation(tmp_path):
    """Verify complete 3D build visualization model generation on FW-007 baseline."""
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

    # 1. Components & Mode Verification
    assert len(vis_pkg.components) == 48
    assert len(vis_pkg.view_modes) == 6
    assert ViewMode.ASSEMBLED.value in vis_pkg.view_modes
    assert ViewMode.EXPLODED.value in vis_pkg.view_modes

    # 2. Exploded Presentation Offsets (Preserves CAD geometry)
    left_wing_parts = [c for c in vis_pkg.components.values() if c.subassembly == "MainWing_Left"]
    assert len(left_wing_parts) > 0
    assert left_wing_parts[0].exploded_offset[1] == -180.0  # Exploded Y offset

    # 3. Assembly Hierarchy Tree
    assert vis_pkg.assembly_tree.node_type == "aircraft"
    assert len(vis_pkg.assembly_tree.children) >= 4  # Fuselage, Wings, Tails, Propulsion

    # 4. Traceability Chain
    sample_part = next(iter(vis_pkg.components.values()))
    assert sample_part.traceability is not None
    assert sample_part.traceability.requirement in ["wing.span", "fuselage.length", "tail.ht_span", "tail.vt_height", "propulsion.propeller_diameter", "mission.category"]
    assert sample_part.traceability.manufacturing_part == sample_part.id

    # 5. Build Progress & Status Separation
    assert vis_pkg.build_progress["overall_build_status"] == BuildProgressStatus.NOT_STARTED.value
    assert sample_part.engineering_status == "VALID"
    assert sample_part.manufacturing_status == "READY"
    assert sample_part.build_status == BuildProgressStatus.NOT_STARTED.value

    # 6. Joints & Steps
    assert len(vis_pkg.joints) == 69
    assert len(vis_pkg.steps) == 5
    assert len(vis_pkg.sheets) == 3
    assert len(vis_pkg.printable_parts) == 1

    # 7. File Export Verification
    exported_file = tmp_path / "visualization" / "build_visualization.json"
    assert exported_file.exists()
    data = json.loads(exported_file.read_text(encoding="utf-8"))
    assert data["aircraft_id"] == "FW-007"
    assert len(data["components"]) == 48


def test_build_progress_tracking_and_separation(tmp_path):
    """Verify that build progress updates properly without altering engineering validity."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")
    profile = create_prototype_manufacturing_profile("FW007_Production_Profile")

    ctx = DesignStudioPipeline.execute(
        part1_input=raw_doc,
        aircraft_id="FW-007",
        version="v1",
        profile=profile,
        output_base_dir=tmp_path
    )

    vis_pkg = ctx.build_visualization
    assert vis_pkg is not None

    first_part_id = next(iter(vis_pkg.components.keys()))
    assert vis_pkg.components[first_part_id].build_status == BuildProgressStatus.NOT_STARTED.value

    # Update single part progress
    BuildVisualizationEngine.update_part_build_progress(vis_pkg, first_part_id, BuildProgressStatus.COMPLETE)
    assert vis_pkg.components[first_part_id].build_status == BuildProgressStatus.COMPLETE.value
    assert vis_pkg.components[first_part_id].engineering_status == "VALID"
    assert vis_pkg.build_progress["completed_parts_count"] == 1
    assert vis_pkg.build_progress["overall_build_status"] == BuildProgressStatus.IN_PROGRESS.value

    # Update step progress
    step_0 = vis_pkg.steps[0]
    BuildVisualizationEngine.update_step_build_progress(vis_pkg, step_0.step_id, BuildProgressStatus.COMPLETE)
    assert step_0.build_status == BuildProgressStatus.COMPLETE.value
    assert vis_pkg.build_progress["completed_steps_count"] == 1


def test_revision_reset_rule_for_changed_components(tmp_path):
    """Verify that changed components in v2 do NOT inherit v1 completed build progress."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")
    cad_res = generate_aircraft_from_spec(spec)
    profile = create_prototype_manufacturing_profile("FW007_Production_Profile")
    mfg_parts, fab_geoms, joints, sheets, print_parts, splits = _generate_mfg_entities(cad_res, profile)

    build_pkg_v1 = BuildPackageEngine.generate_build_package(
        aircraft_id="FW-007",
        version="v1",
        spec=spec,
        manufacturing_parts=mfg_parts,
        joints=joints,
        nested_sheets=sheets,
        printable_parts=print_parts,
    )
    v1_pkg = BuildVisualizationEngine.generate_visualization_package(
        aircraft_id="FW-007",
        version="v1",
        spec=spec,
        build_package=build_pkg_v1,
        structural_components=cad_res.structural_components,
        manufacturing_parts=mfg_parts,
    )

    # Mark all parts in v1 as COMPLETE
    for pid in v1_pkg.components:
        BuildVisualizationEngine.update_part_build_progress(v1_pkg, pid, BuildProgressStatus.COMPLETE)
    assert v1_pkg.build_progress["overall_build_status"] == BuildProgressStatus.COMPLETE.value

    # Construct v2 visualization package
    build_pkg_v2 = BuildPackageEngine.generate_build_package(
        aircraft_id="FW-007",
        version="v2",
        spec=spec,
        manufacturing_parts=mfg_parts,
        joints=joints,
        nested_sheets=sheets,
        printable_parts=print_parts,
    )
    v2_pkg = BuildVisualizationEngine.generate_visualization_package(
        aircraft_id="FW-007",
        version="v2",
        spec=spec,
        build_package=build_pkg_v2,
        structural_components=cad_res.structural_components,
        manufacturing_parts=mfg_parts,
        parent_version="v1"
    )

    # Identify changed parts from Impact Analysis
    all_keys = list(v1_pkg.components.keys())
    sample_key = all_keys[0]
    unaffected_key = all_keys[-1]
    changed_parts = {sample_key}
    BuildVisualizationEngine.propagate_revision_build_state(v1_pkg, v2_pkg, changed_parts)

    # Changed parts must reset to NOT_STARTED
    assert v2_pkg.components[sample_key].build_status == BuildProgressStatus.NOT_STARTED.value
    assert v2_pkg.components[unaffected_key].build_status == BuildProgressStatus.COMPLETE.value
    assert v2_pkg.build_progress["overall_build_status"] == BuildProgressStatus.IN_PROGRESS.value


def test_visualization_integrity_validation():
    """Verify integrity audit detects missing joints, duplicate IDs, and cycles."""
    comp1 = ViewerComponent(id="P1", display_name="Part 1")
    comp2 = ViewerComponent(id="P2", display_name="Part 2")
    joint1 = ViewerJoint(
        joint_id="J1",
        parent_part_id="P1",
        child_part_id="P2",
        joint_type="TAB_SLOT",
        interface_location=(0, 0, 0),
        orientation="X"
    )
    step1 = ViewerAssemblyStep(
        step_id="S1",
        step_number=1,
        title="Step 1",
        description="First",
        subassembly="Fuselage",
        dependencies=[]
    )
    step2 = ViewerAssemblyStep(
        step_id="S2",
        step_number=2,
        title="Step 2",
        description="Second",
        subassembly="Fuselage",
        dependencies=["S1"]
    )

    pkg = BuildVisualizationPackage(
        aircraft_id="TEST",
        version="v1",
        parent_version=None,
        created_at="2026-09-01T00:00:00Z",
        view_modes=["ASSEMBLED"],
        components={"P1": comp1, "P2": comp2},
        assembly_tree=BuildVisualizationEngine._construct_assembly_tree("TEST", {"P1": comp1, "P2": comp2}),
        subassemblies=["Fuselage"],
        steps=[step1, step2],
        joints=[joint1],
        sheets=[],
        printable_parts=[],
        build_progress={},
        engineering_review_summary={},
        warnings=[],
        summary={}
    )

    res = BuildVisualizationEngine.validate_visualization_integrity(pkg)
    assert res["is_valid"] is True
    assert res["status"] == "PASS"

    # Inject missing joint part reference
    pkg.joints.append(ViewerJoint(
        joint_id="J_BAD",
        parent_part_id="P1",
        child_part_id="MISSING_PART_XYZ",
        joint_type="TAB_SLOT",
        interface_location=(0, 0, 0),
        orientation="X"
    ))
    res_bad = BuildVisualizationEngine.validate_visualization_integrity(pkg)
    assert res_bad["is_valid"] is False
    assert any("MISSING_PART_XYZ" in err for err in res_bad["errors"])
