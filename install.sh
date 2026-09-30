#!/bin/sh

set -e

gh_repo="linesty-icon-theme"
gh_desc="Linesty icon theme"

cat <<- EOF

  $gh_desc
  https://github.com/Linesty-Project/$gh_repo


EOF

: "${DESTDIR:=/usr/share/icons}"
: "${TAG:=main}"
: "${uninstall:=false}"

_msg() {
    echo "=>" "$@"
}

_rm() {
    _sudo rm -rf "$1"
}

_sudo() {
    if [ -w "$DESTDIR" ] || [ -w "$(dirname "$DESTDIR")" ]; then
        "$@"
    else
        sudo "$@"
    fi
}

_download() {
    _msg "Getting the latest version from GitHub ..."
    wget -O "$temp_file" \
        "https://github.com/Linesty-Project/$gh_repo/archive/$TAG.tar.gz"
    _msg "Unpacking archive ..."
    tar -xzf "$temp_file" -C "$temp_dir"
}

_uninstall() {
    test -d "$DESTDIR/Linesty" || return 0
    _msg "Deleting Linesty icon theme ..."
    _rm "$DESTDIR/Linesty"
}

_install() {
    _sudo mkdir -p "$DESTDIR/Linesty"
    _msg "Installing Linesty icon theme ..."
    _sudo cp -R "$temp_dir/$gh_repo-$TAG/"* "$DESTDIR/Linesty"
    _sudo gtk-update-icon-cache -q "$DESTDIR/Linesty" || true
}

_cleanup() {
    _msg "Clearing cache ..."
    rm -rf "$temp_file" "$temp_dir"
    rm -f "$HOME/.cache/icon-cache.kcache"
    _msg "Done!"
}

trap _cleanup EXIT HUP INT TERM

temp_file="$(mktemp -u)"
temp_dir="$(mktemp -d)"

if [ "$uninstall" = "false" ]; then
    _download
    _uninstall
    _install
else
    _uninstall
fi
