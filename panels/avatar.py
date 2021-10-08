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

		# ---

		layout.separator()
		layout.label(icon="OPTIONS", text="Preview and fix your avatar")

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
		    text="Ensure/add root bone",
		    operator="tivoli.avatar_ensure_root_bone"
		)

		# ---

		layout.separator()
		layout.label(icon="ERROR", text="Be careful, can make worse!")

		layout.operator(
		    icon="CONSTRAINT_BONE",
		    text="Fix bone rotations",
		    operator="tivoli.avatar_fix_bone_rotations"
		)

		# extras

		tivoli_settings = context.scene.tivoli_settings

		layout.separator()
		layout.prop(
		    tivoli_settings,
		    "avatar_extras",
		    text="Extras that aren't needed",
		)

		if tivoli_settings.avatar_extras:
			layout.operator(
			    icon="NODETREE",
			    text="Add Tivoli settings node",
			    operator="tivoli.avatar_add_tivoli_settings_node"
			)

			layout.operator(
			    icon="NODETREE",
			    text="Add \"glTF Settings\" node",
			    operator="tivoli.avatar_add_gltf_settings_node"
			)
