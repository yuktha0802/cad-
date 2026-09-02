"""Tests for Phase 6A, 6B, 6C, 6D, and 6E manufacturing models, classification, fabrication geometry, joints, kerf, nesting, and 3D printing."""

import json
import os
from pathlib import Path
import pytest

from cadpy.manufacturing import (
    ManufacturingProcess,
    ProvenanceSource,
    FabricationStrategy,
    DecompositionStrategy,
    JointType,
    ManufacturingStatus,
    ClassificationRule,
    ManufacturingMaterial,
    LaserCutProfile,
    ThreeDPrintProfile,
    ManufacturingProfile,
    ManufacturingPart,
    ManufacturingJoint,
    FabricationGeometry,
    FabricationGeometryGenerator,
    FabricationGeometryValidator,
    KerfCompensation,
    KerfCompensator,
    PlacedPart,
    ManufacturingSheet,
    SheetNester,
    export_part_dxf,
    export_part_svg,
    export_sheet_dxf,
    export_sheet_svg,
    LaserManufacturingValidator,
    generate_laser_manufacturing_pipeline,
    PrintStatus,
    SplitStatus,
    SplitJointType,
    PrintablePart,
    PrintSplitRecord,
    PartSplitter,
    PrintablePartGenerator,
    ThreeDPrintExporter,
    ThreeDPrintValidator,
    generate_3d_print_manufacturing_pipeline,
    generate_complete_manufacturing_pipeline,
    PrototypeReadinessStatus,
    ValidationSeverity,
    ManufacturingBOMItem,
    ManufacturingBOM,
    VirtualManufacturingAssembly,
    ManufacturingValidationResult,
    ManufacturingValidationEngine,
    ManufacturingClassifier,
    ManufacturingClassificationValidator,
    generate_manufacturing_part_id,
    validate_laser_cut_profile,
    validate_three_d_print_profile,
    validate_manufacturing_profile,
    create_manufacturing_part_from_structural_component,
    get_prototype_laser_balsa_profile,
    get_prototype_3d_print_profile,
    create_prototype_manufacturing_profile,
    build_manufacturing_manifest,
)
from cadpy.requirements import parse_aircraft_specification
from cadpy.aircraft import generate_aircraft_from_spec
from build123d import BuildSketch, Rectangle, Circle, Mode, Face, Box, import_stl


def test_manufacturing_profile_validation():
    """Test validation of valid and invalid laser and 3D print profiles."""
    valid_laser = LaserCutProfile(
        material="Balsa",
        thickness=3.0,
        kerf=0.15,
        clearance=0.10,
        sheet_width=900.0,
        sheet_height=600.0,
        sheet_margin=10.0
    )
    assert validate_laser_cut_profile(valid_laser) == []

    invalid_laser = LaserCutProfile(
        thickness=-1.0,
        kerf=-0.05,
        clearance=-0.1,
        sheet_width=0.0,
        sheet_height=-50.0,
        sheet_margin=-5.0
    )
    errors = validate_laser_cut_profile(invalid_laser)
    assert len(errors) >= 5

    valid_3dp = ThreeDPrintProfile(
        printer_bed_x=220.0,
        printer_bed_y=220.0,
        printer_bed_z=250.0,
        nozzle_diameter=0.4,
        minimum_wall_thickness=1.2,
        minimum_feature_size=0.8,
        print_clearance=0.2,
        joint_clearance=0.3
    )
    assert validate_three_d_print_profile(valid_3dp) == []

    invalid_3dp = ThreeDPrintProfile(
        printer_bed_x=0.0,
        printer_bed_y=-100.0,
        printer_bed_z=0.0,
        nozzle_diameter=-0.4,
        minimum_wall_thickness=0.0,
        minimum_feature_size=-0.5,
        print_clearance=-0.1,
        joint_clearance=-0.2
    )
    errors_3dp = validate_three_d_print_profile(invalid_3dp)
    assert len(errors_3dp) >= 6

    mfg_prof = ManufacturingProfile(
        name="Valid_Profile",
        laser_cut=valid_laser,
        three_d_print=valid_3dp
    )
    assert validate_manufacturing_profile(mfg_prof) == []

    empty_name_prof = ManufacturingProfile(name="", laser_cut=valid_laser)
    assert len(validate_manufacturing_profile(empty_name_prof)) > 0


