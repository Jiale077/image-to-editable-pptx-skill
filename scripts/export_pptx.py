#!/usr/bin/env python3
"""Export structured SVGs as slides with native PowerPoint objects."""
import argparse
import math
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import unquote, urlsplit

from lxml import etree
from pptx import Presentation
from pptx.util import Pt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor/figgenie/scripts"))
from svg2pptx import Converter, SVG, WARN

XLINK = "{http://www.w3.org/1999/xlink}href"
SUPPORTED = {"svg", "g", "rect", "circle", "ellipse", "line", "polyline", "polygon",
             "path", "text", "image", "defs", "title", "desc", "metadata", "style"}


def parse_size(value):
    try:
        width, height = (float(part) for part in value.lower().split("x"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("use WIDTHxHEIGHT in points, e.g. 960x540") from exc
    if not all(math.isfinite(n) and 72 <= n <= 4032 for n in (width, height)):
        raise argparse.ArgumentTypeError("each slide dimension must be 72–4032 points")
    return width, height


def svg_geometry(root):
    viewbox = root.get("viewBox")
    if viewbox:
        x, y, width, height = map(float, re.split(r"[\s,]+", viewbox.strip()))
    else:
        x, y = 0, 0
        width, height = (float(re.sub(r"(px|pt)$", "", root.get(key, "")))
                         for key in ("width", "height"))
    if not all(map(math.isfinite, (x, y, width, height))) or min(width, height) <= 0:
        raise ValueError("SVG needs finite coordinates and a positive viewBox or width/height")
    return x, y, width, height


def check_image(href, source):
    if re.match(r"^data:image/(?:png|jpe?g);base64,", href, re.I):
        return
    parts = urlsplit(href)
    if not href or parts.scheme or parts.netloc:
        raise ValueError("image href must be a PNG/JPEG data URI or a relative local file")
    # The backend tries the literal filename first, then URL-decoded spelling.
    for spelling in (href, unquote(href)):
        image = Path(spelling)
        if image.is_absolute() or not (source.parent / image).resolve().is_relative_to(source.parent):
            raise ValueError("image reference points outside the SVG folder")


def inspect_svg(root, source):
    issues = []
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        name = etree.QName(el).localname
        if name == "image":
            check_image(el.get("href") or el.get(XLINK) or "", source)
        if name == "style":
            # FigGenie exports may include font-face definitions for SVG viewing.
            css = re.sub(r"@font-face\s*\{[^}]*\}|/\*.*?\*/", "", el.text or "", flags=re.S)
            if css.strip():
                issues.append("CSS stylesheet rules: put appearance on individual SVG elements")
        if any(ancestor.tag == SVG + "defs" for ancestor in el.iterancestors()):
            continue
        if el is not root and (name not in SUPPORTED or name == "svg"):
            issues.append(f"<{name}> has no editable mapping")
        if el.get("data-symbol") == "tex" and not all(
            el.get(key) is not None for key in ("data-w", "data-asc", "data-desc", "data-baseline")
        ):
            raise ValueError("formula needs FigGenie's rendered metrics before export")
        if any(el.get(key) for key in ("clip-path", "mask", "filter", "display", "visibility")):
            issues.append(f"<{name}> has clipping, effects, or visibility attributes")
        styles = el.get("style", "")
        if (any("url(" in el.get(key, "") for key in ("fill", "stroke"))
                or re.search(r"(?:^|;)\s*(?:clip-path|mask|filter|display|visibility)\s*:", styles)
                or re.search(r"(?:^|;)\s*(?:fill|stroke)\s*:\s*url\(", styles)):
            issues.append(f"<{name}> has effects or paints that require a bitmap")
    return list(dict.fromkeys(issues))


def load_svg(source):
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True)
    tree = etree.parse(str(source), parser)
    if tree.docinfo.doctype:
        raise ValueError("SVG must not contain a DOCTYPE")
    root = tree.getroot()
    if root.tag != SVG + "svg":
        raise ValueError("expected an SVG document with the SVG namespace")
    return root


def export(inputs, output, slide_size, latin, cjk, allow_partial, force):
    if output.exists() and not force:
        raise FileExistsError(f"{output} exists; choose another path or pass --force")
    if output.suffix.lower() != ".pptx":
        raise ValueError("output filename must end in .pptx")
    deck = Presentation()
    width, height = slide_size
    deck.slide_width, deck.slide_height = Pt(width), Pt(height)
    summaries = []

    for source in inputs:
        source = source.resolve()
        try:
            root = load_svg(source)
            x, y, w, h = svg_geometry(root)
            issues = inspect_svg(root, source)
            if issues and not allow_partial:
                raise ValueError("; ".join(issues))
            scale = min(width / w, height / h)
            offset = ((width / scale - w) / 2 - x, (height / scale - h) / 2 - y)
            root.set("viewBox", f"0 0 {w} {h}")
            WARN.clear()
            converter = Converter(root, None, scale, latin, cjk, "text", None,
                                  base_dir=source.parent, presentation=deck, offset=offset)
            converter.run(group=True)
            issues.extend(WARN)
            if WARN and not allow_partial:
                raise ValueError("; ".join(WARN))
            if not len(converter.slide.shapes):
                raise ValueError("no slide objects were exported")
        except (OSError, ValueError, etree.XMLSyntaxError) as exc:
            raise ValueError(f"{source.name}: {exc}") from exc
        summaries.append((source.name, converter.counts, list(dict.fromkeys(issues))))

    # Write beside the destination so replace is atomic and a failed slide leaves
    # an existing deck intact. Hard link publishes a new file without overwriting.
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent, prefix=".pptx-export-") as tmp:
        staged = Path(tmp) / "slides.pptx"
        deck.save(staged)
        if force:
            os.replace(staged, output)
        else:
            os.link(staged, output)
    return summaries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("svg", nargs="+", type=Path, help="one SVG per slide, in order")
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--size", type=parse_size, default=(960, 540), metavar="WIDTHxHEIGHT")
    parser.add_argument("--latin", help="override the Latin PowerPoint font")
    parser.add_argument("--cjk", help="override the CJK PowerPoint font")
    parser.add_argument("--allow-partial", action="store_true", help="export with unsupported-content warnings")
    parser.add_argument("--force", action="store_true", help="replace an existing PPTX")
    args = parser.parse_args()
    try:
        summaries = export(args.svg, args.output, args.size, args.latin, args.cjk,
                           args.allow_partial, args.force)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Export failed: {exc}\n")
    print(f"Saved {len(summaries)} slide(s) to {args.output}")
    for index, (name, counts, issues) in enumerate(summaries, 1):
        print(f"  {index}. {name} | " + ", ".join(f"{k}: {v}" for k, v in counts.items() if v))
        for issue in issues:
            print(f"     warning: {issue}")


if __name__ == "__main__":
    main()
