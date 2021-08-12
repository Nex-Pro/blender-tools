import bpy

class AnimationPanel(bpy.types.Panel):
	bl_idname = "VIEW3D_PT_tivoli_animation"
	bl_label = "Animation tools"
	bl_icon = "OBJECT_DATA"
	bl_category = "Tivoli"

	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"

	def draw(self, context):
		layout = self.layout

		mdd_info = layout.column(align=True)
		mdd_info.label(icon="INFO", text="Make sure the addon:")
		mdd_info.label(text="\"NewTek MDD format\"")
		mdd_info.label(text="is enabled before use.")

		layout.operator(
		    icon="PHYSICS",
		    text="Bake physics with MDD",
		    operator="tivoli.animation_bake_physics_with_mdd"
		)

		bake_info = layout.column(align=True)
		bake_info.label(icon="INFO", text="Please try to keep")
		bake_info.label(text="vertices to less than 1000.")

		layout.operator(
		    icon="BONE_DATA",
		    text="Shape key animation to bones",
		    operator="tivoli.animation_shape_key_animation_to_bones"
		)

		export_info = layout.column(align=True)
		export_info.label(icon="INFO", text="Be sure to export as FBX with")
		export_info.label(text="\"...Animation > Simplify\" set to 0.")
