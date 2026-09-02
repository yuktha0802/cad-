"""Shared CAD artifact generation runtime."""

__all__ = [
    "AssemblyHelper",
    "MateRelation",
    "MateTarget",
    "ensure_step_glb_artifact",
    "generate_aircraft",
    "generate_aircraft_from_spec",
    "CADGenerationResult",
    "StructuralProfile",
    "Requirement",
    "AircraftSpecification",
    "parse_aircraft_specification",
    "validate_aircraft_specification",
    "label_text",
    "label_shape",
    "target",
    "validate_step_glb_artifact",
    "ManufacturingProcess",
    "ProvenanceSource",
    "FabricationStrategy",
    "DecompositionStrategy",
    "JointType",
    "ManufacturingStatus",
    "ClassificationRule",
    "ManufacturingMaterial",
    "LaserCutProfile",
    "ThreeDPrintProfile",
    "ManufacturingProfile",
    "ManufacturingPart",
    "ManufacturingJoint",
    "FabricationGeometry",
    "FabricationGeometryGenerator",
    "FabricationGeometryValidator",
    "KerfCompensation",
    "KerfCompensator",
    "PlacedPart",
    "ManufacturingSheet",
    "SheetNester",
    "export_part_dxf",
    "export_part_svg",
    "export_sheet_dxf",
    "export_sheet_svg",
    "LaserManufacturingValidator",
    "generate_laser_manufacturing_pipeline",
    "ManufacturingClassifier",
    "ManufacturingClassificationValidator",
    "generate_manufacturing_part_id",
    "validate_laser_cut_profile",
    "validate_three_d_print_profile",
    "validate_manufacturing_profile",
    "PrintStatus",
    "SplitStatus",
    "SplitJointType",
    "PrintablePart",
    "PrintSplitRecord",
    "PartSplitter",
    "PrintablePartGenerator",
    "ThreeDPrintExporter",
    "ThreeDPrintValidator",
    "generate_3d_print_manufacturing_pipeline",
    "generate_complete_manufacturing_pipeline",
    "PrototypeReadinessStatus",
    "ValidationSeverity",
    "ManufacturingBOMItem",
    "ManufacturingBOM",
    "VirtualManufacturingAssembly",
    "ManufacturingValidationResult",
    "ManufacturingValidationEngine",
    "PipelinePhase",
    "PhaseState",
    "ExecutionMode",
    "ArtifactType",
    "PhaseExecutionRecord",
    "ArtifactRecord",
    "ArtifactRegistry",
    "DesignVersion",
    "PipelineContext",
    "DesignStudioPipeline",
    "create_manufacturing_part_from_structural_component",
    "get_prototype_laser_balsa_profile",
    "get_prototype_3d_print_profile",
    "create_prototype_manufacturing_profile",
    "build_manufacturing_manifest",
]


