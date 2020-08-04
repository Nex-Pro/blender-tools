import bpy

from mathutils import Quaternion, Matrix, Vector, Euler

from .lib.tivoli_skeleton import tivoli_skeleton

class AvatarForceTPose(bpy.types.Operator):
	bl_idname = "tivoli.avatar_force_tpose"
	bl_label = "Tivoli: Force T-Pose"
	bl_options = {"REGISTER", "UNDO", "INTERNAL"}

	clear: bpy.props.BoolProperty(
	    name="Clear T-Pose", default=False, options={"HIDDEN"}
	)

	# https://github.com/Menithal/Blender-Metaverse-Addon/blob/8222b670a2e92158d0c58b2260230b441176ee68/metaverse_tools/utils/bones/bones_builder.py#L676

	def find_armature(self, selection):
		for selected in selection:
			print(selected, selected.parent)
			if selected.type == "ARMATURE":
				return selected
			if selected.type == "MESH" and selected.parent is not None and selected.parent.type == "ARMATURE":
				return selected.parent
		return None

	def navigate_armature(
	    self, data, current_rest_node, world_matrix, parent, parent_node
	):
		name = current_rest_node["name"]
		bone = data.get(name)
		if (bone):
			bone.rotation_mode = "QUATERNION"
			destination_matrix = current_rest_node["matrix_local"].copy()
			inv_destination_matrix = destination_matrix.inverted()
			matrix = bone.matrix
			if parent:
				parent_matrix = parent.matrix.copy()
				parent_inverted = parent_matrix.inverted()
				parent_destination = parent_node["matrix_local"].copy()
			else:
				parent_matrix = Matrix()
				parent_inverted = Matrix()
				parent_destination = Matrix()
			smat = inv_destination_matrix @ (
			    parent_destination @ (parent_inverted @ matrix)
			)
			bone.rotation_quaternion = smat.to_quaternion().inverted()
			for child in current_rest_node["children"]:
				self.navigate_armature(
				    data, child, world_matrix, bone, current_rest_node
				)
		else:
			bone = parent
			for child in current_rest_node["children"]:
				self.navigate_armature(
				    data, child, world_matrix, bone, parent_node
				)

	def reset_scale_rotation(self, obj):
		mode = bpy.context.area.type
		bpy.context.area.type = "VIEW_3D"
		bpy.ops.object.mode_set(mode="OBJECT")
		bpy.ops.view3d.snap_cursor_to_center('INVOKE_DEFAULT')
		bpy.context.area.type = mode
		bpy.ops.object.select_all(action="DESELECT")

		obj.select_set(True)
		bpy.ops.object.transform_apply(
		    location=False, rotation=True, scale=True
		)

		mode = mode

	def correct_scale_rotation(self, obj, rotation):
		self.reset_scale_rotation(obj)
		obj.scale = Vector((100.0, 100.0, 100.0))
		print(obj.scale)
		str_angle = -90 * pi / 180
		if rotation:
			obj.rotation_euler = Euler((str_angle, 0, 0), "XYZ")

		self.reset_scale_rotation(obj)

		obj.scale = Vector((0.01, 0.01, 0.01))
		if rotation:
			obj.rotation_euler = Euler((-str_angle, 0, 0), "XYZ")

	def clear_pose(self, selected):
		armature = self.find_armature(selected)
		if armature is not None:
			mode = bpy.context.mode
			bpy.ops.object.mode_set(mode="OBJECT")

			print("Deselect all")
			bpy.ops.object.select_all(action="DESELECT")
			print("Selected")

			bpy.context.view_layer.objects.active = armature
			armature.select_set(state=True)
			bpy.context.object.data.pose_position = 'POSE'

			bpy.ops.object.mode_set(mode="POSE")
			bpy.ops.pose.select_all(action="SELECT")
			bpy.ops.pose.transforms_clear()
			bpy.ops.pose.select_all(action="DESELECT")

			bpy.ops.object.mode_set(mode=mode)

	def retarget_armature(self, options, selected, selected_only=False):
		armature = self.find_armature(selected)
		if armature is not None:
			# Center Children First
			bpy.context.view_layer.objects.active = armature
			armature.select_set(state=True)
			bpy.context.object.data.pose_position = 'POSE'

			bpy.ops.object.mode_set(mode="OBJECT")
			# Make sure to reset the bones first.
			bpy.ops.object.transform_apply(
			    location=False, rotation=True, scale=True
			)
			print("Selecting Bones")

			bpy.ops.object.mode_set(mode="POSE")
			bpy.ops.pose.select_all(action="SELECT")
			bpy.ops.pose.transforms_clear()
			bpy.ops.pose.select_all(action="DESELECT")

			print("---")

			# Now lets do the repose to rest
			world_matrix = armature.matrix_world
			bones = armature.pose.bones

			for bone in tivoli_skeleton:
				print("Iterating Bones", bone["name"])
				self.navigate_armature(bones, bone, world_matrix, None, None)

			print("Moving Next")
			# Then apply everything
			if options["apply"]:

				print("Applying Scale")
				if bpy.context.mode != "OBJECT":
					bpy.ops.object.mode_set(mode="OBJECT")

				print("Correcting Scale and Rotations")
				self.correct_scale_rotation(armature, True)

				print(" Correcting child rotations and scale")
				for child in armature.children:
					if selected_only == False or child.select_get():
						self.correct_scale_rotation(child, False)

				bpy.context.view_layer.objects.active = armature

			armature.select_set(state=True)

			print("Done")
		else:
			# Judas proofing:
			print("No Armature, select, throw an exception")
			raise Exception("You must have an armature to continue")

	def execute(self, context):
		if self.clear:
			self.clear_pose(bpy.context.view_layer.objects)
		else:
			self.retarget_armature(
			    {"apply": False}, bpy.context.view_layer.objects
			)

		bpy.ops.object.mode_set(mode="OBJECT")

		return {"FINISHED"}