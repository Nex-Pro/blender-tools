import bpy

class LightmapPanel(bpy.types.Panel):
	bl_idname = "VIEW3D_PT_tivoli_lightmap_baking"
	bl_label = "Lightmap baking (don't use)"
	bl_icon = "OBJECT_DATA"
	bl_category = "Tivoli"

	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"

	def draw(self, context):
		layout = self.layout
		tivoli_settings = context.scene.tivoli_settings

		# uv maps
		uv_maps = layout.box()
		uv_maps.label(text="1. Prepare UV maps", icon="GROUP_UVS")
		uv_maps.operator(
		    # icon="GROUP_UVS",
		    text="Prepare UV maps",
		    operator="tivoli.lightmap_prepare_uv_maps",
		)

		# prepare materials
		prepare_materials = layout.box()
		prepare_materials.label(text="2. Prepare materials", icon="MATERIAL")
		prepare_materials.label(text="Texture size:")
		prepare_materials.prop(
		    tivoli_settings,
		    "bake_texture_size",
		    expand=True,
		)
		prepare_materials.operator(
		    text="Prepare materials",
		    operator="tivoli.lightmap_prepare_materials",
		).restore = False
		prepare_materials.operator(
		    text="Restore materials",
		    operator="tivoli.lightmap_prepare_materials",
		).restore = True

		# bake and export
		final = layout.box()
		final.label(text="3. Bake and export", icon="RENDER_STILL")
		final.operator(
		    icon="RENDER_STILL",
		    text="Bake scene",
		    operator="tivoli.lightmap_bake_scene"
		)
		final.operator(
		    icon="EXPORT",
		    text="Export scene",
		    operator="tivoli.lightmap_export_scene"
		)
		progress = tivoli_settings.bake_progress
		if progress > 0 and progress < 100:
			bake_progress = layout.box()
			bake_progress.label(icon="RENDER_STILL", text="Currently baking...")
			bake_progress.prop(tivoli_settings, "bake_current", text="")
			bake_progress.prop(
			    tivoli_settings,
			    "bake_progress",
			    text="Total bake progress",
			    slider=True
			)
