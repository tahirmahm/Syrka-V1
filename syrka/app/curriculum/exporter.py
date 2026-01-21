"""Export curricula in various formats."""

import json
from app.curriculum.structure import FullCurriculum


class CurriculumExporter:
    """Export curricula to different formats."""

    def to_json(self, curriculum: FullCurriculum) -> str:
        """Export as JSON."""
        return curriculum.model_dump_json(indent=2)

    def to_scorm_manifest(self, curriculum: FullCurriculum) -> str:
        """Generate SCORM manifest."""
        manifest = f"""<?xml version="1.0"?>
<manifest identifier="syrka_{curriculum.title.replace(' ', '_')}" version="1.0">
    <metadata>
        <schema>ADL SCORM</schema>
        <schemaversion>1.2</schemaversion>
    </metadata>
    <organizations default="ORG-1">
        <organization identifier="ORG-1">
            <title>{curriculum.title}</title>
        </organization>
    </organizations>
    <resources>
    </resources>
</manifest>"""
        return manifest

    def to_lms_package(self, curriculum: FullCurriculum, output_path: str) -> str:
        """Create LMS-importable package."""
        # Simplified - production would create ZIP with SCORM files
        return output_path

    def to_markdown(self, curriculum: FullCurriculum) -> str:
        """Export as markdown."""
        md = f"# {curriculum.title}\n\n"
        md += f"**Sector:** {curriculum.target_sector}\n\n"
        md += f"**Skills:** {', '.join(curriculum.target_skills)}\n\n"

        for module in curriculum.modules:
            md += f"## {module.title}\n\n{module.description}\n\n"
            for unit in module.units:
                md += f"### {unit.title}\n\n"

        return md
