import bpy
import math

class AvatarFixBoneRotations(bpy.types.Operator):
	bl_idname = "tivoli.avatar_fix_bone_rotations"
	bl_label = "Tivoli: Fix bone rotations"
	bl_options = {"REGISTER", "UNDO", "INTERNAL"}

	def execute(self, context):
		last_view = bpy.context.area.type
		bpy.context.area.type = "VIEW_3D"

		if (
		    not bpy.context.active_object or
		    bpy.context.active_object.type != "ARMATURE"
		):
			raise Exception("Please select a skeleton")

		last_mode = bpy.context.object.mode
		bpy.ops.object.mode_set(mode="EDIT")

		# set all roll to 0
		bpy.ops.armature.select_all(action="SELECT")
		bpy.ops.armature.roll_clear(roll=0)

		# right   left
		#  -90  0  +90
		# -180  0  +180

		bottom = ["UpLeg", "Leg", "Foot", "ToeBase", "Toe_End"]
		bottom_right = list(map(lambda bone: "Right" + bone, bottom))
		bottom_left = list(map(lambda bone: "Left" + bone, bottom))

		top = [
		    "Shoulder", "Arm", "ForeArm", "Hand", "HandThumb1", "HandThumb2",
		    "HandThumb3", "HandThumb4", "HandIndex1", "HandIndex2",
		    "HandIndex3", "HandIndex4", "HandMiddle1", "HandMiddle2",
		    "HandMiddle3", "HandMiddle4", "HandRing1", "HandRing2", "HandRing3",
		    "HandRing4", "HandPinky1", "HandPinky2", "HandPinky3", "HandPinky4"
		]
		top_right = list(map(lambda bone: "Right" + bone, top))
		top_left = list(map(lambda bone: "Left" + bone, top))

		armature = bpy.context.active_object.data

		def clear_bones_roll(bone_list, roll):
			bpy.ops.armature.select_all(action="DESELECT")
			for bone_name in bone_list:
				bone = armature.edit_bones.get(bone_name)
				if bone != None:
					bone.select = bone.select_head = bone.select_tail = True
			bpy.ops.armature.roll_clear(roll=roll)

		clear_bones_roll(bottom_right, -math.pi)  # -180
		clear_bones_roll(bottom_left, +math.pi)  # +180
		clear_bones_roll(top_right, -math.pi / 2)  # -90
		clear_bones_roll(top_left, +math.pi / 2)  # +90

		# deselect and restore view
		bpy.ops.armature.select_all(action="DESELECT")
		bpy.ops.object.mode_set(mode=last_mode)
		bpy.context.area.type = last_view

		return {"FINISHED"}