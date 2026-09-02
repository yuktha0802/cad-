"""Unit tests for the requirements ingestion and validation layer."""

from __future__ import annotations

import os
from pathlib import Path
from cadpy.requirements import (
    parse_aircraft_specification,
    validate_aircraft_specification,
    normalize_unit,
    parse_value_and_unit,
)

# Reference paths relative to repository root
SPEC_PATH = r"c:\Users\samyuktha\OneDrive\Documents\torqwings studio v2\exports\fixed_wing_report\FixedWing_SURVEY_Engineering_Report.md"


def test_unit_normalization():
    """Verify central unit conversion to mm/degrees/kg."""
    assert normalize_unit(2.0, "m") == (2000.0, "mm")
    assert normalize_unit(15.0, "cm") == (150.0, "mm")
    assert normalize_unit(10.0, "in") == (254.0, "mm")
    assert abs(normalize_unit(3.0, "ft")[0] - 914.4) < 1e-4
    assert normalize_unit(5.0, "deg") == (5.0, "degrees")
    assert normalize_unit(500.0, "g") == (0.5, "kg")


def test_value_and_unit_parser():
    """Test text-to-value/unit splitting."""
    assert parse_value_and_unit("2.00 m") == (2.0, "m")
    assert parse_value_and_unit("250mm") == (250.0, "mm")
    assert parse_value_and_unit("12x6 APC") == ("12x6 APC", "")
    assert parse_value_and_unit("200mm x 150mm x 150mm") == ("200x150x150", "mm")


def test_fw_007_ingestion():
    """Authoritative parser test using the actual SURVEY engineering report (FW-007 spec)."""
    assert os.path.exists(SPEC_PATH), f"FW-007 spec file missing at: {SPEC_PATH}"

    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")

    # Identity
    assert "SURVEY" in spec.identity.title.value

    # Configuration
    assert spec.configuration.wing_position.value.lower() == "high wing"
    assert spec.configuration.propulsion_layout.value.lower() == "tractor"
    assert spec.configuration.tail_configuration.value.lower() == "conventional"
    assert spec.configuration.landing_gear.value.lower() == "tricycle"

    # Sourced EXPLICIT Parameters (Normalized to mm/degrees/kg)
    assert spec.wing.span.value == 2000.0  # 2.00 m -> 2000.0 mm
    assert spec.wing.span.status == "EXPLICIT"
    assert spec.wing.root_chord.value == 250.0  # 0.25 m -> 250.0 mm
    assert spec.wing.tip_chord.value == 150.0  # 0.15 m -> 150.0 mm
    assert spec.wing.dihedral.value == 2.0  # 2.0 deg -> 2.0 degrees

    assert spec.fuselage.length.value == 1500.0  # 1.50 m -> 1500.0 mm
    assert spec.fuselage.width.value == 200.0  # 0.20 m -> 200.0 mm
    assert spec.fuselage.height.value == 400.0  # 0.40 m -> 400.0 mm

    assert spec.horizontal_tail.span.value == 500.0  # 0.50 m -> 500.0 mm
    assert spec.vertical_tail.height.value == 400.0  # 0.40 m -> 400.0 mm

    # Internal Envelopes (Payload bay compartment volume 200x150x150)
    assert spec.internal_bays.payload_bay.length.value == 200.0
    assert spec.internal_bays.payload_bay.width.value == 150.0
    assert spec.internal_bays.payload_bay.height.value == 150.0

    # Propulsion and Sized Envelopes
    assert spec.propulsion.motor.value == "SunnySky X2820"
    assert spec.propulsion.propeller.value == "12x6 APC"
    # Sized/Derived propeller dimensions in mm (12 in and 6 in)
    assert abs(spec.propulsion.propeller_diameter.value - 304.8) < 1e-4
    assert abs(spec.propulsion.propeller_pitch.value - 152.4) < 1e-4

    # Sourced Masses
    assert spec.mass.MTOW.value == 5.5  # 5.50 kg
    assert spec.mass.battery_weight.value == 3.5  # 3.50 kg

    # Sized/Derived Relationships
    assert spec.wing.half_span.value == 1000.0  # span / 2
    assert spec.wing.half_span.status == "DERIVED"
    assert abs(spec.wing.taper.value - 0.6) < 1e-4  # 150 / 250
    assert spec.wing.taper.status == "DERIVED"

    # Validation Checks
    errors = validate_aircraft_specification(spec)
    assert len(errors) == 0, f"FW-007 validation failed with: {errors}"


def test_conflict_detection():
    """Verify that contradictory requirements are caught."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    
    # Inject a conflicting wing span requirement in the text of Executive Summary
    raw_doc += "\n*   **Wingspan**: 1.80 m"

    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")
    assert any("wingspan" in err.lower() for err in spec.conflicts) or spec.wing.span.status == "CONFLICT"

    errors = validate_aircraft_specification(spec)
    assert len(errors) > 0, "Conflicts should trigger validation errors"


def test_missing_critical_bounds():
    """Test validation errors for missing CAD parameters."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    
    # Corrupt a section to remove the wingspan completely
    raw_doc = raw_doc.replace("Wingspan", "AlternativeLabel")

    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")
    errors = validate_aircraft_specification(spec)
    assert any("missing" in err.lower() and "span" in err.lower() for err in errors)


def test_envelope_bounds_validation():
    """Test structural containment checks (e.g. bay width exceeding fuselage)."""
    raw_doc = Path(SPEC_PATH).read_text(encoding="utf-8")
    
    # Modify payload bay volume to exceed fuselage max width (200mm)
    raw_doc = raw_doc.replace("200mm x 150mm x 150mm", "200mm x 250mm x 150mm")

    spec = parse_aircraft_specification(raw_doc, source_name="FW-007")
    errors = validate_aircraft_specification(spec)
    assert any("exceeds fuselage" in err.lower() for err in errors)
