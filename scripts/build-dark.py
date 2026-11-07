#!/usr/bin/env python3
"""Build Linesty-Dark from reviewed, per-application SVG palette recipes."""

import argparse
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
PAINTS = {"fill", "stroke", "stop-color"}
SURFACE_TOP = "#474b53"
SURFACE_BOTTOM = "#30343c"
INDEX = """[Icon Theme]
Name=Linesty Dark
Comment=Soft charcoal application icons with vivid brand colors and gentle depth
Example=com.system76.CosmicSettings
Inherits=Linesty,Pop,hicolor
Directories=scalable/apps

[scalable/apps]
Context=Applications
Size=64
MinSize=16
MaxSize=512
Type=Scalable
"""


def color(value):
    value = value.strip().lower()
    if value == "white":
        return "#ffffff"
    if value == "black":
        return "#000000"
    if re.fullmatch(r"#[0-9a-f]{3}", value):
        return "#" + "".join(c * 2 for c in value[1:])
    return value


def recolor(source, recipe):
    root = ET.fromstring(source)
    palette = {color(k): v for k, v in recipe.get("colors", {}).items()}
    surfaces = {color(value) for value in recipe.get("surfaces", [])}
    used_surface = False

    def paint(name, value):
        nonlocal used_surface
        if name == "fill" and color(value) in surfaces:
            used_surface = True
            return "url(#linestyAppSurface)"
        return palette.get(color(value), value)

    for parent in root.iter():
        # Editor metadata is not artwork and need not be shipped in the variant.
        for child in list(parent):
            if not child.tag.startswith("{" + SVG + "}"):
                parent.remove(child)
        for name in list(parent.attrib):
            if name.startswith("{") and not name.startswith("{http://www.w3.org/1999/xlink}"):
                del parent.attrib[name]
        for name in PAINTS:
            if name in parent.attrib:
                parent.set(name, paint(name, parent.attrib[name]))
        if "style" in parent.attrib:
            declarations = []
            for item in parent.attrib["style"].split(";"):
                if ":" not in item:
                    continue
                key, value = item.split(":", 1)
                if key.strip() in PAINTS:
                    value = paint(key.strip(), value)
                declarations.append(key.strip() + ":" + value.strip())
            parent.set("style", ";".join(declarations))
    for override in recipe.get("overrides", []):
        elements = root.findall(override["selector"], {"svg": SVG})
        if not elements:
            raise ValueError("SVG override no longer matches: " + override["selector"])
        for element in elements:
            element.attrib.update(override["attributes"])
    if used_surface:
        defs = ET.SubElement(root, "{" + SVG + "}defs")
        surface_gradient(defs, "linestyAppSurface")
    ET.indent(root, space=" ")
    return ET.tostring(root, encoding="unicode") + "\n"


def surface_gradient(defs, identifier):
    gradient = ET.SubElement(defs, "{" + SVG + "}linearGradient", id=identifier,
                             x1="0", y1="0", x2="0", y2="1")
    ET.SubElement(gradient, "{" + SVG + "}stop", offset="0", attrib={"stop-color": SURFACE_TOP})
    ET.SubElement(gradient, "{" + SVG + "}stop", offset="1", attrib={"stop-color": SURFACE_BOTTOM})


def build(root=ROOT, output=None):
    root = Path(root)
    output = Path(output) if output else root / "Linesty-Dark"
    recipes = json.loads((root / "dark-palettes.json").read_text())
    source = root / "scalable/apps"
    if source.resolve().is_relative_to(output.resolve()):
        raise ValueError("Output must not contain the original application artwork")
    directory = output / "scalable/apps"
    if directory.exists() and any(directory.iterdir()):
        index = output / "index.theme"
        if not index.is_file() or "Name=Linesty Dark\n" not in index.read_text():
            raise ValueError("Output contains an unrecognized icon theme")
    generated = {}
    targets = {}
    for name, recipe in sorted(recipes.items()):
        path = source / (name + ".svg")
        resolved = path.resolve(strict=True)
        if resolved.parent != source.resolve() or "symbolic" in name:
            raise ValueError("Recipe must refer to a full-color application icon: " + name)
        if resolved.name in generated:
            raise ValueError("Duplicate recipe for " + resolved.name)
        generated[resolved.name] = recolor(resolved.read_text(), recipe)
        targets[resolved] = resolved.name
    aliases = {}
    for path in sorted(source.glob("*.svg")):
        if path.is_symlink() and "symbolic" not in path.name:
            destination = targets.get(path.resolve())
            if destination:
                aliases[path.name] = destination
    # Finish validation before writing; discard names removed from the recipes.
    directory.mkdir(parents=True, exist_ok=True)
    expected = set(generated) | set(aliases)
    for path in directory.iterdir():
        if path.name not in expected:
            path.unlink()
    for name, data in generated.items():
        path = directory / name
        if path.is_symlink():
            path.unlink()
        path.write_text(data)
    for name, destination in aliases.items():
        path = directory / name
        if path.exists() or path.is_symlink():
            path.unlink()
        path.symlink_to(destination)
    (output / "index.theme").write_text(INDEX)
    (output / "LICENSE").write_bytes((root / "LICENSE").read_bytes())
    print(f"Built Linesty-Dark: {len(generated)} designs, {len(aliases)} aliases ({len(expected)} icon names).")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Output theme directory (default: ./Linesty-Dark)")
    args = parser.parse_args()
    build(output=args.output)


if __name__ == "__main__":
    main()
