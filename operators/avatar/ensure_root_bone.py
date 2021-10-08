import bpy
import math

from ... import utils

class AvatarEnsureRootBone(bpy.types.Operator):
	bl_idname = "tivoli.avatar_ensure_root_bone"
	bl_label = "Tivoli: Add root bone"
	bl_options = {"REGISTER", "UNDO", "INTERNAL"}

	def execute(self, context):
		last_view = bpy.context.area.type
		bpy.context.area.type = "VIEW_3D"

		if (
		    not bpy.context.active_object or
		    bpy.context.active_object.type != "ARMATURE"
		):
			raise Exception("Please select a skeleton")

		utils.ensure_root_bone(bpy.context.active_object)

		return {"FINISHED"}