def test_manufacturing_material_model():
    """Test material representation with known and unknown density and provenance."""
    mat_balsa = ManufacturingMaterial(
        name="Balsa_Sheet",
        process=ManufacturingProcess.LASER_CUT,
        nominal_thickness=3.0,
        density=0.00015,
        source=ProvenanceSource.REFERENCE_MATERIAL.value
    )
    assert mat_balsa.has_known_density is True
    assert mat_balsa.density == 0.00015
    assert mat_balsa.source == "REFERENCE_MATERIAL"

    mat_unknown = ManufacturingMaterial(
        name="Experimental_Foam",
        process=ManufacturingProcess.LASER_CUT,
        nominal_thickness=5.0,
        density=None,
        source=ProvenanceSource.UNKNOWN.value
    )
    assert mat_unknown.has_known_density is False
    assert mat_unknown.density is None
    assert mat_unknown.source == "UNKNOWN"


def test_deterministic_manufacturing_id_generation():
    """Test human-readable, deterministic manufacturing part ID naming conventions."""
    assert generate_manufacturing_part_id("MainWing_Left_Rib_003") == "RIB-L-003"
    assert generate_manufacturing_part_id("MainWing_Right_Rib_009") == "RIB-R-009"
    assert generate_manufacturing_part_id("MainWing_Left_MainSpar") == "SPAR-L-MAIN"
    assert generate_manufacturing_part_id("MainWing_Right_RearSpar") == "SPAR-R-REAR"
    assert generate_manufacturing_part_id("Fuselage_Former_000") == "FMR-000"
    assert generate_manufacturing_part_id("Fuselage_Longeron_UpperLeft") == "LONG-UPPER-L"
    assert generate_manufacturing_part_id("Fuselage_Longeron_LowerRight") == "LONG-LOWER-R"
    assert generate_manufacturing_part_id("Motor_Firewall") == "FIREWALL-001"
    assert generate_manufacturing_part_id("Wing_Fuselage_Attachment") == "WING-ATTACH-001"
    assert generate_manufacturing_part_id("HorizontalTail_Left_Spar") == "HT-SPAR-L-001"
    assert generate_manufacturing_part_id("HorizontalTail_Right_Rib_002") == "HT-RIB-R-002"
    assert generate_manufacturing_part_id("VerticalTail_MainSpar") == "VT-SPAR-001"
    assert generate_manufacturing_part_id("VerticalTail_Rib_001") == "VT-RIB-001"


def test_fw_007_full_structural_classification():
    """Verify deterministic classification of all 48 FW-007 structural components."""
    spec_path = r"c:\Users\samyuktha\OneDrive\Documents\torqwings studio v2\exports\fixed_wing_report\FixedWing_SURVEY_Engineering_Report.md"
    raw_doc = Path(spec_path).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")

    result = generate_aircraft_from_spec(spec)
    assert len(result.structural_components) == 48

    profile = create_prototype_manufacturing_profile("FW007_Prototype_Profile")
    classifier = ManufacturingClassifier(profile)

    mfg_parts = classifier.classify_structural_assembly(result.structural_components)
    assert len(mfg_parts) == 48

    val_errors = ManufacturingClassificationValidator.validate(
        mfg_parts, profile, result.structural_components
    )
    assert val_errors == [], f"Validation errors: {val_errors}"

    part_ids = [p.part_id for p in mfg_parts]
    assert len(set(part_ids)) == 48

    laser_parts = [p for p in mfg_parts if p.manufacturing_process == ManufacturingProcess.LASER_CUT]
    print_parts = [p for p in mfg_parts if p.manufacturing_process == ManufacturingProcess.THREE_D_PRINT]
    assert len(laser_parts) == 47
    assert len(print_parts) == 1


def test_unknown_component_classification():
    """Verify that unsupported structural types remain visible as REVIEW_REQUIRED."""
    class DummySolid:
        def __init__(self, label: str):
            self.label = label
            self.name = label

    unknown_comp = DummySolid("LandingGear_Custom_Strut_001")
    profile = create_prototype_manufacturing_profile()
    classifier = ManufacturingClassifier(profile)

    part = classifier.classify_structural_component(unknown_comp)
    assert part.manufacturing_process == ManufacturingProcess.UNKNOWN
    assert part.status == ManufacturingStatus.REVIEW_REQUIRED.value
    assert part.classification_rule == ClassificationRule.UNSUPPORTED_TYPE.value
    assert part.fabrication_strategy == FabricationStrategy.REVIEW_REQUIRED


def test_fw_007_fabrication_geometry_and_joints():
    """Verify Phase 6C 2D/3D fabrication geometry generation and structural tab/slot joint extraction."""
    spec_path = r"c:\Users\samyuktha\OneDrive\Documents\torqwings studio v2\exports\fixed_wing_report\FixedWing_SURVEY_Engineering_Report.md"
    raw_doc = Path(spec_path).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")

    result = generate_aircraft_from_spec(spec)
    profile = create_prototype_manufacturing_profile("FW007_Fabrication_Profile")
    
    classifier = ManufacturingClassifier(profile)
    parts = classifier.classify_structural_assembly(result.structural_components)

    generator = FabricationGeometryGenerator(profile)
    fab_geometries, joints = generator.generate_fabrication_geometries(parts, result.structural_components)

    assert len(fab_geometries) == 48
    assert len(joints) == 69  # 40 wing rib-spar + 6 HT rib-spar + 3 VT rib-spar + 20 former-longeron

    errors = FabricationGeometryValidator.validate(fab_geometries, joints, result.structural_components)
    assert errors == [], f"Fabrication validation errors: {errors}"


