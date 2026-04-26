"""report_builder.py — HTML/PDF report builder for formal documentation.

Provides ReportBuilder: build the HTML body with add(), then call render_pdf()
to produce a formatted PDF with title page, TOC, and page headers/footers.

Configuration is loaded from the 'report' key in script_config (passed via
generate_artifacts.py --config-json), or from artifacts.yaml 'report:' section.
"""

import base64
import html as _html
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    _WEASYPRINT = True
except ImportError:
    _WEASYPRINT = False

ASSETS_DIR = Path(__file__).parent / "assets"


@dataclass
class ReportConfig:
    org_name: str = ""
    org_website: str = ""
    org_email: str = ""
    logo_path: str = ""
    font_family: str = "Georgia, serif"
    distribution_statement: str = ""
    doc_version: str = "1.0"
    author: str = ""
    author_title: str = ""   # job title / role of the author


def load_report_config(script_config: dict) -> ReportConfig:
    """Extract ReportConfig from the merged script_config dict."""
    rc = script_config.get("report", {})
    return ReportConfig(
        org_name               = rc.get("org_name", ""),
        org_website            = rc.get("org_website", ""),
        org_email              = rc.get("org_email", ""),
        logo_path              = rc.get("logo_path", ""),
        font_family            = rc.get("font_family", "Georgia, serif"),
        distribution_statement = rc.get("distribution_statement", ""),
        doc_version            = rc.get("doc_version", "1.0"),
        author                 = rc.get("author", ""),
        author_title           = rc.get("author_title", ""),
    )


# ── CSS helpers ───────────────────────────────────────────────────────────────

def _esc_css(s: str) -> str:
    """Escape a Python string for use as a CSS quoted-string value."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\A ")


def _esc(s: str) -> str:
    return _html.escape(s or "")


def _logo_data_url(logo_path: str) -> str:
    """Resolve logo_path and return a base64 data URL, or empty string."""
    if not logo_path:
        return ""
    path = Path(logo_path)
    if not path.is_absolute():
        for base in (Path.cwd(), ASSETS_DIR.parent.parent):
            candidate = base / path
            if candidate.exists():
                path = candidate
                break
    if not path.exists():
        return ""
    mime = {".png": "image/png", ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg", ".svg": "image/svg+xml"}.get(
        path.suffix.lower(), "image/png")
    encoded = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{encoded}"


def _page_margin_css(config: ReportConfig, doc_number: str, project_title: str) -> str:
    """Return CSS @page margin-box rules for headers/footers."""
    logo_url = _logo_data_url(config.logo_path)
    logo_rule = ""
    if logo_url:
        logo_rule = f"""
    @bottom-right {{
        content: "";
        background-image: url("{logo_url}");
        background-size: contain;
        background-repeat: no-repeat;
        background-position: right center;
    }}"""

    font = config.font_family
    dist = _esc_css(config.distribution_statement)
    num  = _esc_css(doc_number)
    proj = _esc_css(project_title)
    ver  = _esc_css(config.doc_version)

    return f"""
