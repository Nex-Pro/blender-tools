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

from .operators.bake_prepare_uv_maps import *
from .operators.bake_prepare_materials import *
from .operators.bake_scene import *
from .operators.bake_export_scene import *

from .operators.export_scene import *

class TivoliSettings(bpy.types.PropertyGroup):
	export_scene_expand: bpy.props.BoolProperty(
	    name="Export scene", default=False
	)

	export_scene_url: bpy.props.StringProperty(name="Export URL", default="")

	export_scene_webp: bpy.props.BoolProperty(
	    name="WebP texture optimize", default=True
	)

	# ---

	bake_expand: bpy.props.BoolProperty(
	    name="Lightmap baking (don't use!)", default=False
	)

	bake_texture_size: bpy.props.EnumProperty(
	    name="Texture size",
	    items=[
	        ("128", "128", ""),
	        ("256", "256", ""),
	        ("512", "512", ""),
	        ("1024", "1024", ""),
	        ("2048", "2048", ""),
	        ("4096", "4096", ""),
	        ("8192", "8192", ""),
	    ],
	    options={'ENUM_FLAG'},
	    default={"1024"}
	)

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
		tivoli_settings = context.scene.tivoli_settings

		export_scene = layout.box()
		export_scene_expand = export_scene.row()
		export_scene_expand.prop(
		    tivoli_settings,
		    "export_scene_expand",
		    icon="TRIA_DOWN"
		    if tivoli_settings.export_scene_expand else "TRIA_RIGHT",
		    emboss=False
		)
		if tivoli_settings.export_scene_expand:
			export = export_scene.box()
			export.label(text="Export URL", icon="URL")
			export.prop(tivoli_settings, "export_scene_url", text="")
			export.prop(tivoli_settings, "export_scene_webp")
			export.operator(
			    icon="EXPORT",
			    text="Export scene to JSON",
			    operator="tivoli.export_scene"
			)

		# ---

		bake = layout.box()
		bake_expand = bake.row()
		bake_expand.prop(
		    tivoli_settings,
		    "bake_expand",
		    icon="TRIA_DOWN" if tivoli_settings.bake_expand else "TRIA_RIGHT",
		    emboss=False
		)
		if tivoli_settings.bake_expand:
			uv_maps = bake.box()
			uv_maps.label(text="1. Prepare UV maps", icon="GROUP_UVS")
			uv_maps.operator(
			    # icon="GROUP_UVS",
			    text="Prepare UV maps",
			    operator="tivoli.bake_prepare_uv_maps",
			)

			# prepare materials
			prepare_materials = bake.box()
			prepare_materials.label(
			    text="2. Prepare materials", icon="MATERIAL"
			)
			prepare_materials.label(text="Texture size:")
			prepare_materials.prop(
			    tivoli_settings,
			    "bake_texture_size",
			    expand=True,
			)
			prepare_materials.operator(
			    text="Prepare materials",
			    operator="tivoli.bake_prepare_materials",
			).restore = False
			prepare_materials.operator(
			    text="Restore materials",
			    operator="tivoli.bake_prepare_materials",
			).restore = True

			# bake and export
			final = bake.box()
			final.label(text="3. Bake and export", icon="RENDER_STILL")
			final.operator(
			    icon="RENDER_STILL",
			    text="Bake scene",
			    operator="tivoli.bake_scene"
			)
			final.operator(
			    icon="EXPORT",
			    text="Export scene",
			    operator="tivoli.bake_export_scene"
			)

			progress = tivoli_settings.bake_progress
			if progress > 0 and progress < 100:
				bake_progress = bake.box()
				bake_progress.label(
				    icon="RENDER_STILL", text="Currently baking..."
				)
				bake_progress.prop(tivoli_settings, "bake_current", text="")
				bake_progress.prop(
				    tivoli_settings,
				    "bake_progress",
				    text="Total bake progress",
				    slider=True
				)

classes = (
    TivoliSettings, BakePrepareUVMaps, BakePrepareMaterials, BakeScene,
    BakeExportScene, SceneExport, ToolPanel
)

main_register, main_unregister = bpy.utils.register_classes_factory(classes)

def register():
	main_register()

	bpy.types.Scene.tivoli_settings = bpy.props.PointerProperty(
	    type=TivoliSettings
	)

def unregister():
	main_unregister()
