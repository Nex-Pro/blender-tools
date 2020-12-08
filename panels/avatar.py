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

		# layout.label(text="Things to add", icon="PLUS")

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

		layout.separator()
		layout.label(text="Preview and fix your avatar")

		tpose = layout.row()
		op = tpose.operator(
		    icon="OUTLINER_OB_ARMATURE",
		    text="Force T-Pose",
		    operator="tivoli.avatar_force_tpose"
		)
		op.clear = False
		op = tpose.operator(
		    icon="ARMATURE_DATA",
		    text="Clear T-Pose",
		    operator="tivoli.avatar_force_tpose"
		)
		op.clear = True

		layout.operator(
		    icon="BONE_DATA",
		    text="Fix bone rotations",
		    operator="tivoli.avatar_fix_bone_rotations"
		)

		layout.separator()

		# layout.label(text="Rename bones")
