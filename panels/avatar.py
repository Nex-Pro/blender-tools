import bpy

class AvatarPanel(bpy.types.Panel):
	bl_idname = "VIEW3D_PT_tivoli_avatar"
	bl_label = "Avatar tools"
	bl_icon = "OBJECT_DATA"
	bl_category = "Tivoli"

	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"

	def draw(self, context):
		layout = self.layout

		layout.operator(
		    icon="OUTLINER_OB_ARMATURE",
		    text="Add Tivoli armature",
		    operator="tivoli.avatar_add_armature"
		)

		layout.operator(
		    icon="NODETREE",
		    text="Add Tivoli settings node",
		    operator="tivoli.avatar_add_tivoli_settings_node"
		)