def test_synthetic_kerf_compensation():
    """Verify outer profile expansion (+K/2) and inner hole contraction (-K/2) on a test square."""
    with BuildSketch() as s:
        Rectangle(100.0, 100.0)
        Rectangle(50.0, 50.0, mode=Mode.SUBTRACT)

    face = s.sketch.faces()[0]
    dummy_geom = FabricationGeometry(
        fabrication_geometry_id="FAB_TEST_SQUARE",
        part_id="TEST-SQUARE",
        source_structural_component_id="Test_Square_001",
        geometry_type=FabricationStrategy.SECTION_PROFILE,
        plane="XY",
        dimensions=(100.0, 3.0, 100.0),
        boundary_2d=face
    )

    kerf = 0.20  # 0.20 mm kerf -> half-kerf = 0.10 mm
    comp_shape, rec = KerfCompensator.compensate(dummy_geom, kerf)

    assert rec.status == "VALID"
    assert rec.kerf == 0.20
    assert rec.outer_offset == 0.10
    assert rec.inner_offset == -0.10
    assert rec.compensated_dimensions[0] == 100.20
    assert rec.compensated_dimensions[2] == 100.20


def test_fw_007_laser_manufacturing_output(tmp_path):
    """Verify Phase 6D complete end-to-end laser output: kerf compensation, DXF/SVG generation, nesting, and manifest."""
    spec_path = r"c:\Users\samyuktha\OneDrive\Documents\torqwings studio v2\exports\fixed_wing_report\FixedWing_SURVEY_Engineering_Report.md"
    raw_doc = Path(spec_path).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")

    result = generate_aircraft_from_spec(spec)
    profile = create_prototype_manufacturing_profile("FW007_Laser_Profile")
    profile.laser_cut.kerf = 0.15

    manifest, sheets, kerf_records = generate_laser_manufacturing_pipeline(
        aircraft_id="FW-007",
        profile=profile,
        structural_components=result.structural_components,
        output_dir=tmp_path
    )

    # 1. Manifest verification
    assert manifest["aircraft_id"] == "FW-007"
    assert manifest["summary"]["laser_cut_count"] == 47
    assert manifest["summary"]["three_d_print_count"] == 1
    assert manifest["summary"]["total_sheets"] == len(sheets)
    assert len(sheets) > 0

    # 2. Kerf records verification
    assert len(kerf_records) == 47
    for k in kerf_records:
        assert k.kerf == 0.15
        assert k.outer_offset == 0.075
        assert k.inner_offset == -0.075

    # 3. DXF and SVG files exist and are valid
    parts_dir = tmp_path / "FW-007_manufacturing" / "parts"
    sheets_dir = tmp_path / "FW-007_manufacturing" / "sheets"
    manifest_file = tmp_path / "FW-007_manufacturing" / "manufacturing_manifest.json"

    assert manifest_file.exists()
    assert manifest_file.stat().st_size > 500

    sample_ids = ["RIB-L-001", "RIB-R-001", "SPAR-L-MAIN", "FMR-000", "FIREWALL-001"]
    for pid in sample_ids:
        dxf_f = parts_dir / f"{pid}.dxf"
        svg_f = parts_dir / f"{pid}.svg"
        assert dxf_f.exists(), f"Missing DXF for {pid}"
        assert dxf_f.stat().st_size > 0
        assert svg_f.exists(), f"Missing SVG for {pid}"
        assert svg_f.stat().st_size > 0

    # 4. Sheets verification
    for s in sheets:
        s_dxf = sheets_dir / f"{s.sheet_id}.dxf"
        s_svg = sheets_dir / f"{s.sheet_id}.svg"
        assert s_dxf.exists()
        assert s_svg.exists()
        assert s.utilization > 0.0
        assert len(s.parts) > 0


