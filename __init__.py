bl_info = {
    "name" : "Tivoli Blender Tools",
    "author" : "Tivoli Cloud VR, Inc.",
    "description" : "",
    "version" : (0, 0, 1),
    "blender" : (2, 82, 0),
    "location" : "View 3D > Tool Shelf > Tivoli",
    "warning" : "",
    "category" : "3D View"
}

import bpy

from .operators.prepare_uv_maps import *
from .operators.prepare_materials import *
from .operators.bake_scene import *
from .operators.export_scene import *

class ToolPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_tivoli"
    bl_label = "Tivoli Blender Tools"

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tivoli"

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(icon="SHADING_RENDERED", text="Baking pipeline")
        box.operator(icon="GROUP_UVS", text="Prepare UV maps", operator="tivoli.prepare_uv_maps")
        box.operator(icon="MATERIAL", text="Prepare materials", operator="tivoli.prepare_materials")
        box.operator(icon="RENDER_STILL", text="Bake scene", operator="tivoli.bake_scene")
        box.operator(icon="EXPORT", text="Export scene", operator="tivoli.export_scene")

classes = (
    PrepareUVMaps,
    PrepareMaterials,
    BakeScene,
    ExportScene,
    ToolPanel
)

main_register, main_unregister = bpy.utils.register_classes_factory(classes)    

def register():
    main_register()

def unregister():
    main_unregister()
