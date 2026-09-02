"""Integration tests for the specifications to CAD generation flow."""

from __future__ import annotations

import os
import tempfile
import re
from pathlib import Path
import pytest

from cadpy.requirements import parse_aircraft_specification
from cadpy.aircraft import generate_aircraft_from_spec, CADGenerationResult

# Path to the SURVEY engineering report markdown
SPEC_PATH = r"c:\Users\samyuktha\OneDrive\Documents\torqwings studio v2\exports\fixed_wing_report\FixedWing_SURVEY_Engineering_Report.md"


def test_fw_007_complete_generation():
    """Verify end-to-end CAD structural generation from the actual SURVEY report markdown."""
    assert os.path.exists(SPEC_PATH), f"FW-007 spec file missing at: {SPEC_PATH}"

    # 1. Ingest/Parse the spec
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")

    # 2. Generate CAD using translation layer
    result = generate_aircraft_from_spec(spec)
    assert isinstance(result, CADGenerationResult)

    # 3. Verify manifest contents
    manifest = result.manifest
    assert manifest is not None
    assert manifest["case_id"] == "Fixed-Wing UAV Engineering Report \u2014 SURVEY Mission"
    assert "wing_span" in manifest["parameters"]
    assert manifest["parameters"]["wing_span"]["value"] == 2000.0
    assert manifest["parameters"]["wing_span"]["status"] == "EXPLICIT"

    # 4. Verify assembly volume & non-degenerate fuselage
    shape = result.assembly
    assert shape.volume > 0

    fuselage = next(c for c in shape.children if "fuselage" in getattr(c, "label", ""))
    assert fuselage.bounding_box().size.Z > 1.0  # Verify non-degenerate Z dimension
    assert fuselage.volume > 1e6  # Verify volumetric solid fuselage

    # Verify exact fuselage bounding box against explicit Part 1 specification
    assert abs(fuselage.bounding_box().size.X - spec.fuselage.length.value) < 1.0
    assert abs(fuselage.bounding_box().size.Y - spec.fuselage.width.value) < 1.0
    assert abs(fuselage.bounding_box().size.Z - spec.fuselage.height.value) < 1.0

    # 5. Verify dimensional validation check table
    assert hasattr(result, "dimensional_validation")
    overall_span_check = next(d for d in result.dimensional_validation if d["parameter"] == "overall wing span")
    assert overall_span_check["result"] == "PASS"
    assert overall_span_check["required"] == 2000.0
    assert abs(overall_span_check["generated"] - 2000.0) < 1.0

    # 6. Verify source -> parsed -> manifest -> CAD geometry traceability assertion chain
    span_match = re.search(r"\*\*\s*Wingspan\s*\*\*\s*:\s*(\d+(?:\.\d+)?)\s*meters", raw_doc, re.IGNORECASE)
    assert span_match is not None
    source_wing_span_meters = float(span_match.group(1))
    source_wing_span_mm = source_wing_span_meters * 1000.0

    parsed_wing_span = spec.wing.span.value
    manifest_wing_span = manifest["parameters"]["wing_span"]["value"]
    left_wing = next(c for c in shape.children if "left_wing" in getattr(c, "label", ""))
    right_wing = next(c for c in shape.children if "right_wing" in getattr(c, "label", ""))
    generated_wing_span = right_wing.bounding_box().max.Y - left_wing.bounding_box().min.Y

    assert source_wing_span_mm == 2000.0
    assert parsed_wing_span == source_wing_span_mm
    assert manifest_wing_span == parsed_wing_span
    assert abs(generated_wing_span - manifest_wing_span) < 1.0

    # 7. Check exported STEP path and content
    assert "step" in result.output_files
    step_path = result.output_files["step"]
    assert os.path.exists(step_path)
    assert os.path.getsize(step_path) > 0
    step_content = Path(step_path).read_text(encoding="utf-8", errors="ignore")

    # 8. Assert structural synthesis outputs - Exactly 48 structural solids
    assert len(result.structural_components) == 48, f"Expected 48 structural components, got {len(result.structural_components)}"
    struct_labels = [c.label for c in result.structural_components]
    assert len(set(struct_labels)) == 48, "Duplicate structural component labels detected!"

    # Breakdown verification:
    # 24 Wing parts
    assert "MainWing_Left_MainSpar" in struct_labels
    assert "MainWing_Left_RearSpar" in struct_labels
    for i in range(10):
        assert f"MainWing_Left_Rib_{i:03d}" in struct_labels
    assert "MainWing_Right_MainSpar" in struct_labels
    assert "MainWing_Right_RearSpar" in struct_labels
    for i in range(10):
        assert f"MainWing_Right_Rib_{i:03d}" in struct_labels

    # 12 Fuselage parts
    for i in range(6):
        assert f"Fuselage_Former_{i:03d}" in struct_labels
    assert "Fuselage_Longeron_UpperLeft" in struct_labels
    assert "Fuselage_Longeron_UpperRight" in struct_labels
    assert "Fuselage_Longeron_LowerLeft" in struct_labels
    assert "Fuselage_Longeron_LowerRight" in struct_labels
    assert "Motor_Firewall" in struct_labels
    assert "Wing_Fuselage_Attachment" in struct_labels

    # 8 Horizontal Tail parts
    assert "HorizontalTail_Left_Spar" in struct_labels
    assert "HorizontalTail_Right_Spar" in struct_labels
    for i in range(3):
        assert f"HorizontalTail_Left_Rib_{i:03d}" in struct_labels
        assert f"HorizontalTail_Right_Rib_{i:03d}" in struct_labels

    # 4 Vertical Tail parts
    assert "VerticalTail_MainSpar" in struct_labels
    for i in range(3):
        assert f"VerticalTail_Rib_{i:03d}" in struct_labels

    # Ensure structural components are actual 3D solids with positive volume and bounding box
    for comp in result.structural_components:
        assert comp.volume > 0.0, f"Component {comp.label} has zero/negative volume: {comp.volume}"
        bbox = comp.bounding_box()
        assert bbox.size.X > 0.0, f"Component {comp.label} degenerate in X"
        assert bbox.size.Y > 0.0, f"Component {comp.label} degenerate in Y"
        assert bbox.size.Z > 0.0, f"Component {comp.label} degenerate in Z"

    # Verify Wing-Fuselage Attachment has positive volume in normal pipeline
    wing_attach = next(c for c in result.structural_components if c.label == "Wing_Fuselage_Attachment")
    assert wing_attach.volume > 1000.0, f"Wing attachment volume too low: {wing_attach.volume}"

    # Verify internal bay envelopes
    payload_bay = next(c for c in shape.children if "payload_envelope" in getattr(c, "label", ""))
    p_box = payload_bay.bounding_box()
    assert abs(p_box.size.X - 200.0) < 1.0, f"Payload length mismatch: {p_box.size.X}"
    assert abs(p_box.size.Y - 150.0) < 1.0, f"Payload width mismatch: {p_box.size.Y}"
    assert abs(p_box.size.Z - 150.0) < 1.0, f"Payload height mismatch: {p_box.size.Z}"

    # Check structural manifest details and reference material classification
    struct_profile = manifest["structural_profile"]
    assert struct_profile["estimated_structural_mass_g"]["value"] > 0
    assert struct_profile["estimated_structural_mass_g"]["source"] == "DERIVED"
    assert struct_profile["reference_material_density_g_mm3"]["source"] == "REFERENCE_MATERIAL"
    assert len(struct_profile["structural_cg_location"]["value"]) == 3


