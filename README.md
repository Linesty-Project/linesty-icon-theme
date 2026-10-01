# Linesty Icon Theme

<div style="display:flex;">
<img style="width:25em;" src="https://github.com/Linesty-Project/linesty-icon-theme/blob/main/preview-1.png"/>
<img style="width:25em;" src="https://github.com/Linesty-Project/linesty-icon-theme/blob/main/preview-2.png"/>
</div>
<p></p>

Linesty is an icon theme created specifically for the [COSMIC](https://system76.com/cosmic/) desktop environment.

It combines application icons from the [Papirus Icon Theme](https://github.com/PapirusDevelopmentTeam/papirus-icon-theme) with system icons from Papirus and the COSMIC Icon Theme. The theme also includes numerous modified and customized icons created to provide a more consistent visual experience within COSMIC.

> [!IMPORTANT]
> Linesty is designed primarily for COSMIC. Other desktop environments are not officially supported.

**The project is actively evolving, and the icon theme is still under development.**

## Installation

### Linesty installer

The Linesty installer downloads the latest version directly from this repository's `main` branch and works independently of your Linux distribution.

> [!NOTE]
> Use the exact same command to update the icon theme.

#### Recommended: System-wide installation

This installs Linesty for all users on the system and requires administrator privileges:

```bash
wget -qO- https://raw.githubusercontent.com/Linesty-Project/linesty-icon-theme/main/install.sh | sh
```

#### User installation

This installs Linesty for the current user only:

```bash
wget -qO- https://raw.githubusercontent.com/Linesty-Project/linesty-icon-theme/main/install.sh | env DESTDIR="$HOME/.local/share/icons" sh
```

> [!IMPORTANT]
> After installation or updating, log out and back in for COSMIC to fully apply the icon theme.

#### Uninstallation

Use the following command to uninstall Linesty:

```bash
wget -qO- https://raw.githubusercontent.com/Linesty-Project/linesty-icon-theme/main/uninstall.sh | sh
```

The uninstall script checks both the user and system-wide icon directories and asks for confirmation before removing Linesty.

### Alternative: Manual installation from ZIP

If you prefer to install Linesty manually:

1. Select **Code → Download ZIP**.
2. Extract the downloaded `linesty-icon-theme-main.zip` archive.
3. Locate the `linesty-icon-theme-main` folder containing the icon theme files.
   * Depending on the archive tool you use, this folder may be directly inside the extracted archive location or inside an additional `linesty-icon-theme-main` folder.
4. Rename the folder containing the icon theme files to **`Linesty`**.
5. Copy the renamed `Linesty` folder to:

```text
~/.local/share/icons/
```
> [!NOTE]
> This method installs Linesty for the current user only.
