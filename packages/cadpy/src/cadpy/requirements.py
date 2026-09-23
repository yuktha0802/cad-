"""Engineering specification parser, normalizer, and validator layer."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


@dataclass
class Requirement:
    value: Any
    unit: str
    source: str
    section: str
    status: str  # EXPLICIT, DERIVED, UNKNOWN, CONFLICT
    original_value: Optional[Any] = None
    original_unit: Optional[str] = None
    raw_text: Optional[str] = None


@dataclass
class IdentitySpec:
    title: Requirement = field(
        default_factory=lambda: Requirement(None, "", "", "", "UNKNOWN")
    )
    author: Requirement = field(
        default_factory=lambda: Requirement(None, "", "", "", "UNKNOWN")
    )


@dataclass
class MissionSpec:
    category: Requirement = field(
        default_factory=lambda: Requirement(None, "", "", "", "UNKNOWN")
    )
    target_payload: Requirement = field(
        default_factory=lambda: Requirement(None, "kg", "", "", "UNKNOWN")
    )
    flight_time_limit: Requirement = field(
        default_factory=lambda: Requirement(None, "minutes", "", "", "UNKNOWN")
    )
    cruise_speed: Requirement = field(
        default_factory=lambda: Requirement(None, "km/h", "", "", "UNKNOWN")
    )
    stall_speed: Requirement = field(
        default_factory=lambda: Requirement(None, "km/h", "", "", "UNKNOWN")
    )


@dataclass
class ConfigurationSpec:
    wing_position: Requirement = field(
        default_factory=lambda: Requirement(None, "", "", "", "UNKNOWN")
    )
    propulsion_layout: Requirement = field(
        default_factory=lambda: Requirement(None, "", "", "", "UNKNOWN")
    )
    tail_configuration: Requirement = field(
        default_factory=lambda: Requirement(None, "", "", "", "UNKNOWN")
    )
    landing_gear: Requirement = field(
        default_factory=lambda: Requirement(None, "", "", "", "UNKNOWN")
    )
    engine_count: Requirement = field(
        default_factory=lambda: Requirement(1, "", "", "", "DERIVED")
    )


@dataclass
class WingSpec:
    span: Requirement = field(
        default_factory=lambda: Requirement(None, "mm", "", "", "UNKNOWN")
    )
    area: Requirement = field(
        default_factory=lambda: Requirement(None, "m^2", "", "", "UNKNOWN")
    )
    root_chord: Requirement = field(
        default_factory=lambda: Requirement(None, "mm", "", "", "UNKNOWN")
    )
    tip_chord: Requirement = field(
        default_factory=lambda: Requirement(None, "mm", "", "", "UNKNOWN")
    )
    taper: Requirement = field(
        default_factory=lambda: Requirement(None, "", "", "", "UNKNOWN")
    )
    sweep: Requirement = field(
        default_factory=lambda: Requirement(0.0, "degrees", "", "", "DERIVED")
    )
    dihedral: Requirement = field(
        default_factory=lambda: Requirement(0.0, "degrees", "", "", "DERIVED")
    )
    incidence: Requirement = field(
        default_factory=lambda: Requirement(0.0, "degrees", "", "", "DERIVED")
    )
    root_airfoil: Requirement = field(
        default_factory=lambda: Requirement(None, "", "", "", "UNKNOWN")
    )
    tip_airfoil: Requirement = field(
        default_factory=lambda: Requirement(None, "", "", "", "UNKNOWN")
    )
    half_span: Requirement = field(
        default_factory=lambda: Requirement(None, "mm", "", "", "UNKNOWN")
    )


@dataclass
class TailSpec:
    span: Requirement = field(
        default_factory=lambda: Requirement(None, "mm", "", "", "UNKNOWN")
    )
    root_chord: Requirement = field(
        default_factory=lambda: Requirement(None, "mm", "", "", "UNKNOWN")
    )
    tip_chord: Requirement = field(
        default_factory=lambda: Requirement(None, "mm", "", "", "UNKNOWN")
    )
    sweep: Requirement = field(
        default_factory=lambda: Requirement(0.0, "degrees", "", "", "DERIVED")
    )
    incidence: Requirement = field(
        default_factory=lambda: Requirement(0.0, "degrees", "", "", "DERIVED")
    )
    airfoil: Requirement = field(
        default_factory=lambda: Requirement(None, "", "", "", "UNKNOWN")
    )
    height: Requirement = field(
        default_factory=lambda: Requirement(None, "mm", "", "", "UNKNOWN")
    )
    tail_arm: Requirement = field(
        default_factory=lambda: Requirement(None, "mm", "", "", "UNKNOWN")
    )


@dataclass
class FuselageSpec:
    length: Requirement = field(
        default_factory=lambda: Requirement(None, "mm", "", "", "UNKNOWN")
    )
    width: Requirement = field(
        default_factory=lambda: Requirement(None, "mm", "", "", "UNKNOWN")
    )
    height: Requirement = field(
        default_factory=lambda: Requirement(None, "mm", "", "", "UNKNOWN")
    )
    nose_length: Requirement = field(
        default_factory=lambda: Requirement(None, "mm", "", "", "UNKNOWN")
    )
    tail_cone_length: Requirement = field(
        default_factory=lambda: Requirement(None, "mm", "", "", "UNKNOWN")
    )
    cross_section_type: Requirement = field(
        default_factory=lambda: Requirement("ellipse", "", "", "", "DERIVED")
    )


@dataclass
class BaySpec:
    length: Requirement = field(
        default_factory=lambda: Requirement(None, "mm", "", "", "UNKNOWN")
    )
    width: Requirement = field(
        default_factory=lambda: Requirement(None, "mm", "", "", "UNKNOWN")
    )
    height: Requirement = field(
        default_factory=lambda: Requirement(None, "mm", "", "", "UNKNOWN")
    )


@dataclass
class InternalBaysSpec:
    payload_bay: BaySpec = field(default_factory=BaySpec)
    battery_bay: BaySpec = field(default_factory=BaySpec)
    avionics_bay: BaySpec = field(default_factory=BaySpec)


@dataclass
class LocationSpec:
    x: Requirement = field(
        default_factory=lambda: Requirement(None, "mm", "", "", "UNKNOWN")
    )
    y: Requirement = field(
        default_factory=lambda: Requirement(None, "mm", "", "", "UNKNOWN")
    )
    z: Requirement = field(
        default_factory=lambda: Requirement(None, "mm", "", "", "UNKNOWN")
    )


@dataclass
class ComponentLocationsSpec:
    motor: LocationSpec = field(default_factory=LocationSpec)
    battery: LocationSpec = field(default_factory=LocationSpec)
    payload: LocationSpec = field(default_factory=LocationSpec)
    avionics: LocationSpec = field(default_factory=LocationSpec)


@dataclass
class PropulsionSpec:
    motor: Requirement = field(
        default_factory=lambda: Requirement(None, "", "", "", "UNKNOWN")
    )
    propeller: Requirement = field(
        default_factory=lambda: Requirement(None, "", "", "", "UNKNOWN")
    )
    esc: Requirement = field(
        default_factory=lambda: Requirement(None, "", "", "", "UNKNOWN")
    )
    propulsion_layout: Requirement = field(
        default_factory=lambda: Requirement(None, "", "", "", "UNKNOWN")
    )
    propeller_diameter: Requirement = field(
        default_factory=lambda: Requirement(None, "mm", "", "", "UNKNOWN")
    )
    propeller_pitch: Requirement = field(
        default_factory=lambda: Requirement(None, "mm", "", "", "UNKNOWN")
    )


@dataclass
class ElectronicsSpec:
    flight_controller: Requirement = field(
        default_factory=lambda: Requirement(None, "", "", "", "UNKNOWN")
    )
    gps: Requirement = field(
        default_factory=lambda: Requirement(None, "", "", "", "UNKNOWN")
    )
    receiver: Requirement = field(
        default_factory=lambda: Requirement(None, "", "", "", "UNKNOWN")
    )
    telemetry: Requirement = field(
        default_factory=lambda: Requirement(None, "", "", "", "UNKNOWN")
    )


@dataclass
class PayloadSpec:
    sensor_type: Requirement = field(
        default_factory=lambda: Requirement(None, "", "", "", "UNKNOWN")
    )
    mass: Requirement = field(
        default_factory=lambda: Requirement(None, "kg", "", "", "UNKNOWN")
    )


@dataclass
class MassSpec:
    empty_weight: Requirement = field(
        default_factory=lambda: Requirement(None, "kg", "", "", "UNKNOWN")
    )
    battery_weight: Requirement = field(
        default_factory=lambda: Requirement(None, "kg", "", "", "UNKNOWN")
    )
    payload_weight: Requirement = field(
        default_factory=lambda: Requirement(None, "kg", "", "", "UNKNOWN")
    )
    MTOW: Requirement = field(
        default_factory=lambda: Requirement(None, "kg", "", "", "UNKNOWN")
    )


@dataclass
class CGSpec:
    cg_x: Requirement = field(
        default_factory=lambda: Requirement(None, "mm", "", "", "UNKNOWN")
    )
    static_margin: Requirement = field(
        default_factory=lambda: Requirement(None, "%", "", "", "UNKNOWN")
    )


@dataclass
class PerformanceSpec:
    takeoff_roll: Requirement = field(
        default_factory=lambda: Requirement(None, "m", "", "", "UNKNOWN")
    )
    stall_speed: Requirement = field(
        default_factory=lambda: Requirement(None, "km/h", "", "", "UNKNOWN")
    )
    flight_time: Requirement = field(
        default_factory=lambda: Requirement(None, "minutes", "", "", "UNKNOWN")
    )


@dataclass
class AircraftSpecification:
    identity: IdentitySpec = field(default_factory=IdentitySpec)
    mission: MissionSpec = field(default_factory=MissionSpec)
    configuration: ConfigurationSpec = field(default_factory=ConfigurationSpec)
    wing: WingSpec = field(default_factory=WingSpec)
    horizontal_tail: TailSpec = field(default_factory=TailSpec)
    vertical_tail: TailSpec = field(default_factory=TailSpec)
    fuselage: FuselageSpec = field(default_factory=FuselageSpec)
    internal_bays: InternalBaysSpec = field(default_factory=InternalBaysSpec)
    component_locations: ComponentLocationsSpec = field(
        default_factory=ComponentLocationsSpec
    )
    propulsion: PropulsionSpec = field(default_factory=PropulsionSpec)
    electronics: ElectronicsSpec = field(default_factory=ElectronicsSpec)
    payload: PayloadSpec = field(default_factory=PayloadSpec)
    mass: MassSpec = field(default_factory=MassSpec)
    cg: CGSpec = field(default_factory=CGSpec)
    performance: PerformanceSpec = field(default_factory=PerformanceSpec)
    conflicts: List[str] = field(default_factory=list)


def normalize_unit(
    value: Union[float, str], unit: str
) -> Tuple[Union[float, str], str]:
    """Centrally normalize length units to mm and angle units to degrees."""
    if isinstance(value, str):
        # Clean string if it is a numeric string
        try:
            val_f = float(value.replace(",", "").strip())
            return normalize_unit(val_f, unit)
        except ValueError:
            return value, unit

    unit_cleaned = unit.strip().lower()
    res_val = value
    res_unit = unit
    if unit_cleaned in {"m", "meter", "meters"}:
        res_val = value * 1000.0
        res_unit = "mm"
    elif unit_cleaned in {"cm", "centimeter", "centimeters"}:
        res_val = value * 10.0
        res_unit = "mm"
    elif unit_cleaned in {"in", "inch", "inches"}:
        res_val = value * 25.4
        res_unit = "mm"
    elif unit_cleaned in {"ft", "foot", "feet"}:
        res_val = value * 304.8
        res_unit = "mm"
    elif unit_cleaned in {"deg", "degree", "degrees", ""}:
        res_val = value
        res_unit = "degrees"
    elif unit_cleaned in {"g", "gram", "grams"}:
        res_val = value / 1000.0
        res_unit = "kg"

    if isinstance(res_val, float):
        res_val = round(res_val, 4)
    return res_val, res_unit


def parse_value_and_unit(text: str) -> Tuple[Union[float, str], str]:
    """Parse a text string into a numeric value (or string) and its unit."""
    text_clean = text.strip()

    # Check for propeller format like 12x6 APC or 12x6
    prop_match = re.match(r"^(\d+(?:\.\d+)?)\s*[xX]\s*(\d+(?:\.\d+)?)(?:\s*(.+))?$", text_clean)
    if prop_match:
        return text_clean, ""

    # Check for dimension patterns like 200mm x 150mm x 150mm
    dim_match = re.match(
        r"^(\d+(?:\.\d+)?)\s*(mm|m|cm)?\s*[xX]\s*(\d+(?:\.\d+)?)\s*(mm|m|cm)?\s*[xX]\s*(\d+(?:\.\d+)?)\s*(mm|m|cm)?$",
        text_clean,
        re.IGNORECASE,
    )
    if dim_match:
        # For bay volume dimensions, return the raw dimensions tuple as a string, e.g. "200x150x150"
        val = f"{dim_match.group(1)}x{dim_match.group(3)}x{dim_match.group(5)}"
        unit = dim_match.group(2) or dim_match.group(4) or dim_match.group(6) or "mm"
        return val, unit

    # Regular single value pattern
    match = re.match(r"^(-?\d+(?:\.\d+)?)\s*([a-zA-Z%^/0-9_-]+)?", text_clean)
    if match:
        val = float(match.group(1))
        unit = match.group(2) or ""
        return val, unit
    return text_clean, ""


def _parse_design_schema_dict(
    data: Dict[str, Any], spec: AircraftSpecification, source_name: str
) -> AircraftSpecification:
    """Parse a structured engineering design JSON dictionary directly into AircraftSpecification."""
    # 1. Identity
    design_id = data.get("design_id", source_name)
    spec.identity.title = Requirement(
        design_id, "", source_name, "Identity", "EXPLICIT"
    )

    # 2. Configuration
    config_str = str(data.get("configuration", ""))
    cfg_lower = config_str.lower()
    wing_pos = "high" if "high" in cfg_lower else ("low" if "low" in cfg_lower else "mid")
    prop_layout = "pusher" if "pusher" in cfg_lower else "tractor"
    tail_cfg = "conventional" if "conventional" in cfg_lower else ("v-tail" if "v-tail" in cfg_lower else "conventional")

    spec.configuration.wing_position = Requirement(
        wing_pos, "", source_name, "Configuration", "EXPLICIT"
    )
    spec.configuration.propulsion_layout = Requirement(
        prop_layout, "", source_name, "Configuration", "EXPLICIT"
    )
    spec.configuration.tail_configuration = Requirement(
        tail_cfg, "", source_name, "Configuration", "EXPLICIT"
    )

    # 3. Geometry - Wing
    geom = data.get("geometry", {})
    wing_geom = geom.get("wing", {})
    cad_handover = data.get("cad_handover", {})
    major_geom = cad_handover.get("major_geometry", {})

    span_m = wing_geom.get("span_m") or major_geom.get("wingspan_m") or 2.0
    root_c_m = wing_geom.get("root_chord_m") or major_geom.get("root_chord_m") or 0.25
    tip_c_m = wing_geom.get("tip_chord_m") or major_geom.get("tip_chord_m") or 0.15
    sweep_deg = float(wing_geom.get("sweep_deg", 0.0))
    dihedral_deg = float(wing_geom.get("dihedral_deg", 2.0))
    incidence_deg = float(wing_geom.get("incidence_deg", 1.5))
    root_airfoil = wing_geom.get("airfoil_root") or (
        cad_handover.get("wing_airfoils", ["NACA 2412"])[0]
        if cad_handover.get("wing_airfoils")
        else "NACA 2412"
    )
    tip_airfoil = wing_geom.get("airfoil_tip") or (
        cad_handover.get("wing_airfoils", ["NACA 2412"])[-1]
        if cad_handover.get("wing_airfoils")
        else "NACA 2412"
    )

    spec.wing.span = Requirement(
        span_m * 1000.0, "mm", source_name, "Wing", "EXPLICIT", original_value=span_m, original_unit="m"
    )
    spec.wing.root_chord = Requirement(
        root_c_m * 1000.0, "mm", source_name, "Wing", "EXPLICIT", original_value=root_c_m, original_unit="m"
    )
    spec.wing.tip_chord = Requirement(
        tip_c_m * 1000.0, "mm", source_name, "Wing", "EXPLICIT", original_value=tip_c_m, original_unit="m"
    )
    spec.wing.sweep = Requirement(
        sweep_deg, "degrees", source_name, "Wing", "EXPLICIT"
    )
    spec.wing.dihedral = Requirement(
        dihedral_deg, "degrees", source_name, "Wing", "EXPLICIT"
    )
    spec.wing.incidence = Requirement(
        incidence_deg, "degrees", source_name, "Wing", "EXPLICIT"
    )
    spec.wing.root_airfoil = Requirement(
        root_airfoil, "", source_name, "Wing", "EXPLICIT"
    )
    spec.wing.tip_airfoil = Requirement(
        tip_airfoil, "", source_name, "Wing", "EXPLICIT"
    )
    if wing_geom.get("area_m2") or major_geom.get("wing_area_m2"):
        spec.wing.area = Requirement(
            wing_geom.get("area_m2") or major_geom.get("wing_area_m2"),
            "m^2", source_name, "Wing", "EXPLICIT"
        )

    # 4. Geometry - Fuselage
    fuse_geom = geom.get("fuselage", {})
    fuse_len_m = fuse_geom.get("length_m") or major_geom.get("fuselage_length_m") or 1.2
    fuse_w_m = fuse_geom.get("max_width_m") or major_geom.get("fuselage_width_m") or 0.16
    fuse_h_m = fuse_geom.get("max_height_m", 0.18)

    spec.fuselage.length = Requirement(
        fuse_len_m * 1000.0, "mm", source_name, "Fuselage", "EXPLICIT", original_value=fuse_len_m, original_unit="m"
    )
    spec.fuselage.width = Requirement(
        fuse_w_m * 1000.0, "mm", source_name, "Fuselage", "EXPLICIT", original_value=fuse_w_m, original_unit="m"
    )
    spec.fuselage.height = Requirement(
        fuse_h_m * 1000.0, "mm", source_name, "Fuselage", "EXPLICIT", original_value=fuse_h_m, original_unit="m"
    )

    # Internal bays
    p_dims = fuse_geom.get("payload_bay_dimensions_m")
    if p_dims and len(p_dims) == 3:
        spec.internal_bays.payload_bay.length = Requirement(
            p_dims[0] * 1000.0, "mm", source_name, "Internal Bays", "EXPLICIT"
        )
        spec.internal_bays.payload_bay.width = Requirement(
            p_dims[1] * 1000.0, "mm", source_name, "Internal Bays", "EXPLICIT"
        )
        spec.internal_bays.payload_bay.height = Requirement(
            p_dims[2] * 1000.0, "mm", source_name, "Internal Bays", "EXPLICIT"
        )

    b_dims = fuse_geom.get("battery_bay_dimensions_m")
    if b_dims and len(b_dims) == 3:
        spec.internal_bays.battery_bay.length = Requirement(
            b_dims[0] * 1000.0, "mm", source_name, "Internal Bays", "EXPLICIT"
        )
        spec.internal_bays.battery_bay.width = Requirement(
            b_dims[1] * 1000.0, "mm", source_name, "Internal Bays", "EXPLICIT"
        )
        spec.internal_bays.battery_bay.height = Requirement(
            b_dims[2] * 1000.0, "mm", source_name, "Internal Bays", "EXPLICIT"
        )

    a_dims = fuse_geom.get("avionics_bay_dimensions_m")
    if a_dims and len(a_dims) == 3:
        spec.internal_bays.avionics_bay.length = Requirement(
            a_dims[0] * 1000.0, "mm", source_name, "Internal Bays", "EXPLICIT"
        )
        spec.internal_bays.avionics_bay.width = Requirement(
            a_dims[1] * 1000.0, "mm", source_name, "Internal Bays", "EXPLICIT"
        )
        spec.internal_bays.avionics_bay.height = Requirement(
            a_dims[2] * 1000.0, "mm", source_name, "Internal Bays", "EXPLICIT"
        )

    # 5. Tail
    tail_geom = geom.get("tail", {})
    t_span_m = tail_geom.get("span_m") or major_geom.get("tail_span_m") or 0.6
    t_root_c_m = tail_geom.get("root_chord_m", 0.15)
    t_tip_c_m = tail_geom.get("tip_chord_m", 0.1)
    t_airfoil = tail_geom.get("airfoil") or cad_handover.get("tail_airfoil", "NACA 0012")

    spec.horizontal_tail.span = Requirement(
        t_span_m * 1000.0, "mm", source_name, "Tail", "EXPLICIT", original_value=t_span_m, original_unit="m"
    )
    spec.horizontal_tail.root_chord = Requirement(
        t_root_c_m * 1000.0, "mm", source_name, "Tail", "EXPLICIT", original_value=t_root_c_m, original_unit="m"
    )
    spec.horizontal_tail.tip_chord = Requirement(
        t_tip_c_m * 1000.0, "mm", source_name, "Tail", "EXPLICIT", original_value=t_tip_c_m, original_unit="m"
    )
    spec.horizontal_tail.airfoil = Requirement(
        t_airfoil, "", source_name, "Tail", "EXPLICIT"
    )

    # Vertical Fin
    spec.vertical_tail.root_chord = Requirement(
        t_root_c_m * 1000.0, "mm", source_name, "Tail", "EXPLICIT"
    )
    spec.vertical_tail.tip_chord = Requirement(
        t_tip_c_m * 1000.0, "mm", source_name, "Tail", "EXPLICIT"
    )
    v_area = tail_geom.get("projected_vertical_area_m2", 0.04)
    avg_c = (t_root_c_m + t_tip_c_m) / 2.0
    v_h_m = (v_area / avg_c) if avg_c > 0 else 0.25
    spec.vertical_tail.height = Requirement(
        v_h_m * 1000.0, "mm", source_name, "Tail", "EXPLICIT", original_value=v_h_m, original_unit="m"
    )
    spec.vertical_tail.airfoil = Requirement(
        t_airfoil, "", source_name, "Tail", "EXPLICIT"
    )

    # 6. Propulsion
    prop_dict = data.get("propulsion", {})
    cruise_prop = prop_dict.get("cruise_propulsion", {})
    motor_name = cruise_prop.get("motor_model", "")
    prop_model = cruise_prop.get("propeller_model", "APC 12x6E")
    prop_diam_in = float(cruise_prop.get("propeller_diameter_in", 12.0))
    prop_pitch_in = float(cruise_prop.get("propeller_pitch_in", 6.0))

    spec.propulsion.motor = Requirement(
        motor_name, "", source_name, "Propulsion", "EXPLICIT"
    )
    spec.propulsion.propeller = Requirement(
        prop_model, "", source_name, "Propulsion", "EXPLICIT"
    )
    spec.propulsion.propeller_diameter = Requirement(
        prop_diam_in * 25.4, "mm", source_name, "Propulsion", "EXPLICIT", original_value=prop_diam_in, original_unit="in"
    )
    spec.propulsion.propeller_pitch = Requirement(
        prop_pitch_in * 25.4, "mm", source_name, "Propulsion", "EXPLICIT", original_value=prop_pitch_in, original_unit="in"
    )

    # 7. Mass & CG
    mass_dict = data.get("mass_properties", {})
    spec.mass.MTOW = Requirement(
        float(mass_dict.get("mtow_kg", 3.2)), "kg", source_name, "Mass", "EXPLICIT"
    )
    spec.mass.empty_weight = Requirement(
        float(mass_dict.get("empty_mass_kg", 1.8)), "kg", source_name, "Mass", "EXPLICIT"
    )
    spec.mass.payload_weight = Requirement(
        float(mass_dict.get("payload_mass_kg", 0.8)), "kg", source_name, "Mass", "EXPLICIT"
    )
    spec.mass.battery_weight = Requirement(
        float(mass_dict.get("battery_mass_kg", 0.65)), "kg", source_name, "Mass", "EXPLICIT"
    )

    cg_x_m = mass_dict.get("cg_x_m") or (
        cad_handover.get("cg_location_m", [0.44])[0] if cad_handover.get("cg_location_m") else 0.44
    )
    spec.cg.cg_x = Requirement(
        float(cg_x_m) * 1000.0, "mm", source_name, "CG", "EXPLICIT"
    )

    derive_values(spec, source_name)
    return spec


def parse_aircraft_specification(
    document: Union[str, Dict[str, Any]], source_name: str = "FW-007"
) -> AircraftSpecification:
    """Parse the engineering specification from a report JSON or raw text."""
    spec = AircraftSpecification()

    # Check for direct design schema JSON / dictionary
    if isinstance(document, dict):
        if "geometry" in document or "cad_handover" in document or "aircraft_class" in document:
            return _parse_design_schema_dict(document, spec, source_name)
    elif isinstance(document, str):
        try:
            parsed_json = json.loads(document)
            if isinstance(parsed_json, dict) and ("geometry" in parsed_json or "cad_handover" in parsed_json or "aircraft_class" in parsed_json):
                return _parse_design_schema_dict(parsed_json, spec, source_name)
        except Exception:
            pass

    # Load dict from JSON if applicable
    raw_sections = {}
    if isinstance(document, dict):
        raw_sections = document.get("sections", {})
        spec.identity.title = Requirement(
            document.get("title", "Aircraft Report"),
            "",
            source_name,
            "Identity",
            "EXPLICIT",
        )
        spec.identity.author = Requirement(
            document.get("author", "Unknown"),
            "",
            source_name,
            "Identity",
            "EXPLICIT",
        )
    elif isinstance(document, str):
        # Try loading as JSON first
        try:
            data = json.loads(document)
            raw_sections = data.get("sections", {})
            spec.identity.title = Requirement(
                data.get("title", "Aircraft Report"),
                "",
                source_name,
                "Identity",
                "EXPLICIT",
            )
            spec.identity.author = Requirement(
                data.get("author", "Unknown"),
                "",
                source_name,
                "Identity",
                "EXPLICIT",
            )
        except json.JSONDecodeError:
            # Check for YAML frontmatter
            title = "Aircraft Report"
            author = "Unknown"
            frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", document, re.DOTALL)
            if frontmatter_match:
                fm_text = frontmatter_match.group(1)
                for line in fm_text.splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        k = k.strip().lower()
                        v = v.strip().strip('"').strip("'")
                        if k == "title":
                            title = v
                        elif k == "author":
                            author = v
            spec.identity.title = Requirement(
                title, "", source_name, "Identity", "EXPLICIT"
            )
            spec.identity.author = Requirement(
                author, "", source_name, "Identity", "EXPLICIT"
            )

            # Treating string as raw Markdown content divided by headers
            current_section = "Executive Summary"
            raw_sections[current_section] = []
            for line in document.splitlines():
                header_match = re.match(r"^#+\s+(.+)$", line)
                if header_match:
                    current_section = header_match.group(1).strip()
                    raw_sections[current_section] = []
                else:
                    raw_sections[current_section].append(line)
            raw_sections = {
                k: "\n".join(v) for k, v in raw_sections.items()
            }

    # Extract requirements from each section
    parsed_occurrences: Dict[str, List[Tuple[Any, str, str, str]]] = {}

    for section_name, content in raw_sections.items():
        # Iterate over lines matching bullet points or containing bold details
        lines = content.splitlines()
        for line in lines:
            # Bullet point matcher
            bullet_match = re.search(
                r"[*+-]\s*\*\*([^*]+)\*\*:\s*(.+)$", line
            )
            if not bullet_match:
                bullet_match = re.search(
                    r"###\s+([^*]+)$", line
                )  # Header-like parameter sections
                if not bullet_match:
                    continue
                # If header, we don't have direct value on this line
                continue

            label = bullet_match.group(1).strip().lower()
            raw_val_str = bullet_match.group(2).strip()

            # Handle comments or references at the end of the line
            raw_val_str = re.split(r"\s+\(", raw_val_str)[0]

            val, unit = parse_value_and_unit(raw_val_str)
            norm_val, norm_unit = normalize_unit(val, unit)

            # Record occurrence for conflict check
            key = f"{section_name.lower()}.{label}"
            if key not in parsed_occurrences:
                parsed_occurrences[key] = []
            parsed_occurrences[key].append(
                (norm_val, norm_unit, section_name, line)
            )

    # Process and assign parsed parameters
    def assign_req(
        section_obj: Any,
        field_name: str,
        label_key: str,
        default_unit: str = "",
    ):
        matching_occs = []
        for key, occs in parsed_occurrences.items():
            if label_key in key:
                matching_occs.extend(occs)

        if not matching_occs:
            return  # Leave as UNKNOWN

        # Conflict check
        first_val, first_unit, first_sec, first_txt = matching_occs[0]
        has_conflict = False
        for val, unit, sec, txt in matching_occs[1:]:
            # Compare numbers within tolerance
            if isinstance(val, (int, float)) and isinstance(
                first_val, (int, float)
            ):
                if abs(val - first_val) > 1e-4:
                    has_conflict = True
            elif val != first_val:
                has_conflict = True

        if has_conflict:
            spec.conflicts.append(
                f"Conflict detected for {label_key}: {[o[0] for o in matching_occs]}"
            )
            req = Requirement(
                first_val,
                first_unit,
                source_name,
                first_sec,
                "CONFLICT",
                original_value=first_val,
                original_unit=first_unit,
                raw_text=first_txt,
            )
        else:
            req = Requirement(
                first_val,
                first_unit,
                source_name,
                first_sec,
                "EXPLICIT",
                original_value=first_val,
                original_unit=first_unit,
                raw_text=first_txt,
            )

        setattr(section_obj, field_name, req)

    # Configuration Mapping
    assign_req(spec.configuration, "wing_position", "wing placement")
    assign_req(spec.configuration, "propulsion_layout", "propulsion layout")
    assign_req(spec.configuration, "tail_configuration", "tail assembly")
    assign_req(spec.configuration, "landing_gear", "landing gear")

    # Wing Mapping
    assign_req(spec.wing, "span", "wingspan")
    assign_req(spec.wing, "root_chord", "root chord")
    assign_req(spec.wing, "tip_chord", "tip chord")
    assign_req(spec.wing, "area", "reference area")
    assign_req(spec.wing, "aspect_ratio", "aspect ratio")
    assign_req(spec.wing, "dihedral", "dihedral")
    assign_req(spec.wing, "sweep", "sweep")
    assign_req(spec.wing, "incidence", "incidence")

    # Fuselage Mapping
    assign_req(spec.fuselage, "length", "total length")
    assign_req(spec.fuselage, "width", "maximum width")
    assign_req(spec.fuselage, "height", "maximum height")

    # Stabilizers Mapping
    assign_req(spec.horizontal_tail, "span", "horizontal stabilizer span")
    assign_req(spec.vertical_tail, "height", "vertical fin height")

    # Propulsion Mapping
    assign_req(spec.propulsion, "motor", "power unit")
    assign_req(spec.propulsion, "propeller", "propeller")

    # Payload Mapping
    assign_req(spec.payload, "sensor_type", "selected sensor")

    # Mass Mapping
    assign_req(spec.mass, "MTOW", "takeoff mass")
    assign_req(spec.mass, "empty_weight", "empty structure weight")
    assign_req(spec.mass, "battery_weight", "battery weight")
    assign_req(spec.mass, "battery_weight", "battery pack mass")
    assign_req(spec.mass, "payload_weight", "useful payload weight")

    # Check for bay volume dimensions (e.g. 200mm x 150mm x 150mm)
    for key, occs in parsed_occurrences.items():
        if "compartment volume" in key:
            val = occs[0][0]  # E.g. "200x150x150"
            sec = occs[0][2]
            txt = occs[0][3]
            try:
                parts = [float(x) for x in val.split("x")]
                spec.internal_bays.payload_bay.length = Requirement(
                    parts[0], "mm", source_name, sec, "EXPLICIT", raw_text=txt
                )
                spec.internal_bays.payload_bay.width = Requirement(
                    parts[1], "mm", source_name, sec, "EXPLICIT", raw_text=txt
                )
                spec.internal_bays.payload_bay.height = Requirement(
                    parts[2], "mm", source_name, sec, "EXPLICIT", raw_text=txt
                )
            except Exception:
                pass

    # Derivations and Defaults Sizing
    derive_values(spec, source_name)

    return spec


def derive_values(spec: AircraftSpecification, source_name: str):
    """Sizer for missing parameters based on pure mathematical relationships."""
    # 1. Wing half_span
    if spec.wing.span.status == "EXPLICIT" and spec.wing.span.value is not None:
        spec.wing.half_span = Requirement(
            spec.wing.span.value / 2.0,
            "mm",
            source_name,
            spec.wing.span.section,
            "DERIVED",
            raw_text="half_span = span / 2",
        )

    # 2. Wing taper
    if (
        spec.wing.tip_chord.status == "EXPLICIT"
        and spec.wing.root_chord.status == "EXPLICIT"
    ):
        if (
            spec.wing.root_chord.value is not None
            and spec.wing.root_chord.value > 0
        ):
            spec.wing.taper = Requirement(
                spec.wing.tip_chord.value / spec.wing.root_chord.value,
                "",
                source_name,
                spec.wing.tip_chord.section,
                "DERIVED",
                raw_text="taper = tip_chord / root_chord",
            )

    # 3. Propeller diameter and pitch from "12x6 APC" format
    if (
        spec.propulsion.propeller.status == "EXPLICIT"
        and spec.propulsion.propeller.value
    ):
        prop_str = str(spec.propulsion.propeller.value)
        prop_match = re.search(r"(\d+(?:\.\d+)?)\s*[x]\s*(\d+(?:\.\d+)?)", prop_str)
        if prop_match:
            try:
                diam_in = float(prop_match.group(1))
                pitch_in = float(prop_match.group(2))
                diam_mm = diam_in * 25.4
                pitch_mm = pitch_in * 25.4
                spec.propulsion.propeller_diameter = Requirement(
                    diam_mm,
                    "mm",
                    source_name,
                    spec.propulsion.propeller.section,
                    "DERIVED",
                    original_value=diam_in,
                    original_unit="in",
                    raw_text=f"extracted from {prop_str}",
                )
                spec.propulsion.propeller_pitch = Requirement(
                    pitch_mm,
                    "mm",
                    source_name,
                    spec.propulsion.propeller.section,
                    "DERIVED",
                    original_value=pitch_in,
                    original_unit="in",
                    raw_text=f"extracted from {prop_str}",
                )
            except Exception:
                pass


def validate_aircraft_specification(spec: AircraftSpecification) -> List[str]:
    """Validate aircraft specification bounds and logical consistency."""
    errors = []

    # 1. Critical CAD fields check
    critical_fields = [
        ("wing.span", spec.wing.span),
        ("wing.root_chord", spec.wing.root_chord),
        ("wing.tip_chord", spec.wing.tip_chord),
        ("fuselage.length", spec.fuselage.length),
        ("fuselage.width", spec.fuselage.width),
        ("fuselage.height", spec.fuselage.height),
    ]
    for label, req in critical_fields:
        if req.status == "UNKNOWN" or req.value is None:
            errors.append(f"Required parameter is missing (UNKNOWN): {label}")
        elif req.status == "CONFLICT":
            errors.append(
                f"Required parameter has unresolved conflict: {label}"
            )

    # 2. Check conflict array (only critical conflicts raise block errors)
    for conf in spec.conflicts:
        if any(c in conf.lower() for c in ["span", "chord", "length", "width", "height"]):
            errors.append(f"Conflict: {conf}")

    # 3. Geometry boundaries & Sizing rules validation
    if spec.wing.span.value is not None:
        if spec.wing.span.value <= 0:
            errors.append("Wing span must be positive.")
    if spec.wing.root_chord.value is not None:
        if spec.wing.root_chord.value <= 0:
            errors.append("Wing root chord must be positive.")

    # Check structural compatibility: battery size inside battery bay
    # If not specified, we do not throw error (they are UNKNOWN), but if they exist, check it.
    if (
        spec.internal_bays.payload_bay.width.value is not None
        and spec.fuselage.width.value is not None
    ):
        if (
            spec.internal_bays.payload_bay.width.value
            > spec.fuselage.width.value
        ):
            errors.append(
                f"Payload bay width ({spec.internal_bays.payload_bay.width.value} mm) "
                f"exceeds fuselage width ({spec.fuselage.width.value} mm)."
            )

    # Airfoil profile validation
    # Clark Y, NACA 0012, NACA 4412, etc are valid. If it's a path or unknown, report it.
    if spec.wing.root_airfoil.value:
        airfoil = str(spec.wing.root_airfoil.value).lower().strip()
        is_known = (
            "clark" in airfoil
            or "naca" in airfoil
            or airfoil in {"clarky", "naca0012", "naca4412", "naca2412"}
        )
        if not is_known:
            errors.append(
                f"Airfoil identifier is invalid or custom coordinate data is missing: {spec.wing.root_airfoil.value}"
            )

    # Configuration support check
    if spec.configuration.wing_position.value:
        pos = str(spec.configuration.wing_position.value).lower().strip()
        if pos not in {"high", "mid", "low", "high wing", "mid wing", "low wing"}:
            errors.append(
                f"Unsupported wing placement configuration: {spec.configuration.wing_position.value}"
            )

    return errors
