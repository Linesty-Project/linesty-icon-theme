#!/usr/bin/env python3
"""Install or remove the separate Linesty-Dark theme for the current user."""

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def default_destination():
    data = os.environ.get("XDG_DATA_HOME", "")
    return (Path(data) if Path(data).is_absolute() else Path.home() / ".local/share") / "icons"


def install(destination):
    destination = Path(destination).expanduser().resolve()
    source = ROOT / "Linesty-Dark"
    if not (source / "index.theme").is_file():
        raise RuntimeError("Build the dark variant first: python3 scripts/build-dark.py")
    if destination == ROOT or ROOT.is_relative_to(destination / "Linesty-Dark") or destination.is_relative_to(source):
        raise RuntimeError("The installation destination must be outside the source theme")
    destination.mkdir(parents=True, exist_ok=True)
    dark = destination / "Linesty-Dark"
    base = destination / "Linesty"
    if dark.is_symlink() or base.is_symlink():
        raise RuntimeError("Refusing to replace a theme directory that is a symbolic link")
    with tempfile.TemporaryDirectory(prefix=".linesty-install-", dir=destination) as temporary:
        stage = Path(temporary)
        shutil.copytree(source, stage / "Linesty-Dark", symlinks=True)
        shutil.copy2(ROOT / "LICENSE", stage / "Linesty-Dark/LICENSE")
        # The child theme needs Linesty for all unmodified icon names/contexts.
        # Preserve any already-installed parent, including user customizations.
        need_base = not (base / "index.theme").exists()
        if need_base:
            if base.exists():
                raise RuntimeError("Linesty exists without index.theme; review it before installing")
            parent = stage / "Linesty"
            parent.mkdir()
            shutil.copy2(ROOT / "index.theme", parent / "index.theme")
            shutil.copy2(ROOT / "LICENSE", parent / "LICENSE")
            shutil.copytree(ROOT / "scalable", parent / "scalable", symlinks=True)
        backup = None
        if dark.exists():
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
            backup = destination / (".Linesty-Dark.backup-" + stamp)
            dark.rename(backup)
        installed_base = False
        try:
            if need_base:
                (stage / "Linesty").rename(base)
                installed_base = True
            (stage / "Linesty-Dark").rename(dark)
        except BaseException:
            if installed_base:
                shutil.rmtree(base)
            if backup:
                backup.rename(dark)
            raise
    for theme in ([base] if need_base else []) + [dark]:
        cache = shutil.which("gtk-update-icon-cache")
        if cache:
            subprocess.run([cache, "-f", "-t", str(theme)], check=False, capture_output=True)
    print("Installed:", dark)
    if backup:
        print("Previous dark theme saved:", backup)
    else:
        print("First installation: log out and back in so running COSMIC components can discover the new theme.")
    print("Select 'Linesty Dark' in COSMIC Settings → Desktop → Appearance → Icons.")
    print("Your currently selected icon theme has not been changed.")


def uninstall(destination):
    theme = Path(destination).expanduser().resolve() / "Linesty-Dark"
    if theme.is_symlink():
        raise RuntimeError("Refusing to remove a theme directory that is a symbolic link")
    if theme.exists():
        index = theme / "index.theme"
        if not index.is_file() or "Name=Linesty Dark\n" not in index.read_text():
            raise RuntimeError("The directory does not contain the Linesty Dark theme")
        shutil.rmtree(theme)
        print("Removed:", theme)
    else:
        print("Linesty-Dark is not installed in", theme.parent)
    print("The parent Linesty theme is retained.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destdir", type=Path, default=os.environ.get("DESTDIR") or default_destination())
    parser.add_argument("--uninstall", action="store_true", help="Remove only Linesty-Dark")
    args = parser.parse_args()
    try:
        (uninstall if args.uninstall else install)(args.destdir)
    except (OSError, RuntimeError) as error:
        parser.exit(1, str(error) + "\n")


if __name__ == "__main__":
    main()
