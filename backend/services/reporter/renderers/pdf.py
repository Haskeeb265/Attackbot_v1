from __future__ import annotations

import os
import tempfile
from html import escape
from typing import TYPE_CHECKING

from PIL import Image as PillowImage
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image as ReportLabImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from backend.services.reporter.renderers.sections import build_render_plan
from backend.services.reporter.renderers.theme import severity_colour_hex

if TYPE_CHECKING:
    from backend.services.reporter.config import ReporterConfig
    from backend.services.reporter.models import ParsedScan, ReproductionPackDraft


class PdfRenderer:
    def __init__(self, settings: ReporterConfig) -> None:
        self._settings = settings

    def generate(
        self,
        report_id: str,
        parsed_scan: ParsedScan,
        packs: list[ReproductionPackDraft],
    ) -> tuple[str, list[str]]:
        fd, output_path = tempfile.mkstemp(
            prefix=f"report-{report_id}-",
            suffix=".pdf",
            dir=self._settings.temp_output_dir,
        )
        os.close(fd)

        plan = build_render_plan(
            parsed_scan=parsed_scan,
            packs=packs,
            include_raw_http_appendix=self._settings.include_raw_http_appendix,
        )

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        story: list = []
        partial_reasons: list[str] = []
        styles = getSampleStyleSheet()

        for line in plan.lines:
            story.append(
                Paragraph(self._line_to_markup(line), _style_for_line(line, styles))
            )
            story.append(Spacer(1, 6))

        if parsed_scan.include_evidence_screenshots:
            for entry in plan.evidence_images:
                story.append(
                    Paragraph(escape(f"Evidence image: {entry.finding_title}"), styles["Code"])
                )
                story.append(Spacer(1, 2))
                try:
                    # Validate image readability before embedding.
                    with PillowImage.open(entry.local_tmp_path) as image:
                        image.verify()
                    img = ReportLabImage(entry.local_tmp_path, width=5.5 * inch, height=3.0 * inch)
                    story.append(img)
                    story.append(Spacer(1, 8))
                except Exception:
                    story.append(
                        Paragraph(
                            escape(
                                f"[Evidence screenshot unavailable - {entry.artifact_type}]"
                            ),
                            styles["Italic"],
                        )
                    )
                    story.append(Spacer(1, 8))
                    partial_reasons.append("evidence_image_load_failed")

        doc.build(story)
        return output_path, _dedupe(partial_reasons)

    @staticmethod
    def _line_to_markup(line: str) -> str:
        if line.startswith("### "):
            return f"<b>{escape(line[4:])}</b>"
        if line.startswith("## "):
            return f"<b>{escape(line[3:])}</b>"
        if line.startswith("# "):
            return f"<b>{escape(line[2:])}</b>"

        if line.startswith(("critical |", "high |", "medium |", "low |", "info |")):
            severity = line.split("|", 1)[0].strip().lower()
            color = severity_colour_hex(severity)
            return f"<font color='{color}'>{escape(line)}</font>"

        return escape(line)


def _style_for_line(line: str, styles) -> object:
    if line.startswith("# "):
        return styles["Heading1"]
    if line.startswith("## "):
        return styles["Heading2"]
    if line.startswith("### "):
        return styles["Heading3"]
    return styles["BodyText"]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
