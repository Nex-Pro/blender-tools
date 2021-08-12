import bpy

from ... import utils

class AnimationShapeKeyAnimationToBones(bpy.types.Operator):
	bl_idname = "tivoli.animation_shape_key_animation_to_bones"
	bl_label = "Tivoli: Shape key animation to bones"
	bl_options = {"REGISTER", "UNDO", "INTERNAL"}

	@classmethod
	def poll(self, context):
		return (
		    len(bpy.context.selected_objects) != 0 and
		    bpy.context.active_object.type == "MESH"
		)

	def execute(self, context):
		bpy.context.area.type = "VIEW_3D"

		obj = bpy.context.active_object

		# apply scale and rotation or local/world space will get confusing
		bpy.ops.object.transform_apply(location=True, scale=True, rotation=True)

		# duplicate object
		bpy.ops.object.duplicate()
		new_obj = bpy.context.active_object

		# empty shape keys, vertex groups, and animation
		bpy.ops.object.shape_key_remove(all=True)
		try:
			bpy.ops.object.vertex_group_remove(all=True)
		except:
			pass
		bpy.ops.anim.keyframe_clear_v3d()

		# add armature
		bpy.ops.object.armature_add(
		    radius=0.0,  # dont create initial bone
		    enter_editmode=False,
		    align="WORLD",
		    location=(0, 0, 0),
		    rotation=(0.0, 0.0, 0.0),
		    scale=(0.0, 0.0, 0.0)
		)
		new_arm = bpy.context.active_object
		edit_bones = new_arm.data.edit_bones

		# add bone for each vertex
		bpy.ops.object.mode_set(mode="EDIT", toggle=False)

		# create root bone first, required for tivoli
		root_bone = edit_bones.new("Root")
		root_bone.head = (0.0, 0.0, 0.0)
		root_bone.tail = (0.0, 0.0, 0.1)

		for i in range(0, len(new_obj.data.vertices)):
			vertex = new_obj.data.vertices[i]

			bone = edit_bones.new(str(i))
			bone.head = vertex.co
			bone.tail = (vertex.co[0], vertex.co[1], vertex.co[2] + 0.1)
			bone.parent = root_bone

			# weight it by adding a vertex group
			vertex_group = new_obj.vertex_groups.new(name=str(i))
			vertex_group.add([i], 1.0, "ADD")

		bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

		# add modifier to object
		utils.select_only(new_obj)
		bpy.ops.object.modifier_add(type='ARMATURE')
		new_obj.modifiers.get("Armature").object = new_arm

		# translate shape keys from initial object
		key_blocks = obj.data.shape_keys.key_blocks

		# filter shape key names
		shape_key_frame_names = filter(
		    lambda name: name.startswith("frame_"), key_blocks.keys()
		)

		# get basis shape key for next part
		# shape_key_basis = key_blocks["Basis"]

		# for each shape key (frame_xxxx)
		for shape_key_frame_name in shape_key_frame_names:
			shape_key = key_blocks[shape_key_frame_name]
			frame = int(shape_key_frame_name[len("frame_"):])

			# for each shape key vertex, set pose bone location
			for i in range(0, len(shape_key.data)):

				pose_bone = new_arm.pose.bones[str(i)]

				# world to local conversion
				world_matrix = obj.convert_space(
				    pose_bone=pose_bone,
				    matrix=pose_bone.matrix,
				    from_space="POSE",
				    to_space="WORLD"
				)
				world_matrix.translation = shape_key.data[i].co
				pose_bone.matrix = obj.convert_space(
				    pose_bone=pose_bone,
				    matrix=world_matrix,
				    from_space="WORLD",
				    to_space="POSE"
				)

				pose_bone.keyframe_insert(data_path="location", frame=frame)

		# delete old object and rename new
		obj_name = obj.name
		utils.select_only(obj)
		bpy.ops.object.delete()
		new_obj.name = obj_name

		# TODO: move new obj into new arm

		return {"FINISHED"}