def test_nesting_repeatability():
    """Verify that repeated nesting runs produce identical sheet assignments and placement coordinates."""
    spec_path = r"c:\Users\samyuktha\OneDrive\Documents\torqwings studio v2\exports\fixed_wing_report\FixedWing_SURVEY_Engineering_Report.md"
    raw_doc = Path(spec_path).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")
    result = generate_aircraft_from_spec(spec)

    profile = create_prototype_manufacturing_profile()
    classifier = ManufacturingClassifier(profile)
    parts = classifier.classify_structural_assembly(result.structural_components)

    gen = FabricationGeometryGenerator(profile)
    fab_geometries, _ = gen.generate_fabrication_geometries(parts, result.structural_components)

    nester = SheetNester(profile.laser_cut)
    sheets1 = nester.nest_parts(parts, fab_geometries)
    sheets2 = nester.nest_parts(parts, fab_geometries)

    assert len(sheets1) == len(sheets2)
    for s1, s2 in zip(sheets1, sheets2):
        assert s1.sheet_id == s2.sheet_id
        assert s1.utilization == s2.utilization
        assert len(s1.parts) == len(s2.parts)
        for p1, p2 in zip(s1.parts, s2.parts):
            assert p1.part_id == p2.part_id
            assert p1.x == p2.x
            assert p1.y == p2.y
            assert p1.rotation == p2.rotation


def test_second_aircraft_laser_manufacturing(tmp_path):
    """Verify generic laser manufacturing pipeline on parameterized second aircraft."""
    spec_path = r"c:\Users\samyuktha\OneDrive\Documents\torqwings studio v2\exports\fixed_wing_report\FixedWing_SURVEY_Engineering_Report.md"
    raw_doc = Path(spec_path).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")

    spec.wing.span.value = 1600.0
    spec.fuselage.length.value = 1200.0

    result = generate_aircraft_from_spec(spec)
    profile = create_prototype_manufacturing_profile("Second_Aircraft_Laser_Profile")

    manifest, sheets, kerf_records = generate_laser_manufacturing_pipeline(
        aircraft_id="FW-008-PARAM",
        profile=profile,
        structural_components=result.structural_components,
        output_dir=tmp_path
    )

    assert manifest["aircraft_id"] == "FW-008-PARAM"
    assert len(sheets) > 0
    laser_comp_count = len([c for c in result.structural_components if "Attachment" not in getattr(c, "label", getattr(c, "name", ""))])
    assert len(kerf_records) == laser_comp_count


def test_second_profile_does_not_modify_geometry():
    """Verify that changing manufacturing profile settings does NOT alter Phase 5 CAD geometry."""
    spec_path = r"c:\Users\samyuktha\OneDrive\Documents\torqwings studio v2\exports\fixed_wing_report\FixedWing_SURVEY_Engineering_Report.md"
    raw_doc = Path(spec_path).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")

    result = generate_aircraft_from_spec(spec)
    initial_volume = result.assembly.volume
    initial_struct_count = len(result.structural_components)

    profile_a = create_prototype_manufacturing_profile("Profile_A_Balsa")
    profile_b = create_prototype_manufacturing_profile("Profile_B_Aeroply")
    profile_b.wing_rib_material = "Aeroply_3mm"
    profile_b.laser_cut.thickness = 5.0

    classifier_a = ManufacturingClassifier(profile_a)
    classifier_b = ManufacturingClassifier(profile_b)

    parts_a = classifier_a.classify_structural_assembly(result.structural_components)
    parts_b = classifier_b.classify_structural_assembly(result.structural_components)

    assert result.assembly.volume == initial_volume
    assert len(result.structural_components) == initial_struct_count == 48
    assert next(p for p in parts_a if p.part_id == "RIB-L-000").material == "Balsa_3mm"
    assert next(p for p in parts_b if p.part_id == "RIB-L-000").material == "Aeroply_3mm"


# ==============================================================================
# PHASE 6E TESTS — 3D PRINT MANUFACTURING OUTPUT, ENVELOPE, SPLIT, STL
# ==============================================================================

def test_fw_007_printable_solid_validation_and_stl_export(tmp_path):
    """Verify Phase 6E extraction of 3D-print component, build volume check, and STL export."""
    spec_path = r"c:\Users\samyuktha\OneDrive\Documents\torqwings studio v2\exports\fixed_wing_report\FixedWing_SURVEY_Engineering_Report.md"
    raw_doc = Path(spec_path).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")

    result = generate_aircraft_from_spec(spec)
    profile = create_prototype_manufacturing_profile("FW007_3DPrint_Profile")

    manifest, printable_parts, split_records = generate_3d_print_manufacturing_pipeline(
        aircraft_id="FW-007",
        profile=profile,
        structural_components=result.structural_components,
        output_dir=tmp_path
    )

    # 1. 3D Print Part Selection
    assert len(printable_parts) == 1
    part = printable_parts[0]
    assert part.print_part_id == "PRINT-WING-ATTACH-001"
    assert part.source_structural_component_id == "Wing_Fuselage_Attachment"
    assert part.print_status == PrintStatus.EXPORTED.value
    assert part.material == "PLA_Standard"

    # 2. Build Envelope Fit
    bed_x, bed_y, bed_z = profile.three_d_print.printer_bed_x, profile.three_d_print.printer_bed_y, profile.three_d_print.printer_bed_z
    dx, dy, dz = part.original_dimensions
    assert dx <= bed_x and dy <= bed_y and dz <= bed_z
    assert len(split_records) == 0

    # 3. STL File Validation
    stl_path = Path(part.output_stl_path)
    assert stl_path.exists()
    assert stl_path.stat().st_size > 0

    # Round-trip verification
    imported = import_stl(str(stl_path))
    imp_bb = imported.bounding_box()
    assert abs(imp_bb.size.X - dx) < 0.1
    assert abs(imp_bb.size.Y - dy) < 0.1
    assert abs(imp_bb.size.Z - dz) < 0.1


