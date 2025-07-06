# Blender-Wallpaper-for-all
Dependency-free addon for blender on windows/mac/linux that creates a theme based on your wallpaper!

Uses a modified colorz.py to retrieve wallpaper colors- retrieves the images via blender's bpy and uses a weighted k-mean to determine the most commonly occurring colors. 
Credit to `https://github.com/metakirby5/colorz`
and `https://github.com/dylanaraps/pywal` whose code I incorporated into this project.
Features adjustments for saturation, whether the colors apply to the xyz-axes, whether the k-mean is seeded (same theme for the same wallpaper), and accuracy (the max number of times the k-mean iterates)
For some reason I find the k-mean to be much slower on windows- I recommend keeping accuracy low, it doesn't make too much of a difference anyways.
