import bpy

class ExportScenePanel(bpy.types.Panel):
	bl_idname = "VIEW3D_PT_tivoli_export_scene"
	bl_label = "Export scene to JSON"
	bl_icon = "OBJECT_DATA"
	bl_category = "Tivoli"

	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"

	def draw(self, context):
		layout = self.layout
		tivoli_settings = context.scene.tivoli_settings

		layout.label(text="Export URL", icon="URL")
		layout.prop(tivoli_settings, "export_scene_url", text="")
		layout.prop(tivoli_settings, "export_scene_webp")

		op = layout.operator(
		    icon="EXPORT",
		    text="Export scene to JSON",
		    operator="tivoli.export_scene"
		)
		op.base_url = tivoli_settings.export_scene_url
		op.webp_textures = tivoli_settings.export_scene_webp