def test_synthetic_oversized_part_splitting_and_joints(tmp_path):
    """Verify deterministic splitting, alignment pin/socket creation, and virtual reassembly on oversized part."""
    # Synthetic oversized beam: 300 x 100 x 100 mm on a 220 x 220 x 250 mm printer
    beam = Box(300.0, 100.0, 100.0)
    profile = get_prototype_3d_print_profile()
    profile.printer_bed_x = 220.0
    profile.printer_bed_y = 220.0
    profile.printer_bed_z = 250.0
    profile.joint_clearance = 0.2

    oversized_part = PrintablePart(
        print_part_id="PRINT-SYNTH-MOUNT-001",
        source_manufacturing_part_id="MOUNT-001",
        source_structural_component_id="Synthetic_Motor_Mount",
        source_fabrication_geometry_id="FAB_MOUNT_001",
        geometry=beam,
        process=ManufacturingProcess.THREE_D_PRINT,
        material="PLA_Standard",
        printer_profile=profile,
        original_dimensions=(300.0, 100.0, 100.0),
        print_dimensions=(300.0, 100.0, 100.0),
        print_status=PrintStatus.READY.value
    )

    children, split_records = PartSplitter.split_part(oversized_part, profile)

    # 1. Splitting verification
    assert len(children) == 2
    assert len(split_records) == 1

    rec = split_records[0]
    assert rec.parent_print_part_id == "PRINT-SYNTH-MOUNT-001"
    assert rec.split_axis == "X"
    assert rec.split_rule == "PRINTER_ENVELOPE_SPLIT"
    assert rec.joint_type == SplitJointType.ALIGNMENT_PIN_SOCKET.value
    assert rec.clearance == 0.2
    assert rec.status == "VALID"

    child_a, child_b = children[0], children[1]
    assert child_a.print_part_id == "PRINT-SYNTH-MOUNT-001-A"
    assert child_b.print_part_id == "PRINT-SYNTH-MOUNT-001-B"
    assert child_a.split_parent == "PRINT-SYNTH-MOUNT-001"
    assert child_b.split_parent == "PRINT-SYNTH-MOUNT-001"

    # 2. Child build envelope fit
    assert child_a.geometry.bounding_box().size.X <= profile.printer_bed_x
    assert child_b.geometry.bounding_box().size.X <= profile.printer_bed_x

    # 3. Virtual reassembly check
    assert rec.reassembled_dimensions == (300.0, 100.0, 100.0)
    assert rec.reassembly_volume_diff_pct < 1.0

    # 4. STL export on both children
    stl_a = tmp_path / f"{child_a.print_part_id}.stl"
    stl_b = tmp_path / f"{child_b.print_part_id}.stl"

    ThreeDPrintExporter.export_stl(child_a, stl_a)
    ThreeDPrintExporter.export_stl(child_b, stl_b)

    assert stl_a.exists() and stl_a.stat().st_size > 0
    assert stl_b.exists() and stl_b.stat().st_size > 0


def test_3d_print_profile_variation():
    """Verify that printer profile bed size dictates whether splitting is required."""
    beam = Box(300.0, 100.0, 100.0)
    
    # Small printer profile (220mm) -> Requires split
    prof_small = get_prototype_3d_print_profile()
    prof_small.printer_bed_x = 220.0

    # Large printer profile (400mm) -> Fits directly
    prof_large = get_prototype_3d_print_profile()
    prof_large.printer_bed_x = 400.0

    part_small = PrintablePart(
        print_part_id="PRINT-TEST-001",
        source_manufacturing_part_id="TEST-001",
        source_structural_component_id="Test_Part",
        source_fabrication_geometry_id="FAB_001",
        geometry=beam,
        printer_profile=prof_small,
        original_dimensions=(300.0, 100.0, 100.0)
    )

    children_small, splits_small = PartSplitter.split_part(part_small, prof_small)
    assert len(children_small) == 2
    assert len(splits_small) == 1

    # Large printer check
    bb = beam.bounding_box()
    assert bb.size.X <= prof_large.printer_bed_x
    assert bb.size.Y <= prof_large.printer_bed_y
    assert bb.size.Z <= prof_large.printer_bed_z


