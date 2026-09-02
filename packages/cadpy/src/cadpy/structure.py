"""Structural synthesis layer for parameterized aircraft airframes."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from build123d import *


@dataclass
class StructuralProfile:
    """Configurable structural rules and parameters for airframe synthesis."""
    # Wing rules
    wing_primary_spar_chord_ratio: float = 0.25
    wing_secondary_spar_chord_ratio: float = 0.65
    wing_spar_thickness: float = 3.0
    wing_rib_spacing: float = 120.0
    wing_rib_thickness: float = 2.5
    
    # Fuselage rules
    fuselage_former_spacing: float = 150.0
    fuselage_former_thickness: float = 4.0
    fuselage_longeron_thickness: float = 6.0
    
    # Tail rules
    tail_spar_chord_ratio: float = 0.35
    tail_spar_thickness: float = 2.0
    tail_rib_spacing: float = 80.0
    tail_rib_thickness: float = 2.0


@dataclass
class StructuralComponentMetadata:
    component_id: str
    component_type: str  # SPAR, RIB, FORMER, LONGERON, FIREWALL, ATTACHMENT
    parent_component: str
    structural_role: str
    source: str = "STRUCTURAL_RULE"
    generation_rule: str = "DEFAULT_RULE"
    material_origin: str = "UNKNOWN"


def label_structural_shape(shape: Any, meta: StructuralComponentMetadata, registry: dict[str, Any] | None = None) -> Any:
    """Helper to label shape with name and metadata."""
    shape.label = meta.component_id
    meta_dict = {
        "component_id": meta.component_id,
        "component_type": meta.component_type,
        "parent_component": meta.parent_component,
        "structural_role": meta.structural_role,
        "source": meta.source,
        "generation_rule": meta.generation_rule,
        "material_origin": meta.material_origin,
    }
    try:
        shape.metadata = meta_dict
    except Exception:
        pass
    if registry is not None:
        registry[meta.component_id] = meta_dict
    return shape


def build_wing_spar(
    span_half: float,
    root_chord: float,
    tip_chord: float,
    sweep_deg: float,
    dihedral_deg: float,
    leading_edge_x: float,
    root_z: float,
    chord_ratio: float,
    thickness: float,
    is_left: bool,
    wing_solid: Solid,
    meta: StructuralComponentMetadata,
    registry: dict[str, Any]
) -> Solid:
    """Generate a wing spar web conforming to dihedral, sweep, and local airfoil thickness."""
    y_sections = [0.0, span_half * 0.5, span_half]
    wires = []
    
    sweep_rad = math.radians(sweep_deg)
    dihedral_rad = math.radians(dihedral_deg)
    
    for y in y_sections:
        eta = y / span_half
        c = root_chord - (root_chord - tip_chord) * eta
        x = leading_edge_x + y * math.tan(sweep_rad) + chord_ratio * c
        z = root_z + y * math.tan(dihedral_rad)
        
        y_val = -y if is_left else y
        
        # Section perpendicular to Y-axis
        plane = Plane(origin=(x, y_val, z), x_dir=(1, 0, 0), z_dir=(0, 1, 0))
        with BuildSketch(plane) as s:
            Rectangle(thickness, c * 0.4)
        wires.append(s.wire().located(plane.location))
        
    draft_spar = Solid.make_loft(wires)
    # Boolean intersect to keep spar inside wing boundary
    spar = wing_solid & draft_spar
    return label_structural_shape(spar, meta, registry)


def build_wing_rib(
    span_half: float,
    root_chord: float,
    tip_chord: float,
    sweep_deg: float,
    dihedral_deg: float,
    leading_edge_x: float,
    root_z: float,
    y: float,
    thickness: float,
    is_left: bool,
    wing_solid: Solid,
    spars: list[Solid],
    meta: StructuralComponentMetadata,
    registry: dict[str, Any]
) -> Solid:
    """Generate a wing rib conforming to local airfoil profile and subtract spars."""
    eta = y / span_half
    c = root_chord - (root_chord - tip_chord) * eta
    x = leading_edge_x + y * math.tan(math.radians(sweep_deg)) + 0.5 * c
    z = root_z + y * math.tan(math.radians(dihedral_deg))
    
    y_val = -y if is_left else y
    
    # Intersect with box
    rib_box = Box(c * 1.5, thickness, c * 0.5)
    rib_box = rib_box.translate((x, y_val, z))
    rib = wing_solid & rib_box
    
    # Cut out holes for spars if they intersect
    for spar in spars:
        if rib.volume > 0 and spar.volume > 0:
            try:
                rib = rib - spar
            except Exception:
                pass
                
    return label_structural_shape(rib, meta, registry)


def synthesize_wing_structure(
    wing_solid: Solid,
    span: float,
    root_chord: float,
    tip_chord: float,
    sweep_deg: float,
    dihedral_deg: float,
    leading_edge_x: float,
    root_z: float,
    is_left: bool,
    profile: StructuralProfile,
    registry: dict[str, Any]
) -> list[Solid]:
    """Orchestrate wing structural synthesis."""
    span_half = span / 2.0
    parent_name = "LeftWing" if is_left else "RightWing"
    side_suffix = "Left" if is_left else "Right"
    
    components = []
    
    # 1. Spars
    main_spar_meta = StructuralComponentMetadata(
        component_id=f"MainWing_{side_suffix}_MainSpar",
        component_type="SPAR",
        parent_component=parent_name,
        structural_role="PRIMARY_LOAD_PATH",
        generation_rule="primary_spar_chord_ratio"
    )
    main_spar = build_wing_spar(
        span_half, root_chord, tip_chord, sweep_deg, dihedral_deg,
        leading_edge_x, root_z, profile.wing_primary_spar_chord_ratio,
        profile.wing_spar_thickness, is_left, wing_solid, main_spar_meta, registry
    )
    if main_spar.volume > 0:
        components.append(main_spar)
        
    rear_spar_meta = StructuralComponentMetadata(
        component_id=f"MainWing_{side_suffix}_RearSpar",
        component_type="SPAR",
        parent_component=parent_name,
        structural_role="SECONDARY_LOAD_PATH",
        generation_rule="secondary_spar_chord_ratio"
    )
    rear_spar = build_wing_spar(
        span_half, root_chord, tip_chord, sweep_deg, dihedral_deg,
        leading_edge_x, root_z, profile.wing_secondary_spar_chord_ratio,
        profile.wing_spar_thickness, is_left, wing_solid, rear_spar_meta, registry
    )
    if rear_spar.volume > 0:
        components.append(rear_spar)

    # 2. Ribs placement spacing
    rib_y_coords = []
    # Root rib at y=5mm (to offset slightly from fuselage connection)
    rib_y_coords.append(5.0)
    
    y_curr = profile.wing_rib_spacing
    while y_curr < span_half - 15.0:
        rib_y_coords.append(y_curr)
        y_curr += profile.wing_rib_spacing
        
    # Tip rib
    rib_y_coords.append(span_half - 2.0)
    
    spars_list = [c for c in components if c.label in registry and registry[c.label]["component_type"] == "SPAR"]
    
    for idx, y_val in enumerate(rib_y_coords):
        role = "ROOT_RIB" if idx == 0 else ("TIP_RIB" if idx == len(rib_y_coords)-1 else "INTERMEDIATE_RIB")
        rib_meta = StructuralComponentMetadata(
            component_id=f"MainWing_{side_suffix}_Rib_{idx:03d}",
            component_type="RIB",
            parent_component=parent_name,
            structural_role=role,
            generation_rule="rib_spacing"
        )
        rib = build_wing_rib(
            span_half, root_chord, tip_chord, sweep_deg, dihedral_deg,
            leading_edge_x, root_z, y_val, profile.wing_rib_thickness,
            is_left, wing_solid, spars_list, rib_meta, registry
        )
        if rib.volume > 0:
            components.append(rib)
            
    return components


def synthesize_fuselage_structure(
    fuselage_solid: Solid,
    length: float,
    width: float,
    height: float,
    profile: StructuralProfile,
    registry: dict[str, Any],
    payload_envelope: Box | None = None,
    battery_envelope: Box | None = None,
    avionics_envelope: Box | None = None,
    propulsion_layout: str = "tractor"
) -> list[Solid]:
    """Synthesize fuselage formers and longerons, and subtract compartment bays."""
    components = []
    
    # 1. Formers placement along X
    former_x_coords = []
    nose_x = length * 0.15
    payload_front = length * 0.20
    payload_back = length * 0.35
    battery_back = length * 0.55
    wing_mount_x = length * 0.40
    tail_mount_x = length * 0.85
    
    former_x_coords.extend([nose_x, payload_front, payload_back, wing_mount_x, battery_back, tail_mount_x])
    
    # Former bulkheads
    for idx, x in enumerate(sorted(list(set(former_x_coords)))):
        role = "INTERMEDIATE_FORMER"
        if abs(x - nose_x) < 1e-4:
            role = "NOSE_FORMER"
        elif abs(x - wing_mount_x) < 1e-4:
            role = "WING_ATTACH_FORMER"
        elif abs(x - tail_mount_x) < 1e-4:
            role = "TAIL_ATTACH_FORMER"
            
        former_meta = StructuralComponentMetadata(
            component_id=f"Fuselage_Former_{idx:03d}",
            component_type="FORMER",
            parent_component="Fuselage",
            structural_role=role,
            generation_rule="former_spacing"
        )
        
        former_box = Box(profile.fuselage_former_thickness, width * 1.5, height * 1.5)
        former_box = former_box.translate((x, 0.0, height / 2.0))
        former = fuselage_solid & former_box
        
        # Subtract bays to maintain access
        for envelope in [payload_envelope, battery_envelope, avionics_envelope]:
            if envelope and former.volume > 0:
                try:
                    former = former - envelope
                except Exception:
                    pass
                    
        if former.volume > 0:
            components.append(label_structural_shape(former, former_meta, registry))
            
    # 2. Longerons
    longeron_thickness = profile.fuselage_longeron_thickness
    longeron_offsets = [
        ("UpperLeft", -width/2.0 * 0.65, height * 0.8),
        ("UpperRight", width/2.0 * 0.65, height * 0.8),
        ("LowerLeft", -width/2.0 * 0.65, height * 0.25),
        ("LowerRight", width/2.0 * 0.65, height * 0.25),
    ]
    
    for name, dy, dz in longeron_offsets:
        longeron_meta = StructuralComponentMetadata(
            component_id=f"Fuselage_Longeron_{name}",
            component_type="LONGERON",
            parent_component="Fuselage",
            structural_role="LONGERON_BEAM",
            generation_rule="longeron_count"
        )
        
        beam = Box(length * 1.2, longeron_thickness, longeron_thickness)
        beam = beam.translate((length / 2.0, dy, dz))
        longeron = fuselage_solid & beam
        
        # Subtract bays to prevent collision
        for envelope in [payload_envelope, battery_envelope, avionics_envelope]:
            if envelope and longeron.volume > 0:
                try:
                    longeron = longeron - envelope
                except Exception:
                    pass
                    
        if longeron.volume > 0:
            components.append(label_structural_shape(longeron, longeron_meta, registry))
            
    # 3. Motor Firewall (Front bulkhead for tractor, rear bulkhead for pusher)
    firewall_meta = StructuralComponentMetadata(
        component_id="Motor_Firewall",
        component_type="FIREWALL",
        parent_component="Fuselage",
        structural_role="MOTOR_MOUNT_PLATE",
        generation_rule="propulsion_layout"
    )
    fw_x = 3.0 if str(propulsion_layout).lower().strip() == "tractor" else length - 3.0
    firewall_box = Box(6.0, width * 0.8, height * 0.8)
    firewall_box = firewall_box.translate((fw_x, 0.0, height / 2.0))
    firewall = fuselage_solid & firewall_box
    if firewall.volume > 0:
        components.append(label_structural_shape(firewall, firewall_meta, registry))
        
    return components


def synthesize_tail_structure(
    stabilizer_solid: Solid,
    span: float,
    root_chord: float,
    tip_chord: float,
    sweep_deg: float,
    leading_edge_x: float,
    root_z: float,
    is_left: bool,
    profile: StructuralProfile,
    parent_name: str,
    registry: dict[str, Any]
) -> list[Solid]:
    """Synthesize stabilizers spars and ribs structural components."""
    span_half = span / 2.0
    side = "Left" if is_left else "Right"
    components = []
    
    # 1. Spar
    spar_meta = StructuralComponentMetadata(
        component_id=f"{parent_name}_{side}_Spar",
        component_type="SPAR",
        parent_component=parent_name,
        structural_role="PRIMARY_LOAD_PATH",
        generation_rule="tail_spar_chord_ratio"
    )
    spar = build_wing_spar(
        span_half, root_chord, tip_chord, sweep_deg, 0.0,
        leading_edge_x, root_z, profile.tail_spar_chord_ratio,
        profile.tail_spar_thickness, is_left, stabilizer_solid, spar_meta, registry
    )
    if spar.volume > 0:
        components.append(spar)
        
    # 2. Ribs
    rib_y_coords = [5.0, span_half * 0.5, span_half - 2.0]
    spars_list = [c for c in components if c.label in registry and registry[c.label]["component_type"] == "SPAR"]
    
    for idx, y_val in enumerate(rib_y_coords):
        role = "ROOT_RIB" if idx == 0 else ("TIP_RIB" if idx == len(rib_y_coords)-1 else "INTERMEDIATE_RIB")
        rib_meta = StructuralComponentMetadata(
            component_id=f"{parent_name}_{side}_Rib_{idx:03d}",
            component_type="RIB",
            parent_component=parent_name,
            structural_role=role,
            generation_rule="tail_rib_spacing"
        )
        rib = build_wing_rib(
            span_half, root_chord, tip_chord, sweep_deg, 0.0,
            leading_edge_x, root_z, y_val, profile.tail_rib_thickness,
            is_left, stabilizer_solid, spars_list, rib_meta, registry
        )
        if rib.volume > 0:
            components.append(rib)
            
    return components


def build_vertical_tail_spar(
    height: float,
    root_chord: float,
    tip_chord: float,
    sweep_deg: float,
    leading_edge_x: float,
    root_z: float,
    chord_ratio: float,
    thickness: float,
    vt_solid: Solid,
    meta: StructuralComponentMetadata,
    registry: dict[str, Any]
) -> Solid:
    """Generate vertical stabilizer spar web conforming to sweep and twist profiles."""
    z_sections = [0.0, height * 0.5, height]
    wires = []
    
    sweep_rad = math.radians(sweep_deg)
    
    for z in z_sections:
        eta = z / height
        c = root_chord - (root_chord - tip_chord) * eta
        x = leading_edge_x + z * math.tan(sweep_rad) + chord_ratio * c
        
        plane = Plane(origin=(x, 0, root_z + z), x_dir=(1, 0, 0), z_dir=(0, 0, 1))
        with BuildSketch(plane) as s:
            Rectangle(thickness, c * 0.4)
        wires.append(s.wire().located(plane.location))
        
    draft_spar = Solid.make_loft(wires)
    spar = vt_solid & draft_spar
    return label_structural_shape(spar, meta, registry)


def build_vertical_tail_rib(
    height: float,
    root_chord: float,
    tip_chord: float,
    sweep_deg: float,
    leading_edge_x: float,
    root_z: float,
    z: float,
    thickness: float,
    vt_solid: Solid,
    spars: list[Solid],
    meta: StructuralComponentMetadata,
    registry: dict[str, Any]
) -> Solid:
    """Generate vertical stabilizer rib conforming to local chord profile and subtract spars."""
    eta = z / height
    c = root_chord - (root_chord - tip_chord) * eta
    x = leading_edge_x + z * math.tan(math.radians(sweep_deg)) + 0.5 * c
    
    rib_box = Box(c * 1.5, c * 0.5, thickness)
    rib_box = rib_box.translate((x, 0.0, root_z + z))
    rib = vt_solid & rib_box
    
    for spar in spars:
        if rib.volume > 0 and spar.volume > 0:
            try:
                rib = rib - spar
            except Exception:
                pass
                
    return label_structural_shape(rib, meta, registry)


def synthesize_vertical_tail_structure(
    vt_solid: Solid,
    height: float,
    root_chord: float,
    tip_chord: float,
    sweep_deg: float,
    leading_edge_x: float,
    root_z: float,
    profile: StructuralProfile,
    registry: dict[str, Any]
) -> list[Solid]:
    """Orchestrate vertical stabilizer structural synthesis."""
    components = []
    
    # 1. Spar
    spar_meta = StructuralComponentMetadata(
        component_id="VerticalTail_MainSpar",
        component_type="SPAR",
        parent_component="VerticalTail",
        structural_role="PRIMARY_LOAD_PATH",
        generation_rule="tail_spar_chord_ratio"
    )
    spar = build_vertical_tail_spar(
        height, root_chord, tip_chord, sweep_deg, leading_edge_x, root_z,
        profile.tail_spar_chord_ratio, profile.tail_spar_thickness, vt_solid, spar_meta, registry
    )
    if spar.volume > 0:
        components.append(spar)
        
    # 2. Ribs
    rib_z_coords = [5.0, height * 0.5, height - 2.0]
    spars_list = [c for c in components if c.label in registry and registry[c.label]["component_type"] == "SPAR"]
    
    for idx, z_val in enumerate(rib_z_coords):
        role = "ROOT_RIB" if idx == 0 else ("TIP_RIB" if idx == len(rib_z_coords)-1 else "INTERMEDIATE_RIB")
        rib_meta = StructuralComponentMetadata(
            component_id=f"VerticalTail_Rib_{idx:03d}",
            component_type="RIB",
            parent_component="VerticalTail",
            structural_role=role,
            generation_rule="tail_rib_spacing"
        )
        rib = build_vertical_tail_rib(
            height, root_chord, tip_chord, sweep_deg, leading_edge_x, root_z,
            z_val, profile.tail_rib_thickness, vt_solid, spars_list, rib_meta, registry
        )
        if rib.volume > 0:
            components.append(rib)
            
    return components


def build_wing_fuselage_attachment(
    fuselage_solid: Solid,
    wing_z: float,
    fuselage_width: float,
    fuselage_height: float,
    wing_le_x: float,
    wing_root_chord: float,
    meta: StructuralComponentMetadata,
    registry: dict[str, Any]
) -> Solid:
    """Generate carry-through structural attachment support connecting wing root to fuselage."""
    saddle = Box(wing_root_chord * 0.8, fuselage_width * 0.9, 12.0)
    saddle = saddle.translate((wing_le_x + wing_root_chord * 0.4, 0.0, wing_z - 6.0))
    attachment = fuselage_solid & saddle
    return label_structural_shape(attachment, meta, registry)


def validate_structure(
    external_components: Dict[str, Any],
    structural_components: List[Solid],
    payload_envelope: Box | None,
    battery_envelope: Box | None,
    avionics_envelope: Box | None
) -> List[str]:
    """Validate containment, attachment connection check, and bay envelope preservation."""
    errors = []
    
    # 1. Expected parts checks
    expected_types = {"SPAR", "RIB", "FORMER", "LONGERON"}
    found_types = {getattr(c, "metadata", {}).get("component_type") for c in structural_components if hasattr(c, "metadata")}
    missing = expected_types - found_types
    if missing:
        errors.append(f"Missing expected structural component types: {list(missing)}")
        
    # Check specific critical structural elements
    crucial_ids = ["Motor_Firewall", "VerticalTail_MainSpar"]
    found_ids = {getattr(c, "label", "") for c in structural_components}
    for cid in crucial_ids:
        if cid not in found_ids:
            errors.append(f"Critical structural element missing: {cid}")

    # 2. Geometry quality (Solid validity)
    for c in structural_components:
        cid = getattr(c, "label", "unnamed")
        if not hasattr(c, "volume") or c.volume <= 0:
            errors.append(f"Structural component has degenerate or zero volume: {cid}")
        bbox = c.bounding_box()
        if bbox.size.X <= 0 or bbox.size.Y <= 0 or bbox.size.Z <= 0:
            errors.append(f"Structural component has degenerate bounding box extents: {cid}")

    # 3. Containment check (spars/ribs inside wing boundary)
    wing_l_solid = external_components.get("left_wing")
    wing_r_solid = external_components.get("right_wing")
    fuse_solid = external_components.get("fuselage")
    
    for c in structural_components:
        cid = getattr(c, "label", "")
        # Since metadata might not be directly on shape, we check name patterns
        if "Spar" in cid or "Rib" in cid:
            parent_solid = wing_l_solid if "Left" in cid else wing_r_solid
            if "HorizontalTail" in cid:
                parent_solid = external_components.get("left_horizontal_tail") if "Left" in cid else external_components.get("right_horizontal_tail")
            elif "VerticalTail" in cid:
                parent_solid = external_components.get("vertical_tail")
                
            if parent_solid and c.volume > 0:
                p_bbox = parent_solid.bounding_box()
                c_bbox = c.bounding_box()
                if "VerticalTail" in cid:
                    if (c_bbox.min.Z < p_bbox.min.Z - 1.0 or c_bbox.max.Z > p_bbox.max.Z + 1.0):
                        errors.append(f"Structural element Z-boundary exceeds parent VerticalTail geometry: {cid}")
                else:
                    if (c_bbox.min.Y < p_bbox.min.Y - 1.0 or c_bbox.max.Y > p_bbox.max.Y + 1.0):
                        errors.append(f"Structural element Y-boundary exceeds parent wing/tail geometry: {cid}")
        elif "Former" in cid or "Longeron" in cid:
            if fuse_solid and c.volume > 0:
                p_bbox = fuse_solid.bounding_box()
                c_bbox = c.bounding_box()
                if (c_bbox.min.X < p_bbox.min.X - 1.0 or c_bbox.max.X > p_bbox.max.X + 1.0):
                    errors.append(f"Structural element X-boundary exceeds parent fuselage geometry: {cid}")

    # 4. Bay preservation: ensure that no former or longeron intersects with bay volumes
    for envelope, name in [(payload_envelope, "payload"), (battery_envelope, "battery"), (avionics_envelope, "avionics")]:
        if envelope:
            for c in structural_components:
                cid = getattr(c, "label", "")
                if "Former" in cid or "Longeron" in cid:
                    try:
                        overlap = c & envelope
                        if overlap.volume > 1.0:  # If overlap volume is greater than 1mm^3
                            errors.append(f"Structural component {cid} obstructs the {name} bay (overlap volume: {overlap.volume:.2f} mm3)")
                    except Exception:
                        pass
                        
    return errors
