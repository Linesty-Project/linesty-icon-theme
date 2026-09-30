#!/bin/sh

set -e

gh_repo="linesty-icon-theme"
gh_desc="Linesty icon theme"

cat <<- EOF

  $gh_desc
  https://github.com/Linesty-Project/$gh_repo


EOF

_rm_icon_theme() {
  test -d "$1" || return 0

  echo "Removing '$1'..." >&2

  if [ -w "$1" ]; then
     rm -rf "$1"
  else
    if command -v sudo >/dev/null; then
      sudo rm -rf "$1"
    elif command -v doas >/dev/null; then
      doas rm -rf "$1"
    else
      echo "Failed to remove '$1'. Please run the script with root permission." >&2
    fi
  fi
}

_yes_no() {
  printf '%s [Y/n]: ' "$*"
  read -r yes_no </dev/tty  # don't read from stdin

  case "$yes_no" in
    [Yy]|'') return 0 ;;
    [Nn]|*)  return 1 ;;
  esac
}

echo "=> Removing $gh_desc ..."
for d in "$HOME/.local/share/icons" "/usr/share/icons"; do
    [ -d "$d/Linesty" ] || continue
    if _yes_no "Do you want to remove Linesty icon theme from '$d'"; then
        _rm_icon_theme "$d/Linesty"
    fi
done

echo "=> Done!"