def test_3d_print_material_variation():
    """Verify that changing 3D print material updates metadata without modifying geometry."""
    spec_path = r"c:\Users\samyuktha\OneDrive\Documents\torqwings studio v2\exports\fixed_wing_report\FixedWing_SURVEY_Engineering_Report.md"
    raw_doc = Path(spec_path).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")

    result = generate_aircraft_from_spec(spec)
    
    prof_pla = create_prototype_manufacturing_profile("PLA_Profile")
    prof_petg = create_prototype_manufacturing_profile("PETG_Profile")
    prof_petg.attachment_material = "PETG_Standard"
    prof_petg.three_d_print.material = "PETG"

    p_gen_pla = PrintablePartGenerator(prof_pla)
    p_gen_petg = PrintablePartGenerator(prof_petg)

    classifier_pla = ManufacturingClassifier(prof_pla)
    classifier_petg = ManufacturingClassifier(prof_petg)

    parts_pla = classifier_pla.classify_structural_assembly(result.structural_components)
    parts_petg = classifier_petg.classify_structural_assembly(result.structural_components)

    fab_pla, _ = FabricationGeometryGenerator(prof_pla).generate_fabrication_geometries(parts_pla, result.structural_components)
    fab_petg, _ = FabricationGeometryGenerator(prof_petg).generate_fabrication_geometries(parts_petg, result.structural_components)

    p_pla, _ = p_gen_pla.generate_printable_parts(parts_pla, fab_pla, result.structural_components)
    p_petg, _ = p_gen_petg.generate_printable_parts(parts_petg, fab_petg, result.structural_components)

    assert p_pla[0].material == "PLA_Standard"
    assert p_petg[0].material == "PETG_Standard"
    assert p_pla[0].original_dimensions == p_petg[0].original_dimensions


def test_3d_print_repeatability():
    """Verify that repeated 3D print pipeline runs produce identical part IDs, splits, and bounding boxes."""
    spec_path = r"c:\Users\samyuktha\OneDrive\Documents\torqwings studio v2\exports\fixed_wing_report\FixedWing_SURVEY_Engineering_Report.md"
    raw_doc = Path(spec_path).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")
    result = generate_aircraft_from_spec(spec)

    profile = create_prototype_manufacturing_profile()
    classifier = ManufacturingClassifier(profile)
    parts = classifier.classify_structural_assembly(result.structural_components)
    fab_geoms, _ = FabricationGeometryGenerator(profile).generate_fabrication_geometries(parts, result.structural_components)

    p_gen = PrintablePartGenerator(profile)
    p1, s1 = p_gen.generate_printable_parts(parts, fab_geoms, result.structural_components)
    p2, s2 = p_gen.generate_printable_parts(parts, fab_geoms, result.structural_components)

    assert len(p1) == len(p2)
    assert len(s1) == len(s2)
    for part1, part2 in zip(p1, p2):
        assert part1.print_part_id == part2.print_part_id
        assert part1.original_dimensions == part2.original_dimensions
        assert part1.print_status == part2.print_status


# ==============================================================================
# PHASE 6F TESTS — MANUFACTURING VALIDATION, BOM & VIRTUAL REASSEMBLY
# ==============================================================================

def test_manufacturing_bom_generation():
    """Verify machine-readable BOM generation with accurate parts, materials, mass, and outputs."""
    spec_path = r"c:\Users\samyuktha\OneDrive\Documents\torqwings studio v2\exports\fixed_wing_report\FixedWing_SURVEY_Engineering_Report.md"
    raw_doc = Path(spec_path).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")
    result = generate_aircraft_from_spec(spec)

    profile = create_prototype_manufacturing_profile()
    classifier = ManufacturingClassifier(profile)
    parts = classifier.classify_structural_assembly(result.structural_components)
    fab_geoms, joints = FabricationGeometryGenerator(profile).generate_fabrication_geometries(parts, result.structural_components)
    sheets = SheetNester(profile.laser_cut).nest_parts(parts, fab_geoms)
    p_gen = PrintablePartGenerator(profile)
    printable_parts, _ = p_gen.generate_printable_parts(parts, fab_geoms, result.structural_components)

    bom = ManufacturingValidationEngine.generate_manufacturing_bom(
        aircraft_id="FW-007",
        profile=profile,
        parts=parts,
        joints=joints,
        sheets=sheets,
        printable_parts=printable_parts
    )

    assert bom.aircraft_id == "FW-007"
    assert bom.total_parts == 48
    assert bom.total_joints == 69
    assert bom.total_sheets == 3
    assert bom.laser_cut_count == 47
    assert bom.three_d_print_count == 1
    assert "Balsa_3mm" in bom.materials_summary
    assert "Aeroply_3mm" in bom.materials_summary
    assert "PLA_Standard" in bom.materials_summary
    assert len(bom.parts) == 48