@page {{
    @top-left   {{ font-family: {font}; font-size: 8pt; color: #555;
                   content: "{num}"; vertical-align: bottom; padding-bottom: 3pt; }}
    @top-center {{ font-family: {font}; font-size: 8pt; color: #555;
                   content: "{proj}"; vertical-align: bottom; padding-bottom: 3pt; }}
    @top-right  {{ font-family: {font}; font-size: 8pt; color: #555;
                   content: "Rev {ver}"; vertical-align: bottom; padding-bottom: 3pt; }}
    @bottom-left   {{ font-family: {font}; font-size: 8pt; color: #555;
                      content: "{dist}"; vertical-align: top; padding-top: 3pt; }}
    @bottom-center {{ font-family: {font}; font-size: 8pt; color: #555;
                      content: "Page " counter(page) " of " counter(pages);
                      vertical-align: top; padding-top: 3pt; }}
    {logo_rule}
}}
@page :first {{
    @top-left    {{ content: ""; }}
    @top-center  {{ content: ""; }}
    @top-right   {{ content: ""; }}
    @bottom-left {{ content: ""; }}
    @bottom-center {{ content: ""; }}
    @bottom-right {{ content: ""; background-image: none; }}
}}
"""


# ── TOC generation ────────────────────────────────────────────────────────────

def _generate_toc(html: str) -> tuple[str, str]:
    """Add id= attributes to h2/h3 headings and return (modified_html, toc_html)."""
    seen: dict[str, int] = {}
    modified = html
    items: list[str] = []

    for m in re.finditer(r"<(h[2-4])>(.*?)</\1>", html, re.DOTALL):
        tag  = m.group(1)
        text = m.group(2)
        level = tag[1]
        clean_text = re.sub(r"<[^>]+>", "", text).strip()
        base  = re.sub(r"[^\w\s-]", "", clean_text.lower()).strip()
        base  = re.sub(r"[\s_]+", "-", base)
        base  = re.sub(r"-+", "-", base).strip("-")
        n = seen.get(base, 0)
        seen[base] = n + 1
        anchor = base if n == 0 else f"{base}-{n}"
        old = f"<{tag}>{text}</{tag}>"
        new = f'<{tag} id="{anchor}">{text}</{tag}>'
        modified = modified.replace(old, new, 1)
        items.append(f'<a href="#{anchor}" data-level="{level}">{clean_text}</a>')

    toc_html = (
        '<div class="toc-page"><h2>Table of Contents</h2>'
        '<div class="toc">' + "\n".join(items) + "</div></div>"
    )
    return modified, toc_html


# ── Title page ────────────────────────────────────────────────────────────────

def _meta_row(label: str, value: str) -> str:
    return (f'<tr><td class="meta-label">{_esc(label)}</td>'
            f'<td class="meta-value">{_esc(value)}</td></tr>')


def build_title_page(config: ReportConfig, doc_title: str,
                     doc_number: str, project: str) -> str:
    """Return the HTML <div class="title-page"> block."""

    # Logo
    logo_url = _logo_data_url(config.logo_path)
    logo_block = (
        f'<div class="title-logo-area"><img class="org-logo" src="{logo_url}" alt=""></div>'
        if logo_url else ""
    )

    # Document title + rule + subtitle
    title_block = (
        f'<div class="title-doc-title">{_esc(doc_title)}</div>'
        '<hr class="title-rule">'
        f'<div class="title-doc-subtitle">{_esc(project)}</div>'
    )

    # Metadata table rows
    meta_rows: list[str] = []
    if doc_number:
        meta_rows.append(_meta_row("Document Number", doc_number))
    meta_rows.append(_meta_row("Revision", config.doc_version))
    meta_rows.append(_meta_row("Date", date.today().isoformat()))
    if config.author:
        meta_rows.append(_meta_row("Prepared By", config.author))
    if config.author_title:
        meta_rows.append(_meta_row("Title / Role", config.author_title))
    if config.org_name:
        meta_rows.append(_meta_row("Organization", config.org_name))
    if config.org_email:
        meta_rows.append(_meta_row("Contact", config.org_email))

    meta_block = ""
    if meta_rows:
        meta_block = (
            '<div class="title-meta-area">'
            '<table class="title-meta-table"><tbody>'
            + "".join(meta_rows) +
            "</tbody></table></div>"
        )

    # Distribution statement
    dist_block = ""
    if config.distribution_statement:
        dist_block = (
            '<div class="title-distribution-area">'
            f'<div class="distribution-box">{_esc(config.distribution_statement)}</div>'
            "</div>"
        )

    return (
        '<div class="title-page">'
        f"{logo_block}"
        f"{title_block}"
        f"{meta_block}"
        f"{dist_block}"
        "</div>"
    )


# ── ReportBuilder ─────────────────────────────────────────────────────────────

class ReportBuilder:
    """
    Accumulates HTML content parts and renders a formatted PDF with:
    - Title page (no header/footer)
    - Auto-generated TOC page
    - Content pages with configurable header/footer
    """

    def __init__(self, config: ReportConfig, doc_title: str,
                 doc_number: str = "", project: str = ""):
        self.config     = config
        self.doc_title  = doc_title
        self.doc_number = doc_number
        self.project    = project
        self._parts: list[str] = []

    def add(self, html: str):
        """Append raw HTML to the document body."""
        self._parts.append(html)

    def _build_html_and_css(self) -> tuple[str, str]:
        body = "\n".join(self._parts)
        body_with_ids, toc_html = _generate_toc(body)
        title_html = build_title_page(
            self.config, self.doc_title, self.doc_number, self.project)
        full_body = title_html + "\n" + toc_html + "\n" + body_with_ids

        html = (
            "<!DOCTYPE html><html><head>"
            '<meta charset="utf-8">'
            f"<title>{_esc(self.doc_title)}</title>"
            "</head><body>"
            f"{full_body}"
            "</body></html>"
        )

        base_css = (ASSETS_DIR / "report_styles.css").read_text(encoding="utf-8")
        font_override = f':root {{ --doc-font-family: {self.config.font_family}; }}\n'
        page_css = _page_margin_css(self.config, self.doc_number, self.project)
        css = font_override + base_css + page_css

        return html, css

    def render_pdf(self, output_path: Path) -> bool:
        """Render to PDF via weasyprint. Returns True on success."""
        if not _WEASYPRINT:
            print("  [PDF] ⚠  weasyprint not installed — pip install weasyprint")
            return False
        html, css = self._build_html_and_css()
        try:
            fc = FontConfiguration()
            ss = CSS(string=css, font_config=fc,
                     base_url=str(output_path.parent))
            HTML(string=html,
                 base_url=str(output_path.parent)).write_pdf(
                target=output_path, stylesheets=[ss], font_config=fc)
            print(f"  [PDF] → {output_path}")
            return True
        except Exception as exc:
            print(f"  [PDF] ⚠  {exc}")
            return False

    def render_html_debug(self, output_path: Path):
        """Write a standalone HTML file (CSS inlined) for visual debugging."""
        html, css = self._build_html_and_css()
        debug_html = html.replace("</head>", f"<style>{css}</style></head>")
        output_path.write_text(debug_html, encoding="utf-8")
        print(f"  [HTML] → {output_path}")
