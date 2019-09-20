bl_info = {  
 "name": "Palette Generator",  
 "author": "mac7ua",  
 "version": (1, 3),
 "blender": (2, 80, 0),  
 "location": "Texture Paint",  
 "description": "Key (G) - Generate palette",  
 "warning": "",  
 "wiki_url": "",  
 "tracker_url": "",  
 "category": "Paint"}

import bpy
import requests
import json
from mathutils import Color
from inspect import getsource
from bl_ui.properties_paint_common import (
    UnifiedPaintPanel,
)
        
addon_keymaps = []
class PaletteGenerator(bpy.types.Operator):
    bl_idname = "paint.pallet_generator"
    bl_label = "PaletteGenerator"
    bl_description = "Generate a color palette"
    bl_options = {'REGISTER', 'UNDO'}
    
    type: bpy.props.EnumProperty(items=[('mix','Mix',''),('line','Line',''),('spectrum','Spectrum',''),('colormind','Colormind.io','')], name="Type")
    steps: bpy.props.IntProperty(name="Steps", default=15, min=1, max=100, subtype='PERCENTAGE')
    use_color1: bpy.props.BoolProperty(name="First", default=True)
    use_color2: bpy.props.BoolProperty(name="Secondary", default=True)
    status : bpy.props.StringProperty(name="Status",default="")
    Colormind_list = [('default','default','')]
    def enum_items(self,context):
        return PaletteGenerator.Colormind_list
    Colormind_models: bpy.props.EnumProperty(items=enum_items, name="Models")
    colorList=list(tuple())
    
    
    def CreatePalette(self,context): 
        palette = bpy.data.palettes.get("PaletteGenerator")
        if palette is None:
            palette = bpy.data.palettes.new('PaletteGenerator')
        else:
            palette.colors.clear()
        for i in self.colorList:
            palette_color = palette.colors.new()
            palette_color.color = Color(i)
        context.tool_settings.image_paint.palette = palette
        return {'FINISHED'} 
    
    def LineColor(self, color1): 
        col1 = color1
        col4 = Color((self.steps/100,self.steps/100,self.steps/100))
        TmpLib=list(tuple())
        for i in range(4):            
            col1=col1-col4
            TmpLib.append(col1)
                     
        for j in reversed(range(4)):
            self.colorList.append(TmpLib[j])
        col1 = color1
        self.colorList.append(col1)
        for i in range(4):            
            col1=col1+col4
            self.colorList.append(col1)
        return {'FINISHED'}
    
    def Colormind(self, context, color1, color2):
        self.status=""
        if len(self.Colormind_list)<=1:
            try:
                result_list = requests.post("http://colormind.io/list/", timeout=2.0)
            except requests.Timeout:
                self.status="Timeout"
                return {'FINISHED'}
            except requests.ConnectionError:
                self.status="Connection Error"
                return {'FINISHED'}
            except requests.RequestException:
                self.status="Unknown Error"
            else:
                list = json.loads(result_list.text)
                model_list = [('default','default','')]
                for i in range(len(list["result"])):
                    if list["result"][i] != "default":
                        model_list.append((list["result"][i],list["result"][i],''))
                PaletteGenerator.Colormind_list = model_list.copy()    
        col1=[color1[0]*256, color1[1]*256, color1[2]*256]
        col2=[color2[0]*256, color2[1]*256, color2[2]*256]
        if self.use_color1==False:
            col1="N"
        if self.use_color2==False:
            col2="N"
        try:
            result = requests.post("http://colormind.io/api/", json=({ "model" : self.Colormind_models, "input" : [col1, "N", "N","N",col2]}), timeout=2.0) 
        except requests.Timeout:
            self.status="Timeout"
        except requests.ConnectionError:
            self.status="Connection Error"
        except requests.RequestException:
            self.status="Unknown Error"
        else:
            colors=json.loads(result.text)
            k=1/256
            for i in range(len(colors["result"])):
                self.colorList.append(Color((k*colors["result"][i][0],k*colors["result"][i][1],k*colors["result"][i][2])))
            pass
        return {'FINISHED'}
    
    def SpectrumColor(self, color1):
        color=[color1[0],color1[1],color1[2]]
        color.sort()
        color[1]=color[0]+(color[2]-color[0])/2
        
        self.colorList.append((color[2], color[0], color[2]))
        self.colorList.append((color[1], color[0], color[2]))                 
        self.colorList.append((color[0], color[0], color[2]))
        self.colorList.append((color[0], color[1], color[2]))           
        self.colorList.append((color[0], color[2], color[2]))
        self.colorList.append((color[0], color[2], color[1]))      
        self.colorList.append((color[0], color[2], color[0]))
        self.colorList.append((color[1], color[2], color[0]))    
        self.colorList.append((color[2], color[2], color[0]))
        self.colorList.append((color[2], color[1], color[0]))       
        self.colorList.append((color[2], color[0], color[0]))
        self.colorList.append((color[2], color[0], color[1]))
        return {'FINISHED'} 
      
    def MixColor(self, color1, color2): 
        k=self.steps/100
        col1 = color1
        tmpcolor=[color2[0],color2[1],color2[2]]
        tmpcolor.sort()
        col2 = color2 - Color((tmpcolor[0],tmpcolor[1],tmpcolor[0]))          
        col3 = Color((1,1,1))*k        
        TmpLib=list(tuple())
        for i in range(4):            
            col1=(col1+col2*k)*(1-k)
            TmpLib.append(col1)
                     
        for j in reversed(range(4)):
            self.colorList.append(TmpLib[j])
            
        col1 = color1    
        self.colorList.append(col1)
        for i in range(4):            
            col1=col1+col2*k
            self.colorList.append(col1)
        return {'FINISHED'}
    
    def draw(self, context):
        col = self.layout.column()
        col.prop(self, "type")
        if self.type=="mix" or self.type=="line":
            col.prop(self, "steps")
        elif self.type=="colormind":
            if self.status=="":
                col.prop(self, "Colormind_models")             
                col.label(text="Use Color:")
                row = self.layout.row()
                row.prop(self, "use_color1")
                row.prop(self, "use_color2")
            else:
                col.label(text=self.status)
    
    def execute(self, context):
        color1 = context.tool_settings.image_paint.brush.color.copy()
        color2 = context.tool_settings.image_paint.brush.secondary_color.copy()
        self.colorList=list(tuple())
        if self.type=="mix":
            self.MixColor(color1, color2)
        elif self.type=="line":
            self.LineColor(color1)
        elif self.type=="spectrum":
            self.SpectrumColor(color1)
        elif self.type=="colormind":
            self.Colormind(context, color1, color2)
        self.CreatePalette(context)
        return {'FINISHED'}
