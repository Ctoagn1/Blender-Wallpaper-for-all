bl_info = {
    "name": "Wal Theme",
    "author": "Ctoagn1",
    "version": (1, 0),
    "blender": (4, 4, 3),
    "location": "File > Apply Wallpaper Theme",
    "description": "Applies wallpaper colors as Blender theme",
    "category": "Interface",
}
        

import bpy
import os
import re
import colorsys
from . import wallpaper
from . import colorz
from bpy.types import Panel, Operator

def init_properties():
    bpy.types.Scene.axis_shift = bpy.props.BoolProperty(
        name='Apply to Axis/Grid',
        default=True
    )
    bpy.types.Scene.rand_shift = bpy.props.BoolProperty(
        name='Random/Unseeded Theme',
        default=False
    )
    
    bpy.types.Scene.saturation_shift = bpy.props.FloatProperty(
        name='Saturation Shift',
        default=1.0,
        soft_min=0.0,
        soft_max=3.0
    )

def clear_properties():
    del bpy.types.Scene.axis_shift
    del bpy.types.Scene.saturation_shift
    del bpy.types.Scene.rand_shift

class MainPanel(bpy.types.Panel):
    bl_label = "Wal Theme"
    bl_idname = "WAL_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'wal'
    
    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "axis_shift")
        layout.prop(context.scene, "rand_shift")
        layout.prop(context.scene, "saturation_shift")
        layout.operator("wal.operator")
        
class WAL_operator(bpy.types.Operator):
    bl_idname = "wal.operator"
    bl_label = "Make Wallpaper Theme"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Makes Blender theme from wallpaper colors accessible under Preferences > Themes"
    
    def modulate(self, val, mod, sat): 
        r=int(val[1:3], 16)/255.0
        g=int(val[3:5], 16)/255.0
        b=int(val[5:7], 16)/255.0
        h,l,s=colorsys.rgb_to_hls(r, g, b)
        l=max(0.0, min(1.0, l*mod))         
        s=max(0.0, min(1.0, s*sat*0.8/(mod))) 
        r, g, b=colorsys.hls_to_rgb(h, l, s)
        r=f"{int(r * 255):02x}"
        g=f"{int(g * 255):02x}"
        b=f"{int(b* 255):02x}"
        return "#"+r+g+b

    def apply_colors(self, home, workingdir, blenderversion, axis_change, saturation, rand):
        image = wallpaper.get_desktop_wallpaper(wallpaper.get_desktop_env())
        try:
            image = os.path.expanduser(os.path.normpath(image.replace('$HOME', '~')))
        except:
            pass
        if image is None:
            self.report({'ERROR'}, "Could not find wallpaper")
            return {'CANCELLED'}
        raw_colors = colorz.colorz(bpy.data.images.load(image), n=6, bold_add=0, randomness=rand)
        colors =["#000000"] + [wallpaper.rgb_to_hex([*color[0]]) for color in raw_colors]
        while len(colors)<30:
            colors.append("#000000")
        



        for i in range(9,16):
            colors[i] = self.modulate(colors[i-8], .6, saturation)
            colors[i+7] = self.modulate(colors[i-8], 1.25, saturation)
            colors[i+14] = self.modulate(colors[i-8], .4, saturation)
        with open(f"{workingdir}/blendertemplate.xml", "r") as templatefile:
            contents = templatefile.read()
        for i in range(0, 26):
            contents = re.sub("color"+str(i)+"_", colors[i], contents)
        if axis_change:
            contents = re.sub("x-axis-color_", colors[20], contents)
            contents = re.sub("y-axis-color_", colors[21], contents)
            contents = re.sub("z-axis-color_", colors[22], contents)
            contents = re.sub("grid-color_", colors[19], contents)
        else:
            contents = re.sub("x-axis-color_", "#ff3352", contents)
            contents = re.sub("y-axis-color_", "#8bdc00", contents)
            contents = re.sub("z-axis-color_", "#2890ff", contents)
            contents = re.sub("grid-color_", "#545454", contents)
        os.makedirs(f"{home}/.config/blender/{blenderversion}/scripts/presets/interface_theme", exist_ok=True)
        with open(f"{home}/.config/blender/{blenderversion}/scripts/presets/interface_theme/Wal_Theme.xml", "w") as templatefile:
            templatefile.write(contents)
        

    def execute(self, context):
        workingdir = os.path.dirname(os.path.abspath(__file__))
        home = os.path.expanduser("~")
        blenderversion = f"{bpy.app.version[0]}.{bpy.app.version[1]}"
        self.apply_colors(home, workingdir, blenderversion, context.scene.axis_shift, context.scene.saturation_shift, context.scene.rand_shift)
        return {'FINISHED'}
    
classes = [
    MainPanel,
    WAL_operator,
]
    
def register():
    for c in classes:
        bpy.utils.register_class(c)
    init_properties()

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    clear_properties()
      
if __name__ == "__main__":
    register()

