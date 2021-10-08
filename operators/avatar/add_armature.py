import bpy

from .lib.tivoli_skeleton import tivoli_skeleton
from ... import utils

class AvatarAddArmature(bpy.types.Operator):
	bl_idname = "tivoli.avatar_add_armature"
	bl_label = "Tivoli: Add Skeleton"
	bl_options = {"REGISTER", "UNDO", "INTERNAL"}

	# https://github.com/Menithal/Blender-Metaverse-Addon/blob/master/metaverse_tools/utils/bones/bones_builder.py

	def build_armature_structure(self, data, current_node, parent):
		name = current_node["name"]
		bpy.ops.armature.bone_primitive_add(name=name)

		current_bone_index = data.edit_bones.find(name)
		current_bone = data.edit_bones[current_bone_index]

		current_bone.parent = parent

		current_bone.head = current_node["head"]
		current_bone.tail = current_node["tail"]
		mat = current_node["matrix"]
		current_bone.matrix = mat

		if current_node["connect"]:
			current_bone.use_connect = True

		for child in current_node["children"]:
			self.build_armature_structure(data, child, current_bone)

		return current_bone

	def execute(self, context):
		current_view = bpy.context.area.type

		try:
			# set context to 3D View and set Cursor
			bpy.context.area.type = "VIEW_3D"
			bpy.context.scene.cursor.location[0] = 0.0
			bpy.context.scene.cursor.location[1] = 0.0
			bpy.context.scene.cursor.location[2] = 0.0

			if bpy.context.active_object:
				bpy.ops.object.mode_set(mode="OBJECT")

			bpy.ops.object.add(type="ARMATURE", enter_editmode=True)

			current_armature = bpy.context.active_object

			current_armature.name = "Armature"
			for root_bone in tivoli_skeleton:
				self.build_armature_structure(
				    current_armature.data, root_bone, None
				)

			utils.ensure_root_bone(current_armature)

		except Exception as exception:
			raise exception

		finally:
			bpy.context.area.type = current_view

		return {"FINISHED"}