def draw_(self, context):
    pass

def palette_context_menu(self, context):
    layout = self.layout
    settings = context.tool_settings.image_paint
    capabilities = settings.brush.image_paint_capabilities
    if capabilities.has_color:
        split = layout.split(factor=0.1)
        column = split.column()
        UnifiedPaintPanel.prop_unified_color(column, context, settings.brush, "color", text="")
        UnifiedPaintPanel.prop_unified_color(column, context, settings.brush, "secondary_color", text="")
        column.operator("paint.brush_colors_flip", icon='FILE_REFRESH', text="", emboss=False)
        column.operator(PaletteGenerator.bl_idname, icon='MOD_OPACITY', text="", emboss=False)
        UnifiedPaintPanel.prop_unified_color_picker(split, context, settings.brush, "color", value_slider=True)
        layout.prop(settings.brush, "blend", text="")

    if capabilities.has_radius:
        UnifiedPaintPanel.prop_unified_size(layout, context, settings.brush, "size", slider=True)
    UnifiedPaintPanel.prop_unified_strength(layout, context, settings.brush, "strength")
    if settings.palette:
        layout.template_palette(settings, "palette", color=True)
    
def register():
    bpy.utils.register_class(PaletteGenerator)
    bpy.types.VIEW3D_PT_paint_texture_context_menu.append(draw_)
    bpy.types.VIEW3D_PT_paint_texture_context_menu.draw_= bpy.types.VIEW3D_PT_paint_texture_context_menu.draw
    bpy.types.VIEW3D_PT_paint_texture_context_menu.draw = palette_context_menu
    
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new('Image Paint', space_type='EMPTY', region_type='WINDOW', modal=False)
        kmi = km.keymap_items.new(PaletteGenerator.bl_idname, 'G', 'PRESS')
        addon_keymaps.append(km)
        
def unregister():
    bpy.utils.unregister_class(PaletteGenerator)
    bpy.types.VIEW3D_PT_paint_texture_context_menu.draw= bpy.types.VIEW3D_PT_paint_texture_context_menu.draw_
    bpy.types.VIEW3D_PT_paint_texture_context_menu.remove(draw_)
    wm = bpy.context.window_manager
    for km in addon_keymaps:
        wm.keyconfigs.addon.keymaps.remove(km)
    del addon_keymaps[:]
    
if __name__ == "__main__":
    register()
