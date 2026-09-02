"""Parametric Aircraft CAD Geometry Engine.

Provides reusable parameter-driven component builders (Wing, Fuselage, Stabilizers, 
Propulsion, and Internal Envelopes) and a top-level generate_aircraft flow.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence
from dataclasses import dataclass, field
from build123d import *
from cadpy.assembly import AssemblyHelper

# Normalized Clark Y coordinates (X, Upper Y, Lower Y)
CLARKY_COORDS = [
    (0.0000, 0.0000, 0.0000),
    (0.0005, 0.0023, -0.0047),
    (0.0010, 0.0037, -0.0059),
    (0.0020, 0.0058, -0.0078),
    (0.0040, 0.0089, -0.0105),
    (0.0080, 0.0137, -0.0143),
    (0.0120, 0.0179, -0.0170),
    (0.0200, 0.0254, -0.0203),
    (0.0300, 0.0330, -0.0226),
    (0.0400, 0.0391, -0.0245),
    (0.0500, 0.0443, -0.0260),
    (0.0600, 0.0488, -0.0271),
    (0.0800, 0.0564, -0.0285),
    (0.1000, 0.0630, -0.0294),
    (0.1200, 0.0686, -0.0300),
    (0.1400, 0.0734, -0.0302),
    (0.1600, 0.0776, -0.0303),
    (0.1800, 0.0811, -0.0300),
    (0.2000, 0.0839, -0.0297),
    (0.3000, 0.0907, -0.0263),
    (0.4000, 0.0912, -0.0203),
    (0.5000, 0.0859, -0.0143),
    (0.6000, 0.0758, -0.0083),
    (0.7000, 0.0614, -0.0039),
    (0.8000, 0.0439, -0.0015),
    (0.9000, 0.0235, -0.0004),
    (1.0000, 0.0006, 0.0000),
]


def clarky_points(chord: float, num_points: int = 60) -> list[tuple[float, float]]:
    """Generate 2D coordinates for a Clark Y airfoil scaled by chord."""
    upper_pts = []
    lower_pts = []
    for i in range(num_points + 1):
        beta = math.pi * i / num_points
        x = 0.5 * (1.0 - math.cos(beta))
        
        # Interpolate coordinates table
        idx = 0
        while idx < len(CLARKY_COORDS) - 1 and CLARKY_COORDS[idx+1][0] < x:
            idx += 1
            
        x0, y_u0, y_l0 = CLARKY_COORDS[idx]
        x1, y_u1, y_l1 = CLARKY_COORDS[idx+1]
        
        t = (x - x0) / (x1 - x0) if x1 > x0 else 0.0
        yu = y_u0 + t * (y_u1 - y_u0)
        yl = y_l0 + t * (y_l1 - y_l0)
        
        upper_pts.append((x * chord, yu * chord))
        lower_pts.append((x * chord, yl * chord))
        
    pts = []
    for pt in reversed(lower_pts):
        pts.append(pt)
    for pt in upper_pts[1:]:
        pts.append(pt)
    return pts


def naca_points(code: str, chord: float, num_points: int = 60) -> list[tuple[float, float]]:
    """Generate NACA 4-digit airfoil coordinates scaled by chord."""
    code_val = int(code.lower().replace("naca", ""))
    code_str = f"{code_val:04d}"
    m = float(code_str[0]) / 100.0
    p = float(code_str[1]) / 10.0
    t = float(code_str[2:]) / 100.0
    
    upper_pts = []
    lower_pts = []
    for i in range(num_points + 1):
        beta = math.pi * i / num_points
        x = 0.5 * (1.0 - math.cos(beta))
        yt = 5.0 * t * (0.2969 * math.sqrt(x) - 0.1260 * x - 0.3516 * x**2 + 0.2843 * x**3 - 0.1015 * x**4)
        if x < p and p > 0:
            yc = (m / p**2) * (2.0 * p * x - x**2)
            dyc_dx = (2.0 * m / p**2) * (p - x)
        else:
            if 1.0 - p > 0:
                yc = (m / (1.0 - p)**2) * ((1.0 - 2.0 * p) + 2.0 * p * x - x**2)
                dyc_dx = (2.0 * m / (1.0 - p)**2) * (p - x)
            else:
                yc = 0.0
                dyc_dx = 0.0
        theta = math.atan(dyc_dx)
        xu = x - yt * math.sin(theta)
        yu = yc + yt * math.cos(theta)
        upper_pts.append((xu * chord, yu * chord))
        xl = x + yt * math.sin(theta)
        yl = yc - yt * math.cos(theta)
        lower_pts.append((xl * chord, yl * chord))
        
    pts = []
    for pt in reversed(lower_pts):
        pts.append(pt)
    for pt in upper_pts[1:]:
        pts.append(pt)
    return pts


def airfoil_points(airfoil_name: str, chord: float, num_points: int = 60) -> list[tuple[float, float]]:
    """Determine coordinates for NACA or Clark Y airfoils."""
    name = airfoil_name.lower().strip()
    if "clark" in name:
        return clarky_points(chord, num_points)
    return naca_points(name, chord, num_points)


def build_wing_half(
    span_half: float,
    root_chord: float,
    tip_chord: float,
    sweep_deg: float,
    dihedral_deg: float,
    incidence_deg: float,
    root_airfoil: str,
    tip_airfoil: str,
    leading_edge_x: float,
    root_z: float,
    is_left: bool = False
) -> Solid:
    """Generate a single lofted solid wing half."""
    y_sections = [0.0, span_half * 0.5, span_half]
    wires = []
    
    for y in y_sections:
        eta = y / span_half
        chord = root_chord - (root_chord - tip_chord) * eta
        
        # Calculate local twist angle
        local_incidence = incidence_deg * (1.0 - eta)
        
        # Dihedral and Sweep offsets
        z_pos = root_z + y * math.tan(math.radians(dihedral_deg))
        x_offset = leading_edge_x + y * math.tan(math.radians(sweep_deg))
        
        # Airfoil coordinate selection
        local_airfoil = root_airfoil if eta < 0.5 else tip_airfoil
        pts_2d = airfoil_points(local_airfoil, chord)
        
        # Rotate coordinates by local incidence (Y-axis rotation)
        angle_rad = math.radians(-local_incidence)
        cos_i = math.cos(angle_rad)
        sin_i = math.sin(angle_rad)
        
        pts_3d = []
        for px, pz in pts_2d:
            rx = px * cos_i - pz * sin_i
            rz = px * sin_i + pz * cos_i
            
            y_pos = -y if is_left else y
            pts_3d.append(Vector(x_offset + rx, y_pos, z_pos + rz))
            
        w_spline = Spline(pts_3d, periodic=True)
        wires.append(Wire([w_spline]))
        
    return Solid.make_loft(wires)


def build_wing(
    span: float,
    root_chord: float,
    tip_chord: float,
    sweep_deg: float,
    dihedral_deg: float,
    incidence_deg: float,
    root_airfoil: str,
    tip_airfoil: str,
    leading_edge_x: float,
    root_z: float,
) -> tuple[Solid, Solid]:
    """Generate left and right lofted wing halves."""
    left = build_wing_half(span / 2.0, root_chord, tip_chord, sweep_deg, dihedral_deg, incidence_deg, root_airfoil, tip_airfoil, leading_edge_x, root_z, is_left=True)
    right = build_wing_half(span / 2.0, root_chord, tip_chord, sweep_deg, dihedral_deg, incidence_deg, root_airfoil, tip_airfoil, leading_edge_x, root_z, is_left=False)
    return left, right


def build_fuselage(
    length: float,
    width: float,
    height: float,
    nose_length: float,
    tail_cone_length: float,
    cross_section_type: str = "ellipse"
) -> Solid:
    """Generate a precision aerodynamic fuselage using nose loft, constant midbody, and tail loft."""
    mid_length = length - nose_length - tail_cone_length
    if mid_length < 0:
        raise ValueError("Nose and tail lengths exceed total fuselage length.")
        
    ry_max = width / 2.0
    rz_max = height / 2.0
    center_z = height / 2.0
    
    # 1. Nose loft (from x=0 to x=nose_length)
    wires_nose = []
    for x, sy, sz in [(0.0, 0.05, 0.05), (nose_length * 0.4, 0.7, 0.7), (nose_length, 1.0, 1.0)]:
        plane = Plane(origin=(x, 0, center_z), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
        with BuildSketch(plane) as s:
            if cross_section_type.lower() == "rectangle":
                Rectangle(width * sy, height * sz)
            else:
                Ellipse(ry_max * sy, rz_max * sz)
        wires_nose.append(s.wire().located(plane.location))
    nose_solid = Solid.make_loft(wires_nose)

    # 2. Midbody extrude (constant cross-section across mid_length)
    if mid_length > 0:
        plane_mid = Plane(origin=(nose_length, 0, center_z), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
        with BuildSketch(plane_mid) as s:
            if cross_section_type.lower() == "rectangle":
                Rectangle(width, height)
            else:
                Ellipse(ry_max, rz_max)
        mid_solid = extrude(s.sketch.faces()[0], amount=mid_length, dir=(1, 0, 0))
    else:
        mid_solid = None

    # 3. Tail cone loft (from x=nose_length+mid_length to length)
    wires_tail = []
    for x, sy, sz in [(nose_length + mid_length, 1.0, 1.0), (nose_length + mid_length + tail_cone_length * 0.6, 0.5, 0.4), (length, 0.1, 0.1)]:
        plane = Plane(origin=(x, 0, center_z), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
        with BuildSketch(plane) as s:
            if cross_section_type.lower() == "rectangle":
                Rectangle(width * sy, height * sz)
            else:
                Ellipse(ry_max * sy, rz_max * sz)
        wires_tail.append(s.wire().located(plane.location))
    tail_solid = Solid.make_loft(wires_tail)

    fuselage = nose_solid
    if mid_solid:
        fuselage = fuselage.fuse(mid_solid)
    fuselage = fuselage.fuse(tail_solid)
    return fuselage


def build_horizontal_tail(
    span: float,
    root_chord: float,
    tip_chord: float,
    sweep_deg: float,
    incidence_deg: float,
    airfoil: str,
    leading_edge_x: float,
    root_z: float,
) -> tuple[Solid, Solid]:
    """Generate horizontal tail stabilizers."""
    left = build_wing_half(span / 2.0, root_chord, tip_chord, sweep_deg, 0.0, incidence_deg, airfoil, airfoil, leading_edge_x, root_z, is_left=True)
    right = build_wing_half(span / 2.0, root_chord, tip_chord, sweep_deg, 0.0, incidence_deg, airfoil, airfoil, leading_edge_x, root_z, is_left=False)
    return left, right


def build_vertical_tail(
    height: float,
    root_chord: float,
    tip_chord: float,
    sweep_deg: float,
    airfoil: str,
    leading_edge_x: float,
    root_z: float,
) -> Solid:
    """Generate vertical tail fin using airfoil lofting upward."""
    z_sections = [0.0, height * 0.5, height]
    wires = []
    
    for z in z_sections:
        eta = z / height
        chord = root_chord - (root_chord - tip_chord) * eta
        x_offset = leading_edge_x + z * math.tan(math.radians(sweep_deg))
        
        pts_2d = airfoil_points(airfoil, chord)
        pts_3d = []
        for px, py in pts_2d:
            pts_3d.append(Vector(x_offset + px, py, root_z + z))
            
        w_spline = Spline(pts_3d, periodic=True)
        wires.append(Wire([w_spline]))
        
    return Solid.make_loft(wires)


def build_propulsion(
    diameter: float,
    pitch: float,
    position_x: float,
    position_y: float,
    position_z: float,
    orientation_y: float,
    layout: str = "pusher",
    fuselage_height: float = 270.0
) -> tuple[Solid, Solid, Solid]:
    """Generate motor mount plate, motor body envelope, and propeller blades."""
    mount_thickness = 5.0
    mount = Cylinder(radius=25.0, height=mount_thickness)
    mount = mount.rotate(Axis.Y, 90).translate((position_x, position_y, position_z))
    
    motor_length = 40.0
    motor_radius = 20.0
    motor = Cylinder(radius=motor_radius, height=motor_length)
    
    x_motor_pos = position_x - (motor_length / 2.0 + mount_thickness) if layout == "pusher" else position_x + (motor_length / 2.0 + mount_thickness)
    motor = motor.rotate(Axis.Y, 90).translate((x_motor_pos, position_y, position_z))
    
    prop_x = x_motor_pos - (motor_length / 2.0 + 5.0) if layout == "pusher" else x_motor_pos + (motor_length / 2.0 + 5.0)
    hub = Cylinder(radius=12.0, height=8.0).rotate(Axis.Y, 90)
    blade1 = Box(6.0, diameter / 2.0, 4.0, align=(Align.CENTER, Align.MIN, Align.CENTER))
    blade2 = Box(6.0, diameter / 2.0, 4.0, align=(Align.CENTER, Align.MAX, Align.CENTER))
    propeller = hub.fuse(blade1).fuse(blade2).translate((prop_x, position_y, position_z))
    
    return mount, motor, propeller


def build_internal_envelopes(
    fuselage_length: float,
    fuselage_width: float,
    fuselage_height: float,
    payload_dims: tuple[float, float, float] | None = None,
    battery_dims: tuple[float, float, float] | None = None,
    avionics_dims: tuple[float, float, float] | None = None,
) -> tuple[Box, Box, Box]:
    """Generate basic interior space region boxes for payload, battery, and avionics."""
    center_z = fuselage_height / 2.0
    
    p_len, p_w, p_h = payload_dims if payload_dims else (250.0, fuselage_width * 0.7, fuselage_height * 0.6)
    payload = Box(p_len, p_w, p_h)
    payload = payload.translate((fuselage_length * 0.25, 0.0, center_z))
    
    b_len, b_w, b_h = battery_dims if battery_dims else (200.0, fuselage_width * 0.7, fuselage_height * 0.5)
    battery = Box(b_len, b_w, b_h)
    battery = battery.translate((fuselage_length * 0.45, 0.0, center_z))
    
    a_len, a_w, a_h = avionics_dims if avionics_dims else (180.0, fuselage_width * 0.7, fuselage_height * 0.5)
    avionics = Box(a_len, a_w, a_h)
    avionics = avionics.translate((fuselage_length * 0.65, 0.0, center_z))
    
    return payload, battery, avionics


def generate_aircraft(params: Mapping[str, Any]) -> Any:
    """Orchestrate complete aircraft synthesis assembly using AssemblyHelper."""
    asm = AssemblyHelper("parametric_aircraft")
    
    fuse_len = params.get("fuselage_length", 1500.0)
    fuse_w = params.get("fuselage_width", 220.0)
    fuse_h = params.get("fuselage_height", 270.0)
    nose_len = params.get("nose_length", 300.0)
    tail_len = params.get("tail_cone_length", 450.0)
    cross_sec = params.get("cross_section_type", "ellipse")
    
    # 1. Fuselage
    fuselage = build_fuselage(fuse_len, fuse_w, fuse_h, nose_len, tail_len, cross_sec)
    asm.add(fuselage, "fuselage")
    
    # 2. Main Wing
    wing_span = params.get("wing_span", 2000.0)
    wing_root_c = params.get("wing_root_chord", 250.0)
    wing_tip_c = params.get("wing_tip_chord", 125.0)
    wing_sweep = params.get("wing_sweep_deg", 0.0)
    wing_dihedral = params.get("wing_dihedral_deg", 3.0)
    wing_incidence = params.get("wing_incidence_deg", 2.0)
    wing_root_airfoil = params.get("wing_root_airfoil", "clarky")
    wing_tip_airfoil = params.get("wing_tip_airfoil", "clarky")
    wing_le_x = params.get("wing_leading_edge_x", 400.0)
    
    wing_pos_type = params.get("wing_position", "high")
    if wing_pos_type == "high":
        wing_z = fuse_h - 10.0
    elif wing_pos_type == "low":
        wing_z = 20.0
    else:
        wing_z = fuse_h / 2.0
        
    left_wing, right_wing = build_wing(
        wing_span, wing_root_c, wing_tip_c, wing_sweep, wing_dihedral, 
        wing_incidence, wing_root_airfoil, wing_tip_airfoil, wing_le_x, wing_z
    )
    asm.add(left_wing, "left_wing")
    asm.add(right_wing, "right_wing")
    
    # 3. Stabilizers
    ht_span = params.get("ht_span", 400.0)
    ht_root_c = params.get("ht_root_chord", 120.0)
    ht_tip_c = params.get("ht_tip_chord", 80.0)
    ht_sweep = params.get("ht_sweep_deg", 5.0)
    ht_incidence = params.get("ht_incidence_deg", 0.0)
    ht_airfoil = params.get("ht_airfoil", "naca0012")
    
    vt_height = params.get("vt_height", 250.0)
    vt_root_c = params.get("vt_root_chord", 150.0)
    vt_tip_c = params.get("vt_tip_chord", 90.0)
    vt_sweep = params.get("vt_sweep_deg", 20.0)
    vt_airfoil = params.get("vt_airfoil", "naca0012")
    
    tail_start_x = fuse_len - max(ht_root_c, vt_root_c) - 30.0
    tail_z = fuse_h / 2.0
    
    left_ht, right_ht = build_horizontal_tail(
        ht_span, ht_root_c, ht_tip_c, ht_sweep, ht_incidence, ht_airfoil, tail_start_x, tail_z
    )
    asm.add(left_ht, "left_horizontal_tail")
    asm.add(right_ht, "right_horizontal_tail")
    
    v_tail = build_vertical_tail(
        vt_height, vt_root_c, vt_tip_c, vt_sweep, vt_airfoil, tail_start_x, tail_z
    )
    asm.add(v_tail, "vertical_tail")
    
    # 4. Propulsion
    prop_diam = params.get("propeller_diameter", 300.0)
    prop_pitch = params.get("propeller_pitch", 100.0)
    prop_layout = params.get("propulsion_layout", "pusher")
    
    if prop_layout == "pusher":
        prop_x = fuse_len
    else:
        prop_x = 0.0
        
    mount, motor, propeller = build_propulsion(
        prop_diam, prop_pitch, prop_x, 0.0, fuse_h / 2.0, 0.0, prop_layout, fuse_h
    )
    asm.add(mount, "motor_mount")
    asm.add(motor, "motor_envelope")
    asm.add(propeller, "propeller")
    
    # 5. Compartment Envelopes
    payload_dims = params.get("payload_bay_dimensions")
    battery_dims = params.get("battery_bay_dimensions")
    avionics_dims = params.get("avionics_bay_dimensions")
    payload, battery, avionics = build_internal_envelopes(
        fuse_len, fuse_w, fuse_h, payload_dims, battery_dims, avionics_dims
    )
    asm.add(payload, "payload_envelope")
    asm.add(battery, "battery_envelope")
    asm.add(avionics, "avionics_envelope")
    
    return asm.build()


def generate_aircraft_from_spec(spec: AircraftSpecification) -> Any:
    """Map engineering specification to geometry parameters and compile CAD."""
    import re
    import sys
    from cadpy.requirements import validate_aircraft_specification

    # 1. Airfoil validation
    def validate_airfoil(name: str) -> None:
        n = name.lower().strip()
        if "clark" in n:
            return
        match = re.match(r"^naca\s*(\d{4})$", n)
        if match:
            return
        raise ValueError(
            f"Unsupported airfoil: {name}\n"
            f"Available: Clark Y, NACA 4-digit airfoils (e.g. NACA 0012, NACA 4412)"
        )

    if spec.wing.root_airfoil.status != "UNKNOWN" and spec.wing.root_airfoil.value:
        validate_airfoil(spec.wing.root_airfoil.value)
    if spec.wing.tip_airfoil.status != "UNKNOWN" and spec.wing.tip_airfoil.value:
        validate_airfoil(spec.wing.tip_airfoil.value)
    if spec.horizontal_tail.airfoil.status != "UNKNOWN" and spec.horizontal_tail.airfoil.value:
        validate_airfoil(spec.horizontal_tail.airfoil.value)
    if spec.vertical_tail.airfoil.status != "UNKNOWN" and spec.vertical_tail.airfoil.value:
        validate_airfoil(spec.vertical_tail.airfoil.value)

    # 2. Validation check
    cad_blocking_errors = []
    non_cad_blocking_errors = []
    
    raw_errors = validate_aircraft_specification(spec)
    for err in raw_errors:
        err_lower = err.lower()
        is_non_blocking = (
            "takeoff mass" in err_lower
            or "mtow" in err_lower
            or "weight" in err_lower
            or "mass" in err_lower
            or "speed" in err_lower
            or "velocity" in err_lower
            or "range" in err_lower
            or "endurance" in err_lower
            or "performance" in err_lower
            or "takeoff roll" in err_lower
            or "flight time" in err_lower
            or "static margin" in err_lower
        )
        if is_non_blocking:
            non_cad_blocking_errors.append(err)
        else:
            cad_blocking_errors.append(err)

    # Directly scan spec.conflicts to capture non-blocking conflicts not reported by validate_aircraft_specification
    for conf in spec.conflicts:
        conf_lower = conf.lower()
        is_cad_blocking = any(c in conf_lower for c in ["span", "chord", "length", "width", "height", "airfoil", "position", "layout", "tail_configuration"])
        err_msg = f"Conflict: {conf}"
        if is_cad_blocking:
            if err_msg not in cad_blocking_errors:
                cad_blocking_errors.append(err_msg)
        else:
            if err_msg not in non_cad_blocking_errors:
                non_cad_blocking_errors.append(err_msg)

    if cad_blocking_errors:
        raise ValueError(f"Specification validation failed: {cad_blocking_errors}")

    # 3. Check tail configuration compatibility
    if spec.configuration.tail_configuration.status != "UNKNOWN" and spec.configuration.tail_configuration.value:
        tail_val = spec.configuration.tail_configuration.value.lower()
        if "conventional" not in tail_val:
            raise ValueError(f"Unsupported tail configuration: {spec.configuration.tail_configuration.value}. Only 'Conventional' tail is supported.")

    # 4. Parameters mapping
    params = {}
    manifest_info = {}

    def map_param(cad_key: str, req_field: Any, transform_fn=None):
        if req_field.status != "UNKNOWN" and req_field.value is not None:
            val = req_field.value
            if transform_fn:
                val = transform_fn(val)
            params[cad_key] = val
            manifest_info[cad_key] = {
                "value": val,
                "unit": req_field.unit,
                "source": req_field.source,
                "section": req_field.section,
                "status": req_field.status,
                "original_value": req_field.original_value,
                "original_unit": req_field.original_unit,
            }

    # Configuration mapping
    def map_wing_position(val):
        v = val.lower().strip()
        if "high" in v:
            return "high"
        elif "low" in v:
            return "low"
        else:
            return "mid"

    def map_propulsion_layout(val):
        v = val.lower().strip()
        if "pusher" in v:
            return "pusher"
        else:
            return "tractor"

    map_param("wing_position", spec.configuration.wing_position, map_wing_position)
    map_param("propulsion_layout", spec.configuration.propulsion_layout, map_propulsion_layout)
    map_param("cross_section_type", spec.fuselage.cross_section_type)

    # Wing
    map_param("wing_span", spec.wing.span)
    map_param("wing_root_chord", spec.wing.root_chord)
    map_param("wing_tip_chord", spec.wing.tip_chord)
    map_param("wing_sweep_deg", spec.wing.sweep)
    map_param("wing_dihedral_deg", spec.wing.dihedral)
    map_param("wing_incidence_deg", spec.wing.incidence)
    map_param("wing_root_airfoil", spec.wing.root_airfoil)
    map_param("wing_tip_airfoil", spec.wing.tip_airfoil)

    # Fuselage
    map_param("fuselage_length", spec.fuselage.length)
    map_param("fuselage_width", spec.fuselage.width)
    map_param("fuselage_height", spec.fuselage.height)
    map_param("nose_length", spec.fuselage.nose_length)
    map_param("tail_cone_length", spec.fuselage.tail_cone_length)

    # Stabilizers
    map_param("ht_span", spec.horizontal_tail.span)
    map_param("ht_root_chord", spec.horizontal_tail.root_chord)
    map_param("ht_tip_chord", spec.horizontal_tail.tip_chord)
    map_param("ht_sweep_deg", spec.horizontal_tail.sweep)
    map_param("ht_incidence_deg", spec.horizontal_tail.incidence)
    map_param("ht_airfoil", spec.horizontal_tail.airfoil)

    map_param("vt_height", spec.vertical_tail.height)
    map_param("vt_root_chord", spec.vertical_tail.root_chord)
    map_param("vt_tip_chord", spec.vertical_tail.tip_chord)
    map_param("vt_sweep_deg", spec.vertical_tail.sweep)
    map_param("vt_airfoil", spec.vertical_tail.airfoil)

    # Propulsion
    map_param("propeller_diameter", spec.propulsion.propeller_diameter)
    map_param("propeller_pitch", spec.propulsion.propeller_pitch)

    # Internal bays dimensions mapping
    if spec.internal_bays.payload_bay.length.value is not None:
        params["payload_bay_dimensions"] = (
            spec.internal_bays.payload_bay.length.value,
            spec.internal_bays.payload_bay.width.value,
            spec.internal_bays.payload_bay.height.value,
        )
    if spec.internal_bays.battery_bay.length.value is not None:
        params["battery_bay_dimensions"] = (
            spec.internal_bays.battery_bay.length.value,
            spec.internal_bays.battery_bay.width.value,
            spec.internal_bays.battery_bay.height.value,
        )
    if spec.internal_bays.avionics_bay.length.value is not None:
        params["avionics_bay_dimensions"] = (
            spec.internal_bays.avionics_bay.length.value,
            spec.internal_bays.avionics_bay.width.value,
            spec.internal_bays.avionics_bay.height.value,
        )

    # 5. PRE-GENERATION CAD MANIFEST
    case_id = spec.identity.title.value or "FW-007"
    manifest = {
        "case_id": case_id,
        "parameters": manifest_info,
    }

    # 6. PRE-GENERATION SNAPSHOT
    print(f"\n=========================================", file=sys.stderr)
    print(f"CAD GENERATION SNAPSHOT - {case_id}", file=sys.stderr)
    print(f"=========================================", file=sys.stderr)
    print(f"Source: Part 1 engineering specification", file=sys.stderr)
    print(f"Configuration:", file=sys.stderr)
    print(f"  Wing Position: {params.get('wing_position', 'default (high)')}", file=sys.stderr)
    print(f"  Propulsion Layout: {params.get('propulsion_layout', 'default (pusher)')}", file=sys.stderr)
    print(f"Wing:", file=sys.stderr)
    print(f"  Span: {params.get('wing_span', 'default')} mm", file=sys.stderr)
    print(f"  Root Chord: {params.get('wing_root_chord', 'default')} mm", file=sys.stderr)
    print(f"  Tip Chord: {params.get('wing_tip_chord', 'default')} mm", file=sys.stderr)
    print(f"  Dihedral: {params.get('wing_dihedral_deg', 'default')} deg", file=sys.stderr)
    print(f"  Incidence: {params.get('wing_incidence_deg', 'default')} deg", file=sys.stderr)
    print(f"  Root Airfoil: {params.get('wing_root_airfoil', 'default')}", file=sys.stderr)
    print(f"  Tip Airfoil: {params.get('wing_tip_airfoil', 'default')}", file=sys.stderr)
    print(f"Fuselage:", file=sys.stderr)
    print(f"  Length: {params.get('fuselage_length', 'default')} mm", file=sys.stderr)
    print(f"  Width: {params.get('fuselage_width', 'default')} mm", file=sys.stderr)
    print(f"  Height: {params.get('fuselage_height', 'default')} mm", file=sys.stderr)
    print(f"Tail:", file=sys.stderr)
    print(f"  HT Span: {params.get('ht_span', 'default')} mm", file=sys.stderr)
    print(f"  VT Height: {params.get('vt_height', 'default')} mm", file=sys.stderr)
    print(f"Propulsion:", file=sys.stderr)
    print(f"  Propeller Diameter: {params.get('propeller_diameter', 'default')} mm", file=sys.stderr)
    print(f"  Propeller Pitch: {params.get('propeller_pitch', 'default')} mm", file=sys.stderr)
    print(f"=========================================\n", file=sys.stderr)

    # 7. Generate shape using foundation
    shape = generate_aircraft(params)

    # 8. Post-Generation Validation
    if hasattr(shape, "volume") and shape.volume <= 0:
        raise ValueError("Generated aircraft CAD has zero or negative volume.")

    # Validate that conventional tail geometry works: checking children labels
    child_labels = [getattr(c, "label", "") for c in getattr(shape, "children", [])]
    expected_labels = [
        "fuselage",
        "left_wing",
        "right_wing",
        "left_horizontal_tail",
        "right_horizontal_tail",
        "vertical_tail",
        "motor_mount",
        "motor_envelope",
        "propeller",
        "payload_envelope",
        "battery_envelope",
        "avionics_envelope",
    ]
    for exp in expected_labels:
        if not any(exp in lbl for lbl in child_labels):
            raise ValueError(f"Missing expected child component: {exp} (Found labels: {child_labels})")

    # 9. Dimensional Validation with tolerancing
    dim_validation = []
    validation_warnings = []

    def check_dim(name: str, required: float, generated: float, tolerance: float):
        dev = abs(generated - required)
        passed = dev <= tolerance
        result = "PASS" if passed else "FAIL"
        dim_validation.append({
            "parameter": name,
            "required": required,
            "generated": generated,
            "deviation": dev,
            "tolerance": tolerance,
            "result": result
        })
        if not passed:
            validation_warnings.append(
                f"Dimensional validation warning for {name}: "
                f"required {required}, generated {generated} (deviation {dev} > tolerance {tolerance})"
            )

    left_wing = next((c for c in shape.children if "left_wing" in getattr(c, "label", "")), None)
    right_wing = next((c for c in shape.children if "right_wing" in getattr(c, "label", "")), None)
    if left_wing and right_wing:
        wing_span_gen = right_wing.bounding_box().max.Y - left_wing.bounding_box().min.Y
        check_dim("overall wing span", params.get("wing_span", 2000.0), wing_span_gen, 1.0)
        left_span = abs(left_wing.bounding_box().min.Y)
        right_span = abs(right_wing.bounding_box().max.Y)
        check_dim("left wing span", params.get("wing_span", 2000.0) / 2, left_span, 1.0)
        check_dim("right wing span", params.get("wing_span", 2000.0) / 2, right_span, 1.0)

    fuselage_obj = next((c for c in shape.children if "fuselage" in getattr(c, "label", "")), None)
    if fuselage_obj:
        fuse_len_gen = fuselage_obj.bounding_box().size.X
        check_dim("fuselage length", params.get("fuselage_length", 1500.0), fuse_len_gen, 1.0)
        fuse_w_gen = fuselage_obj.bounding_box().size.Y
        check_dim("fuselage width", params.get("fuselage_width", 180.0), fuse_w_gen, 1.0)
        fuse_h_gen = fuselage_obj.bounding_box().size.Z
        check_dim("fuselage height", params.get("fuselage_height", 160.0), fuse_h_gen, 1.0)

    left_ht = next((c for c in shape.children if "left_horizontal_tail" in getattr(c, "label", "")), None)
    right_ht = next((c for c in shape.children if "right_horizontal_tail" in getattr(c, "label", "")), None)
    if left_ht and right_ht:
        ht_span_gen = right_ht.bounding_box().max.Y - left_ht.bounding_box().min.Y
        check_dim("horizontal tail span", params.get("ht_span", 400.0), ht_span_gen, 1.0)

    vt_obj = next((c for c in shape.children if "vertical_tail" in getattr(c, "label", "")), None)
    if vt_obj:
        check_dim("vertical tail height", params.get("vt_height", 250.0), vt_obj.bounding_box().size.Z, 1.0)

    propeller_obj = next((c for c in shape.children if "propeller" in getattr(c, "label", "")), None)
    if propeller_obj:
        check_dim("propeller diameter", params.get("propeller_diameter", 300.0), propeller_obj.bounding_box().size.Y, 1.0)

    payload_bay = next((c for c in shape.children if "payload_envelope" in getattr(c, "label", "")), None)
    if payload_bay and spec.internal_bays.payload_bay.length.value:
        check_dim("payload bay length", spec.internal_bays.payload_bay.length.value, payload_bay.bounding_box().size.X, 1.0)
        check_dim("payload bay width", spec.internal_bays.payload_bay.width.value, payload_bay.bounding_box().size.Y, 1.0)
        check_dim("payload bay height", spec.internal_bays.payload_bay.height.value, payload_bay.bounding_box().size.Z, 1.0)

    # 10. Requirement-to-CAD Traceability Mapping
    traceability = {
        "REQ-WING-SPAN": {
            "requirement": "wing.span",
            "value": spec.wing.span.value,
            "cad_parameter": "wing_span",
            "components": ["left_wing", "right_wing"]
        },
        "REQ-WING-ROOT-CHORD": {
            "requirement": "wing.root_chord",
            "value": spec.wing.root_chord.value,
            "cad_parameter": "wing_root_chord",
            "components": ["left_wing", "right_wing"]
        },
        "REQ-WING-TIP-CHORD": {
            "requirement": "wing.tip_chord",
            "value": spec.wing.tip_chord.value,
            "cad_parameter": "wing_tip_chord",
            "components": ["left_wing", "right_wing"]
        },
        "REQ-FUSELAGE-LENGTH": {
            "requirement": "fuselage.length",
            "value": spec.fuselage.length.value,
            "cad_parameter": "fuselage_length",
            "components": ["fuselage"]
        },
        "REQ-FUSELAGE-WIDTH": {
            "requirement": "fuselage.width",
            "value": spec.fuselage.width.value,
            "cad_parameter": "fuselage_width",
            "components": ["fuselage"]
        },
        "REQ-FUSELAGE-HEIGHT": {
            "requirement": "fuselage.height",
            "value": spec.fuselage.height.value,
            "cad_parameter": "fuselage_height",
            "components": ["fuselage"]
        },
        "REQ-HT-SPAN": {
            "requirement": "horizontal_tail.span",
            "value": spec.horizontal_tail.span.value,
            "cad_parameter": "ht_span",
            "components": ["left_horizontal_tail", "right_horizontal_tail"]
        },
        "REQ-VT-HEIGHT": {
            "requirement": "vertical_tail.height",
            "value": spec.vertical_tail.height.value,
            "cad_parameter": "vt_height",
            "components": ["vertical_tail"]
        },
        "REQ-PROPELLER-DIAMETER": {
            "requirement": "propulsion.propeller_diameter",
            "value": spec.propulsion.propeller_diameter.value,
            "cad_parameter": "propeller_diameter",
            "components": ["propeller"]
        }
    }

    # 10.5 STRUCTURAL SYNTHESIS LAYER
    from cadpy.structure import (
        StructuralProfile,
        StructuralComponentMetadata,
        synthesize_wing_structure,
        synthesize_fuselage_structure,
        synthesize_tail_structure,
        synthesize_vertical_tail_structure,
        build_wing_fuselage_attachment,
        validate_structure
    )

    # Ingest structural profile
    prof = StructuralProfile(
        wing_primary_spar_chord_ratio=params.get("wing_primary_spar_chord_ratio", 0.25),
        wing_secondary_spar_chord_ratio=params.get("wing_secondary_spar_chord_ratio", 0.65),
        wing_spar_thickness=params.get("wing_spar_thickness", 3.0),
        wing_rib_spacing=params.get("wing_rib_spacing", 120.0),
        wing_rib_thickness=params.get("wing_rib_thickness", 2.5),
        fuselage_former_spacing=params.get("fuselage_former_spacing", 150.0),
        fuselage_former_thickness=params.get("fuselage_former_thickness", 4.0),
        fuselage_longeron_thickness=params.get("fuselage_longeron_thickness", 6.0),
        tail_spar_chord_ratio=params.get("tail_spar_chord_ratio", 0.35),
        tail_spar_thickness=params.get("tail_spar_thickness", 2.0),
        tail_rib_spacing=params.get("tail_rib_spacing", 80.0),
        tail_rib_thickness=params.get("tail_rib_thickness", 2.0),
    )

    # Extract original shapes
    left_wing_solid = next(c for c in shape.children if "left_wing" in getattr(c, "label", ""))
    right_wing_solid = next(c for c in shape.children if "right_wing" in getattr(c, "label", ""))
    fuselage_solid = next(c for c in shape.children if "fuselage" in getattr(c, "label", ""))
    left_ht_solid = next(c for c in shape.children if "left_horizontal_tail" in getattr(c, "label", ""))
    right_ht_solid = next(c for c in shape.children if "right_horizontal_tail" in getattr(c, "label", ""))
    vt_solid = next(c for c in shape.children if "vertical_tail" in getattr(c, "label", ""))

    payload_bay = next((c for c in shape.children if "payload_envelope" in getattr(c, "label", "")), None)
    battery_bay = next((c for c in shape.children if "battery_envelope" in getattr(c, "label", "")), None)
    avionics_bay = next((c for c in shape.children if "avionics_envelope" in getattr(c, "label", "")), None)

    # Geometrical coordinates matching generate_aircraft
    fuse_len = params.get("fuselage_length", 1500.0)
    fuse_w = params.get("fuselage_width", 180.0)
    fuse_h = params.get("fuselage_height", 160.0)

    wing_span = params.get("wing_span", 2000.0)
    wing_root_c = params.get("wing_root_chord", 250.0)
    wing_tip_c = params.get("wing_tip_chord", 125.0)
    wing_sweep = params.get("wing_sweep_deg", 0.0)
    wing_dihedral = params.get("wing_dihedral_deg", 3.0)
    wing_le_x = params.get("wing_leading_edge_x", 400.0)
    wing_pos_type = params.get("wing_position", "high")
    if wing_pos_type == "high":
        wing_z = fuse_h - 10.0
    elif wing_pos_type == "low":
        wing_z = 20.0
    else:
        wing_z = fuse_h / 2.0

    ht_span = params.get("ht_span", 600.0)
    ht_root_c = params.get("ht_root_chord", 180.0)
    ht_tip_c = params.get("ht_tip_chord", 120.0)
    ht_sweep = params.get("ht_sweep_deg", 5.0)

    vt_height = params.get("vt_height", 250.0)
    vt_root_c = params.get("vt_root_chord", 150.0)
    vt_tip_c = params.get("vt_tip_chord", 90.0)
    vt_sweep = params.get("vt_sweep_deg", 20.0)

    tail_start_x = fuse_len - max(ht_root_c, vt_root_c) - 30.0
    tail_z = fuse_h / 2.0

    # Build structures
    structural_components = []
    struct_registry = {}
    
    # Wings
    structural_components.extend(
        synthesize_wing_structure(
            left_wing_solid, wing_span, wing_root_c,
            wing_tip_c, wing_sweep,
            wing_dihedral, wing_le_x, wing_z, True, prof, struct_registry
        )
    )
    structural_components.extend(
        synthesize_wing_structure(
            right_wing_solid, wing_span, wing_root_c,
            wing_tip_c, wing_sweep,
            wing_dihedral, wing_le_x, wing_z, False, prof, struct_registry
        )
    )

    # Fuselage (formers, longerons, firewall)
    structural_components.extend(
        synthesize_fuselage_structure(
            fuselage_solid, fuse_len, fuse_w, fuse_h, prof, struct_registry,
            payload_bay, battery_bay, avionics_bay,
            propulsion_layout=params.get("propulsion_layout", "tractor")
        )
    )

    # Tails
    structural_components.extend(
        synthesize_tail_structure(
            left_ht_solid, ht_span, ht_root_c, ht_tip_c, ht_sweep,
            tail_start_x, tail_z, True, prof, "HorizontalTail", struct_registry
        )
    )
    structural_components.extend(
        synthesize_tail_structure(
            right_ht_solid, ht_span, ht_root_c, ht_tip_c, ht_sweep,
            tail_start_x, tail_z, False, prof, "HorizontalTail", struct_registry
        )
    )
    structural_components.extend(
        synthesize_vertical_tail_structure(
            vt_solid, vt_height, vt_root_c, vt_tip_c, vt_sweep,
            tail_start_x, tail_z, prof, struct_registry
        )
    )

    # Wing Attachment
    attachment_meta = StructuralComponentMetadata(
        component_id="Wing_Fuselage_Attachment",
        component_type="ATTACHMENT",
        parent_component="Fuselage",
        structural_role="WING_MOUNT_CARRY_THROUGH"
    )
    wing_attach = build_wing_fuselage_attachment(
        fuselage_solid, wing_z, fuse_w, fuse_h, wing_le_x, wing_root_c, attachment_meta, struct_registry
    )
    if wing_attach.volume > 0:
        structural_components.append(wing_attach)

    # Calculate Structural Mass and CG (Prototype estimate based on reference material assumption)
    total_struct_mass = 0.0
    sum_mx = 0.0
    sum_my = 0.0
    sum_mz = 0.0
    
    # Reference material assumption: 150 kg/m^3 is 0.00015 g/mm^3 (Balsa Wood reference)
    density = params.get("structural_material_density", 0.00015)
    for comp in structural_components:
        label = comp.label
        vol = comp.volume
        comp_mass = vol * density
        if label not in struct_registry:
            struct_registry[label] = {}
        struct_registry[label]["volume_mm3"] = vol
        struct_registry[label]["material_density_g_mm3"] = density
        struct_registry[label]["estimated_mass_g"] = comp_mass
        total_struct_mass += comp_mass
        center = comp.center()
        sum_mx += center.X * comp_mass
        sum_my += center.Y * comp_mass
        sum_mz += center.Z * comp_mass

    cg_struct = (
        sum_mx / total_struct_mass if total_struct_mass > 0 else 0.0,
        sum_my / total_struct_mass if total_struct_mass > 0 else 0.0,
        sum_mz / total_struct_mass if total_struct_mass > 0 else 0.0,
    )

    # Ingest structural profile parameters to manifest
    manifest["structural_profile"] = {
        "wing_primary_spar_chord_ratio": {
            "value": prof.wing_primary_spar_chord_ratio,
            "source": "STRUCTURAL_RULE"
        },
        "wing_secondary_spar_chord_ratio": {
            "value": prof.wing_secondary_spar_chord_ratio,
            "source": "STRUCTURAL_RULE"
        },
        "wing_spar_thickness": {
            "value": prof.wing_spar_thickness,
            "source": "STRUCTURAL_RULE"
        },
        "wing_rib_spacing": {
            "value": prof.wing_rib_spacing,
            "source": "STRUCTURAL_RULE"
        },
        "wing_rib_thickness": {
            "value": prof.wing_rib_thickness,
            "source": "STRUCTURAL_RULE"
        },
        "fuselage_former_spacing": {
            "value": prof.fuselage_former_spacing,
            "source": "STRUCTURAL_RULE"
        },
        "fuselage_former_thickness": {
            "value": prof.fuselage_former_thickness,
            "source": "STRUCTURAL_RULE"
        },
        "fuselage_longeron_thickness": {
            "value": prof.fuselage_longeron_thickness,
            "source": "STRUCTURAL_RULE"
        },
        "reference_material_density_g_mm3": {
            "value": density,
            "source": "REFERENCE_MATERIAL"
        },
        "estimated_structural_mass_g": {
            "value": total_struct_mass,
            "source": "DERIVED"
        },
        "structural_cg_location": {
            "value": cg_struct,
            "source": "DERIVED"
        }
    }

    # Verify structural integrity
    ext_components = {
        "left_wing": left_wing_solid,
        "right_wing": right_wing_solid,
        "fuselage": fuselage_solid,
    }
    struct_errors = validate_structure(
        ext_components, structural_components, payload_bay, battery_bay, avionics_bay
    )

    # Classify structural errors
    for err in struct_errors:
        err_lower = err.lower()
        is_blocking = (
            "obstructs" in err_lower
            or "degenerate" in err_lower
            or "zero volume" in err_lower
            or "missing" in err_lower
            or "exceeds parent" in err_lower
        )
        if is_blocking:
            cad_blocking_errors.append(err)
        else:
            non_cad_blocking_errors.append(err)

    if cad_blocking_errors:
        raise ValueError(f"Structural assembly failed: {cad_blocking_errors}")

    # Reassemble complete aircraft with external and structural parts
    asm = AssemblyHelper("parametric_aircraft")
    for child in shape.children:
        asm.add(child, child.label)
    for comp in structural_components:
        asm.add(comp, comp.label)
        
    final_shape = asm.build()

    # Verify external geometry remains unchanged (Bounding box check)
    ext_boxes_before = {c.label: c.bounding_box() for c in shape.children if not getattr(c, "metadata", {})}
    ext_boxes_after = {c.label: c.bounding_box() for c in final_shape.children if not getattr(c, "metadata", {})}
    for label, box_before in ext_boxes_before.items():
        box_after = ext_boxes_after.get(label)
        if not box_after:
            raise ValueError(f"External component {label} was lost during structural assembly.")
        d_x = abs(box_before.size.X - box_after.size.X)
        d_y = abs(box_before.size.Y - box_after.size.Y)
        d_z = abs(box_before.size.Z - box_after.size.Z)
        if d_x > 1e-3 or d_y > 1e-3 or d_z > 1e-3:
            raise ValueError(
                f"External geometry component {label} was modified during structural synthesis "
                f"(Bounding Box changed by X:{d_x:.4f}, Y:{d_y:.4f}, Z:{d_z:.4f})"
            )

    # Keep track of external component dictionary
    ext_dict = {c.label: c for c in shape.children}

    # Replace shape with the complete structural assembly
    shape = final_shape

    # 11. STEP Export to standard location
    import os
    from build123d import export_step
    os.makedirs("outputs", exist_ok=True)
    step_path = "outputs/FW-007_complete.step"
    export_step(shape, step_path)

    # 12. Create Structured Result
    all_validation_errors = cad_blocking_errors + non_cad_blocking_errors + validation_warnings
    
    result = CADGenerationResult(
        assembly=shape,
        manifest=manifest,
        validation_errors=all_validation_errors,
        output_files={"step": step_path},
        traceability=traceability,
        structural_components=structural_components,
        external_components=ext_dict
    )
    result.dimensional_validation = dim_validation
    result.cad_blocking_errors = cad_blocking_errors
    result.non_cad_blocking_errors = non_cad_blocking_errors

    return result


@dataclass
class CADGenerationResult:
    assembly: Any
    manifest: dict[str, Any]
    validation_errors: list[str]
    output_files: dict[str, str] = field(default_factory=dict)
    traceability: dict[str, Any] = field(default_factory=dict)
    structural_components: list[Any] = field(default_factory=list)
    external_components: dict[str, Any] = field(default_factory=dict)

    @property
    def structural_assembly(self) -> Any:
        return self.assembly


