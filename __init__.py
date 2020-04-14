bl_info = {
    "name": "Tivoli Blender Tools",
    "author": "Tivoli Cloud VR, Inc.",
    "description": "",
    "version": (0, 0, 1),
    "blender": (2, 82, 0),
    "location": "View 3D > Tool Shelf > Tivoli",
    "warning": "",
    "category": "3D View",
}

import bpy

from .operators.prepare_uv_maps import *
from .operators.prepare_materials import *
from .operators.bake_scene import *
from .operators.export_scene import *

class TivoliSettings(bpy.types.PropertyGroup):
	bake_current: bpy.props.StringProperty(name="Bake current", default="")
	bake_progress: bpy.props.FloatProperty(
	    name="Bake progress",
	    default=-1,
	    subtype="PERCENTAGE",
	    min=-1,
	    soft_min=0,
	    soft_max=100,
	    max=101
	)

class ToolPanel(bpy.types.Panel):
	bl_idname = "VIEW3D_PT_tivoli"
	bl_label = "Tivoli Blender Tools"

	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Tivoli"

	def draw(self, context):
		layout = self.layout

		bake_buttons = layout.box()
		bake_buttons.label(icon="SHADING_RENDERED", text="Baking pipeline")
		bake_buttons.operator(
		    icon="GROUP_UVS",
		    text="Prepare UV maps",
		    operator="tivoli.prepare_uv_maps",
		)
		bake_buttons.operator(
		    icon="MATERIAL",
		    text="Prepare materials",
		    operator="tivoli.prepare_materials",
		).restore = False
		bake_buttons.operator(
		    icon="MATERIAL",
		    text="Restore materials",
		    operator="tivoli.prepare_materials",
		).restore = True
		bake_buttons.operator(
		    icon="RENDER_STILL",
		    text="Bake scene",
		    operator="tivoli.bake_scene"
		)
		bake_buttons.operator(
		    icon="EXPORT", text="Export scene", operator="tivoli.export_scene"
		)

		progress = context.scene.tivoli_settings.bake_progress
		if progress > 0 and progress < 100:
			bake_progress = layout.box()
			bake_progress.label(icon="RENDER_STILL", text="Currently baking...")
			bake_progress.prop(
			    context.scene.tivoli_settings, "bake_current", text=""
			)
			bake_progress.prop(
			    context.scene.tivoli_settings,
			    "bake_progress",
			    text="Total bake progress",
			    slider=True
			)

classes = (
    TivoliSettings, PrepareUVMaps, PrepareMaterials, BakeScene, ExportScene,
    ToolPanel
)

main_register, main_unregister = bpy.utils.register_classes_factory(classes)

def register():
	main_register()

	bpy.types.Scene.tivoli_settings = bpy.props.PointerProperty(
	    type=TivoliSettings
	)

def unregister():
	main_unregister()