def test_fw_007_full_manufacturing_validation_and_reassembly(tmp_path):
    """Verify complete Phase 6F validation audit, virtual prototype reassembly, and readiness determination on FW-007."""
    spec_path = r"c:\Users\samyuktha\OneDrive\Documents\torqwings studio v2\exports\fixed_wing_report\FixedWing_SURVEY_Engineering_Report.md"
    raw_doc = Path(spec_path).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")
    result = generate_aircraft_from_spec(spec)
    profile = create_prototype_manufacturing_profile("FW007_Production_Profile")

    # Generate files first
    generate_complete_manufacturing_pipeline("FW-007", profile, result.structural_components, output_dir=tmp_path)

    # Run Phase 6F validation
    val_res = ManufacturingValidationEngine.run_full_validation(
        aircraft_id="FW-007",
        profile=profile,
        structural_components=result.structural_components,
        structural_assembly=result.structural_assembly,
        spec=spec,
        output_dir=tmp_path
    )

    # 1. Statuses
    assert val_res.overall_status == "PASS"
    assert val_res.prototype_readiness == "READY"
    assert val_res.completeness_status == "PASS"
    assert val_res.traceability_status == "PASS"
    assert val_res.laser_status == "PASS"
    assert val_res.printing_status == "PASS"
    assert val_res.joints_status == "PASS"
    assert val_res.dimensions_status == "PASS"
    assert val_res.symmetry_status == "PASS"
    assert val_res.bays_status == "PASS"
    assert val_res.propulsion_status == "PASS"
    assert val_res.reassembly_status == "PASS"
    assert len(val_res.errors) == 0

    # 2. Dimensional comparison check
    assert len(val_res.dimensional_comparison) >= 5
    span_entry = next(d for d in val_res.dimensional_comparison if d["parameter"] == "Wingspan")
    assert span_entry["result"] == "PASS"
    assert span_entry["virtual_manufacturing"] == "2000.0 mm"

    fuse_entry = next(d for d in val_res.dimensional_comparison if d["parameter"] == "Fuselage Length")
    assert fuse_entry["result"] == "PASS"
    assert fuse_entry["virtual_manufacturing"] == "1500.0 mm"

    # 3. Validation report JSON file existence
    val_json = tmp_path / "FW-007_manufacturing" / "manufacturing_validation.json"
    assert val_json.exists()
    data = json.loads(val_json.read_text(encoding="utf-8"))
    assert data["aircraft_id"] == "FW-007"
    assert data["prototype_readiness"] == "READY"
    assert data["inventory"]["structural_components"] == 48
    assert data["inventory"]["manufacturing_parts"] == 48


def test_parameterized_aircraft_full_manufacturing_validation(tmp_path):
    """Verify Phase 6F validation dynamically adapts to scaled parameterized aircraft."""
    spec_path = r"c:\Users\samyuktha\OneDrive\Documents\torqwings studio v2\exports\fixed_wing_report\FixedWing_SURVEY_Engineering_Report.md"
    raw_doc = Path(spec_path).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")

    spec.wing.span.value = 1600.0
    spec.fuselage.length.value = 1200.0

    result = generate_aircraft_from_spec(spec)
    profile = create_prototype_manufacturing_profile("Param_Profile")

    generate_complete_manufacturing_pipeline("FW-008-PARAM", profile, result.structural_components, output_dir=tmp_path)

    val_res = ManufacturingValidationEngine.run_full_validation(
        aircraft_id="FW-008-PARAM",
        profile=profile,
        structural_components=result.structural_components,
        structural_assembly=result.structural_assembly,
        spec=spec,
        output_dir=tmp_path
    )

    assert val_res.overall_status == "PASS"
    assert val_res.prototype_readiness == "READY"
    span_entry = next(d for d in val_res.dimensional_comparison if d["parameter"] == "Wingspan")
    assert span_entry["virtual_manufacturing"] == "1600.0 mm"
    fuse_entry = next(d for d in val_res.dimensional_comparison if d["parameter"] == "Fuselage Length")
    assert fuse_entry["virtual_manufacturing"] == "1200.0 mm"