def __getattr__(name: str):
    if name in {
        "PipelinePhase",
        "PhaseState",
        "ExecutionMode",
        "ArtifactType",
        "PhaseExecutionRecord",
        "ArtifactRecord",
        "ArtifactRegistry",
        "DesignVersion",
        "PipelineContext",
        "DesignStudioPipeline",
    }:
        import cadpy.pipeline as pipe
        return getattr(pipe, name)
    if name in {
        "ManufacturingProcess",
        "ProvenanceSource",
        "FabricationStrategy",
        "DecompositionStrategy",
        "JointType",
        "ManufacturingStatus",
        "ClassificationRule",
        "ManufacturingMaterial",
        "LaserCutProfile",
        "ThreeDPrintProfile",
        "ManufacturingProfile",
        "ManufacturingPart",
        "ManufacturingJoint",
        "FabricationGeometry",
        "FabricationGeometryGenerator",
        "FabricationGeometryValidator",
        "KerfCompensation",
        "KerfCompensator",
        "PlacedPart",
        "ManufacturingSheet",
        "SheetNester",
        "export_part_dxf",
        "export_part_svg",
        "export_sheet_dxf",
        "export_sheet_svg",
        "LaserManufacturingValidator",
        "generate_laser_manufacturing_pipeline",
        "PrintStatus",
        "SplitStatus",
        "SplitJointType",
        "PrintablePart",
        "PrintSplitRecord",
        "PartSplitter",
        "PrintablePartGenerator",
        "ThreeDPrintExporter",
        "ThreeDPrintValidator",
        "generate_3d_print_manufacturing_pipeline",
        "generate_complete_manufacturing_pipeline",
        "PrototypeReadinessStatus",
        "ValidationSeverity",
        "ManufacturingBOMItem",
        "ManufacturingBOM",
        "VirtualManufacturingAssembly",
        "ManufacturingValidationResult",
        "ManufacturingValidationEngine",
        "ManufacturingClassifier",
        "ManufacturingClassificationValidator",
        "generate_manufacturing_part_id",
        "validate_laser_cut_profile",
        "validate_three_d_print_profile",
        "validate_manufacturing_profile",
        "create_manufacturing_part_from_structural_component",
        "get_prototype_laser_balsa_profile",
        "get_prototype_3d_print_profile",
        "create_prototype_manufacturing_profile",
        "build_manufacturing_manifest",
    }:
        import cadpy.manufacturing as mfg
        return getattr(mfg, name)
    if name in {
        "ChangeType", "ChangeSeverity", "ImpactCategory", "ArtifactRevisionStatus",
        "RequirementChange", "ImpactResult", "RevisionManifest",
        "RequirementDiffEngine", "DependencyGraph", "ImpactAnalysisEngine"
    }:
        import cadpy.revision as rev
        return getattr(rev, name)
    if name in {
        "ReviewStatus", "PrototypeReadiness", "CoverageStage", "ComplianceItem",
        "RequirementCoverageItem", "EngineeringReview", "EngineeringReviewEngine"
    }:
        import cadpy.review as revw
        return getattr(revw, name)
    if name in {
        "BuildReadiness", "BuildPart", "MaterialScheduleItem", "JointMappingItem",
        "AssemblyStep", "BuildValidationResult", "PrototypeBuildPackage", "BuildPackageEngine"
    }:
        import cadpy.build_package as bpkg
        return getattr(bpkg, name)
    if name in {
        "BuildProgressStatus", "ViewMode", "HighlightMode", "ViewerTraceability",
        "ViewerComponent", "ViewerAssemblyTreeNode", "ViewerJoint", "ViewerAssemblyStep",
        "ViewerLaserSheet", "ViewerPrintablePart", "BuildVisualizationPackage", "BuildVisualizationEngine"
    }:
        import cadpy.build_visualization as bvis
        return getattr(bvis, name)
    if name in {
        "ReleaseStatus", "ReleaseGateCheckCategory", "ReleaseGateCheckItem",
        "PrototypeReleaseManifest", "ReleaseGateResult", "ReleaseGateEngine"
    }:
        import cadpy.release_gate as rgate
        return getattr(rgate, name)
    if name in {"Requirement", "AircraftSpecification", "parse_aircraft_specification", "validate_aircraft_specification"}:
        from cadpy.requirements import Requirement, AircraftSpecification, parse_aircraft_specification, validate_aircraft_specification
        return {
            "Requirement": Requirement,
            "AircraftSpecification": AircraftSpecification,
            "parse_aircraft_specification": parse_aircraft_specification,
            "validate_aircraft_specification": validate_aircraft_specification,
        }[name]
    if name in {"generate_aircraft", "generate_aircraft_from_spec", "CADGenerationResult", "StructuralProfile"}:
        from cadpy.aircraft import generate_aircraft, generate_aircraft_from_spec, CADGenerationResult
        from cadpy.structure import StructuralProfile
        return {
            "generate_aircraft": generate_aircraft,
            "generate_aircraft_from_spec": generate_aircraft_from_spec,
            "CADGenerationResult": CADGenerationResult,
            "StructuralProfile": StructuralProfile,
        }[name]
    if name in {"ensure_step_glb_artifact", "validate_step_glb_artifact"}:
        from cadpy.api import ensure_step_glb_artifact, validate_step_glb_artifact

        return {
            "ensure_step_glb_artifact": ensure_step_glb_artifact,
            "validate_step_glb_artifact": validate_step_glb_artifact,
        }[name]
    if name in {"AssemblyHelper", "MateRelation", "MateTarget", "label_shape", "label_text", "target"}:
        from cadpy.assembly import AssemblyHelper, MateRelation, MateTarget, label_shape, label_text, target

        return {
            "AssemblyHelper": AssemblyHelper,
            "MateRelation": MateRelation,
            "MateTarget": MateTarget,
            "label_text": label_text,
            "label_shape": label_shape,
            "target": target,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

