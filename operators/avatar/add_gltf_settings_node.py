import bpy

from ...functions.gltf_settings_node import *

class AvatarAddGltfSettingsNode(bpy.types.Operator):
	bl_idname = "tivoli.avatar_add_gltf_settings_node"
	bl_label = "Tivoli: Add \"glTF Settings\" node"
	bl_options = {"REGISTER", "UNDO", "INTERNAL"}

	def execute(self, context):
		get_gltf_settings_node()

		return {"FINISHED"}