def test_intentional_failure_missing_part(tmp_path):
    """Verify that removing a required manufacturing output correctly produces a FAIL."""
    spec_path = r"c:\Users\samyuktha\OneDrive\Documents\torqwings studio v2\exports\fixed_wing_report\FixedWing_SURVEY_Engineering_Report.md"
    raw_doc = Path(spec_path).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")
    result = generate_aircraft_from_spec(spec)
    profile = create_prototype_manufacturing_profile()

    generate_complete_manufacturing_pipeline("FW-FAIL-MISSING", profile, result.structural_components, output_dir=tmp_path)

    # Intentionally delete one DXF
    dxf_to_delete = tmp_path / "FW-FAIL-MISSING_manufacturing" / "parts" / "RIB-L-001.dxf"
    if dxf_to_delete.exists():
        dxf_to_delete.unlink()

    val_res = ManufacturingValidationEngine.run_full_validation(
        aircraft_id="FW-FAIL-MISSING",
        profile=profile,
        structural_components=result.structural_components,
        structural_assembly=result.structural_assembly,
        spec=spec,
        output_dir=tmp_path
    )

    assert val_res.overall_status == "FAIL"
    assert val_res.prototype_readiness == "NOT_READY"
    assert any("MISSING_OUTPUT_FILE" in err for err in val_res.errors)


def test_intentional_failure_broken_traceability(tmp_path):
    """Verify that an invalid source structural ID correctly produces a TRACEABILITY_ERROR."""
    class DummySolid:
        def __init__(self, label: str):
            self.label = label
            self.name = label

    dummy_parts = [
        ManufacturingPart(
            part_id="ORPHAN-PART-001",
            source_structural_component_id="NON_EXISTENT_SOLID",
            component_type="RIB",
            manufacturing_process=ManufacturingProcess.LASER_CUT,
            material="Balsa_3mm"
        )
    ]
    struct_comps = [DummySolid("Real_Solid_001")]

    stat, errors = ManufacturingValidationEngine.validate_traceability("TEST-AIRCRAFT", struct_comps, dummy_parts, [], output_dir=tmp_path)
    assert stat == "FAIL"
    assert any("TRACEABILITY_ERROR" in err for err in errors)


def test_intentional_failure_dimension_mismatch():
    """Verify that virtual assembly dimensional drift beyond tolerance produces a DIMENSION_MISMATCH."""
    spec_path = r"c:\Users\samyuktha\OneDrive\Documents\torqwings studio v2\exports\fixed_wing_report\FixedWing_SURVEY_Engineering_Report.md"
    raw_doc = Path(spec_path).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")

    drifted_virtual_assembly = VirtualManufacturingAssembly(
        aircraft_id="FW-DRIFT",
        critical_dimensions={
            "wingspan": 1950.0,  # 50 mm deviation from 2000.0 mm
            "fuselage_length": 1500.0,
            "height": 400.0,
            "volume": 500000.0
        }
    )

    stat, table, errors = ManufacturingValidationEngine.validate_dimensions_and_reassembly(None, drifted_virtual_assembly, spec)
    assert stat == "FAIL"
    assert any("DIMENSION_MISMATCH" in err for err in errors)
    span_row = next(r for r in table if r["parameter"] == "Wingspan")
    assert span_row["result"] == "FAIL"


def test_intentional_failure_bay_blockage():
    """Verify that degenerate former volumes produce a BAY_BLOCKED error."""
    class DummyFormer:
        def __init__(self, label: str, volume: float):
            self.label = label
            self.name = label
            self.volume = volume

    blocked_formers = [
        DummyFormer("Fuselage_Former_000", volume=0.0),
        DummyFormer("Fuselage_Former_001", volume=100.0),
    ]

    stat, errors = ManufacturingValidationEngine.validate_bays(blocked_formers, None, None)
    assert stat == "FAIL"
    assert any("BAY_BLOCKED" in err for err in errors)


def test_phase6f_validation_repeatability(tmp_path):
    """Verify that repeated validation runs on the same aircraft yield identical audit results."""
    spec_path = r"c:\Users\samyuktha\OneDrive\Documents\torqwings studio v2\exports\fixed_wing_report\FixedWing_SURVEY_Engineering_Report.md"
    raw_doc = Path(spec_path).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")
    result = generate_aircraft_from_spec(spec)
    profile = create_prototype_manufacturing_profile()

    generate_complete_manufacturing_pipeline("FW-REPEAT", profile, result.structural_components, output_dir=tmp_path)

    res1 = ManufacturingValidationEngine.run_full_validation("FW-REPEAT", profile, result.structural_components, result.structural_assembly, spec, output_dir=tmp_path)
    res2 = ManufacturingValidationEngine.run_full_validation("FW-REPEAT", profile, result.structural_components, result.structural_assembly, spec, output_dir=tmp_path)

    assert res1.overall_status == res2.overall_status
    assert res1.prototype_readiness == res2.prototype_readiness
    assert len(res1.errors) == len(res2.errors)
    assert res1.inventory == res2.inventory
    assert res1.dimensional_comparison == res2.dimensional_comparison