def test_unsupported_airfoil():
    """Verify that an unsupported airfoil raises a clean ValueError."""
    assert os.path.exists(SPEC_PATH), f"FW-007 spec file missing at: {SPEC_PATH}"

    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")

    # Inject an unsupported airfoil
    spec.wing.root_airfoil.value = "MH32"
    spec.wing.root_airfoil.status = "EXPLICIT"

    with pytest.raises(ValueError) as excinfo:
        generate_aircraft_from_spec(spec)
    assert "Unsupported airfoil" in str(excinfo.value)


def test_unsupported_tail_configuration():
    """Verify that an unsupported tail configuration raises a clean ValueError."""
    assert os.path.exists(SPEC_PATH), f"FW-007 spec file missing at: {SPEC_PATH}"

    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")

    # Inject an unsupported tail configuration
    spec.configuration.tail_configuration.value = "V-tail"
    spec.configuration.tail_configuration.status = "EXPLICIT"

    with pytest.raises(ValueError) as excinfo:
        generate_aircraft_from_spec(spec)
    assert "Unsupported tail configuration" in str(excinfo.value)


def test_non_cad_blocking_conflict():
    """Verify that a non-CAD-blocking conflict (e.g. MTOW) does NOT prevent generation."""
    assert os.path.exists(SPEC_PATH), f"FW-007 spec file missing at: {SPEC_PATH}"

    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")

    # Inject a conflicting non-geometry performance target in spec conflicts
    spec.conflicts.append("Conflict detected for takeoff mass: [5.5, 6.0]")

    # Run generation - should succeed but include validation warnings
    result = generate_aircraft_from_spec(spec)
    assert isinstance(result, CADGenerationResult)
    assert result.assembly.volume > 0
    assert any("takeoff mass" in err for err in result.validation_errors)
    assert len(result.cad_blocking_errors) == 0
    assert len(result.non_cad_blocking_errors) > 0


def test_parameterized_aircraft_structure():
    """Verify that structural synthesis scales dynamically on a second simple parameterized aircraft."""
    assert os.path.exists(SPEC_PATH), f"FW-007 spec file missing at: {SPEC_PATH}"

    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")

    # Alter parameters of simple second aircraft
    spec.wing.span.value = 1600.0  # Smaller wing span
    spec.fuselage.length.value = 1200.0  # Shorter fuselage length

    result = generate_aircraft_from_spec(spec)
    assert isinstance(result, CADGenerationResult)
    assert result.assembly.volume > 0

    left_wing = next(c for c in result.assembly.children if "left_wing" in getattr(c, "label", ""))
    right_wing = next(c for c in result.assembly.children if "right_wing" in getattr(c, "label", ""))
    span_gen = right_wing.bounding_box().max.Y - left_wing.bounding_box().min.Y
    
    # Confirm external wing span is exactly the scaled 1600.0 mm
    assert abs(span_gen - 1600.0) < 1.0

    # Verify that left wing main spar dimensions scaled correctly with half span (800 mm)
    left_main_spar = next(c for c in result.structural_components if c.label == "MainWing_Left_MainSpar")
    assert abs(left_main_spar.bounding_box().size.Y - 800.0) < 5.0
