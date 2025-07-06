
import subprocess
import os
import re
import platform
import colorsys
import logging

HOME = os.getenv("HOME", os.getenv("USERPROFILE"))
XDG_CACHE_DIR = os.getenv("XDG_CACHE_HOME", os.path.join(HOME, ".cache"))
XDG_CONF_DIR = os.getenv("XDG_CONFIG_HOME", os.path.join(HOME, ".config"))
CONF_DIR = os.path.join(XDG_CONF_DIR, "wal")
MODULE_DIR = os.path.dirname(__file__)

OS = platform.uname()[0]

def saturate_color(color, amount):
    """Saturate a hex color."""
    r, g, b = hex_to_rgb(color)
    r, g, b = [x / 255.0 for x in (r, g, b)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    s = amount
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    r, g, b = [x * 255.0 for x in (r, g, b)]

    return rgb_to_hex((int(r), int(g), int(b)))

def hex_to_rgb(color):
    """Convert a hex color to rgb."""
    return tuple(bytes.fromhex(color.strip("#")))

def rgb_to_hex(color):
    """Convert an rgb color to hex."""
    return "#%02x%02x%02x" % (*color,)


def get_desktop_env():
    """Identify the current running desktop environment."""
    
    desktop = os.environ.get("XDG_CURRENT_DESKTOP")
    if desktop:
        return desktop

    desktop = os.environ.get("DESKTOP_SESSION")
    if desktop:
        return desktop

    desktop = os.environ.get("GNOME_DESKTOP_SESSION_ID")
    if desktop:
        return "GNOME"

    desktop = os.environ.get("MATE_DESKTOP_SESSION_ID")
    if desktop:
        return "MATE"

    desktop = os.environ.get("SWAYSOCK")
    if desktop:
        return "SWAY"
    
        

    return None

def get_desktop_wallpaper(desktop):
    try:
        desktop = str(desktop).lower()
    except:
        pass

    try:
        if "gnome" in desktop or "unity" in desktop or "cinnamon" in desktop:
            out = subprocess.check_output([
                "gsettings", "get",
                "org.gnome.desktop.background", "picture-uri"
            ], text=True).strip()
            return out.strip("'").removeprefix("file://")

        elif "mate" in desktop:
            out = subprocess.check_output([
                "gsettings", "get", "org.mate.background", "picture-filename"
            ], text=True).strip()
            return out.strip("'")

        elif "xfce" in desktop:
            out = subprocess.check_output([
                "xfconf-query", "-c", "xfce4-desktop",
                "-p", "/backdrop/screen0/monitor0/image-path"
            ], text=True).strip()
            return out

        elif "kde" in desktop:
            with open(os.path.expanduser("~/.config/plasma-org.kde.plasma.desktop-appletsrc")) as f:
                contents = f.read()
            match = re.search(r'Image=(.*)', contents)
            if match:
                return match.group(1)
        
        elif "hyprland" in desktop:
            if os.path.exists(os.path.expanduser("~/.config/hypr/hyprpaper.conf")):
                with open(os.path.expanduser("~/.config/hypr/hyprpaper.conf")) as f:
                    contents = f.read()
                match = re.search(r'wallpaper\s*=\s*(.*)', contents)
                if match:
                    out = match.group(1).strip()
                    if ',' in out:
                        return out.split(',')[-1].strip()
                    return out
            return None
        
        elif "darwin" in OS.lower() :
            out = subprocess.check_output([
                "osascript", "-e",
                'tell application "Finder" to get POSIX path of (desktop picture as alias)'
            ], text=True).strip()
            return out

        elif "windows" in OS.lower():
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop") as key:
                value, _ = winreg.QueryValueEx(key, "WallPaper")
                return value

    except Exception as e:
        logging.error("Error retrieving wallpaper: %s", e)

    return None
