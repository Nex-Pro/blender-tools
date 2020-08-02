import bpy

from ...functions.tivoli_settings_node import *

class AvatarAddTivoliSettingsNode(bpy.types.Operator):
	bl_idname = "tivoli.avatar_add_tivoli_settings_node"
	bl_label = "Tivoli: Add Tivoli settings node"
	bl_options = {"REGISTER", "UNDO", "INTERNAL"}

	def execute(self, context):
		get_tivoli_settings_node()

		return {"FINISHED"}
