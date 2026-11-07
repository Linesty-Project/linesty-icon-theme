import configparser
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


builder = module("dark_builder", "build-dark.py")
installer = module("dark_installer", "install-dark.py")


class DarkThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.theme = builder.build(output=Path(cls.temp.name) / "Linesty-Dark")
        cls.icons = cls.theme / "scalable/apps"

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_published_artwork_matches_recipes_and_keeps_all_aliases(self):
        published = ROOT / "Linesty-Dark/scalable/apps"
        self.assertEqual({p.name for p in published.iterdir()}, {p.name for p in self.icons.iterdir()})
        for p in self.icons.iterdir():
            self.assertEqual(p.is_symlink(), (published / p.name).is_symlink(), p.name)
            if p.is_symlink():
                self.assertEqual(os.readlink(p), os.readlink(published / p.name), p.name)
                self.assertEqual(p.resolve().parent, self.icons.resolve(), p.name)
            else:
                self.assertEqual(p.read_bytes(), (published / p.name).read_bytes(), p.name)
            self.assertTrue(p.exists(), p.name)
        self.assertTrue((self.icons / "org.telegram.desktop.svg").is_symlink())
        self.assertEqual((self.icons / "org.telegram.desktop.svg").resolve().name, "telegram.svg")
        self.assertFalse(any("symbolic" in p.name for p in self.icons.iterdir()))

    def test_metadata_declares_real_directories_and_inherits_linesty(self):
        config = configparser.ConfigParser()
        config.read(self.theme / "index.theme")
        self.assertEqual(config["Icon Theme"]["Inherits"].split(",")[0], "Linesty")
        for directory in config["Icon Theme"]["Directories"].split(","):
            self.assertTrue((self.theme / directory).is_dir())
            self.assertEqual(config[directory]["Context"], "Applications")
            self.assertEqual(config[directory]["Type"], "Scalable")

    @unittest.skipUnless(shutil.which("rsvg-convert"), "librsvg is optional")
    def test_every_design_renders_at_panel_and_launcher_sizes(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow is required for render validation")
        from io import BytesIO
        for path in sorted(self.icons.glob("*.svg")):
            if path.is_symlink():
                continue
            for size in (16, 64):
                with self.subTest(icon=path.name, size=size):
                    result = subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size), str(path)],
                                            capture_output=True, check=True)
                    image = Image.open(BytesIO(result.stdout)).convert("RGBA")
                    self.assertEqual(image.size, (size, size))
                    self.assertIsNotNone(image.getchannel("A").getbbox())
                    self.assertLess(image.getpixel((0, 0))[3], 10, "Transparent canvas was lost")

    def test_svg_resources_are_internal_and_ids_are_unique(self):
        import re
        for path in self.icons.glob("*.svg"):
            if path.is_symlink():
                continue
            root = ET.parse(path).getroot()
            ids = [e.attrib["id"] for e in root.iter() if "id" in e.attrib]
            self.assertEqual(len(ids), len(set(ids)), path.name)
            references = re.findall(r"url\(#([^)]*)\)", path.read_text())
            self.assertTrue(set(references).issubset(ids), path.name)
            for e in root.iter():
                for key in ("href", "{http://www.w3.org/1999/xlink}href"):
                    if key in e.attrib:
                        self.assertTrue(e.attrib[key].startswith("#"), path.name)

    def test_original_geometry_is_preserved_without_extra_frames(self):
        shape_tags = {"path", "rect", "circle", "ellipse", "line", "polyline", "polygon", "text", "image", "use"}
        geometry = {"d", "x", "y", "x1", "x2", "y1", "y2", "cx", "cy", "r", "rx", "ry", "width", "height", "points", "transform"}

        def shapes(root):
            return [(e.tag, {k: v for k, v in e.attrib.items() if k in geometry})
                    for e in root.iter() if e.tag.split("}")[-1] in shape_tags]

        for path in self.icons.glob("*.svg"):
            if path.is_symlink():
                continue
            original = ET.parse(ROOT / "scalable/apps" / path.name).getroot()
            refined = ET.parse(path).getroot()
            self.assertEqual(shapes(original), shapes(refined), path.name)
            for key in ("width", "height", "viewBox"):
                self.assertEqual(original.get(key), refined.get(key), (path.name, key))

    def test_install_update_and_uninstall_preserve_parent_and_keep_backup(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "icons"
            base = destination / "Linesty"
            base.mkdir(parents=True)
            (base / "index.theme").write_text("[Icon Theme]\nName=Custom Linesty\n")
            marker = base / "custom.svg"
            marker.write_text("Keep my installed parent exactly as it is")
            before = {p.name: p.read_bytes() for p in base.iterdir()}
            installer.install(destination)
            icon = destination / "Linesty-Dark/scalable/apps/org.telegram.desktop.svg"
            self.assertTrue(icon.is_symlink())
            self.assertTrue(icon.exists())
            (destination / "Linesty-Dark/local-note").write_text("previous version")
            installer.install(destination)
            backups = list(destination.glob(".Linesty-Dark.backup-*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual((backups[0] / "local-note").read_text(), "previous version")
            installer.uninstall(destination)
            self.assertFalse((destination / "Linesty-Dark").exists())
            self.assertEqual(before, {p.name: p.read_bytes() for p in base.iterdir()})

    def test_fresh_install_includes_parent_and_symbolic_icons(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "icons"
            installer.install(destination)
            self.assertTrue((destination / "Linesty/scalable/places/folder.svg").exists())
            self.assertTrue((destination / "Linesty/scalable/actions/edit-copy-symbolic.svg").exists())
            self.assertTrue((destination / "Linesty-Dark/LICENSE").is_file())
            try:
                import gi
                gi.require_version("Gtk", "3.0")
                from gi.repository import Gtk
            except (ImportError, ValueError):
                return
            theme = Gtk.IconTheme.new()
            theme.set_search_path([str(destination), "/usr/share/icons"])
            theme.set_custom_theme("Linesty-Dark")
            for name, parent in [("org.telegram.desktop", "Linesty-Dark"),
                                 ("com.system76.CosmicFiles", "Linesty-Dark"),
                                 ("folder", "Linesty"), ("edit-copy-symbolic", "Linesty")]:
                info = theme.lookup_icon(name, 64, 0)
                self.assertIsNotNone(info, name)
                self.assertTrue(Path(info.get_filename()).is_relative_to(destination / parent), name)

    def test_install_refuses_a_symlink_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary)
            (destination / "Linesty-Dark").symlink_to(self.theme, target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError, "symbolic link"):
                installer.install(destination)

    def test_build_cannot_overwrite_original_artwork(self):
        source = ROOT / "scalable/apps/firefox.svg"
        before = source.read_bytes()
        with self.assertRaisesRegex(ValueError, "original application artwork"):
            builder.build(output=ROOT)
        self.assertEqual(source.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
