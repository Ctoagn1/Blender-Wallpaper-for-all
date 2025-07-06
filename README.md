# Blender-Wallpaper-for-all
Dependency-free addon for blender on windows/mac/linux that creates a theme based on your wallpaper!
Download with `git clone https://github.com/Ctoagn1/Blender-Wallpaper-for-all/` and go to Preferences > Add-ons > Install from Disk and load the zip. 

Uses a modified colorz.py to retrieve wallpaper colors- retrieves the images via blender's bpy and uses a weighted k-mean to determine the most commonly occurring colors. 
Credit to `https://github.com/metakirby5/colorz`
and `https://github.com/dylanaraps/pywal` whose code I incorporated into this project.
Note- creating the theme can take a few seconds! To avoid dependencies on scipy I rewrote the k-mean method in python- it's not the fastest!

# Features 
Features adjustments for saturation, whether the colors apply to the xyz-axes, whether the k-mean is seeded (same theme for the same wallpaper), and accuracy (the max number of times the k-mean iterates)
For some reason I find the k-mean to be much slower on windows- I recommend keeping accuracy low, it doesn't make too much of a difference anyways.

# Also check out:
For those of you on linux, I recommend my pywal-dependent version- `https://github.com/Ctoagn1/blender-wal` The imagemagick backend tends to look much more cohesive and runs much faster.
