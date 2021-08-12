import bpy
import tempfile
import os

from ... import utils

class AnimationBakePhysicsWithMdd(bpy.types.Operator):
	bl_idname = "tivoli.animation_bake_physics_with_mdd"
	bl_label = "Tivoli: Bake physics with MDD"
	bl_options = {"REGISTER", "UNDO", "INTERNAL"}

	@classmethod
	def poll(self, context):
		return (
		    len(bpy.context.selected_objects) != 0 and
		    bpy.context.active_object.type == "MESH"
		)

	def execute(self, context):
		bpy.context.area.type = "VIEW_3D"

		if (not utils.addon_installed("io_shape_mdd")):
			raise Exception("\"NewTek MDD format\" addon not enabled")

		obj = bpy.context.active_object

		bpy.ops.object.transform_apply(scale=True, rotation=True)

		filepath = tempfile.mktemp(suffix=".mdd")

		bpy.ops.export_shape.mdd(
		    filepath=filepath,
		    fps=bpy.context.scene.render.fps,
		    frame_start=bpy.context.scene.frame_start,
		    frame_end=bpy.context.scene.frame_end
		)

		bpy.ops.import_shape.mdd(filepath=filepath)

		if os.path.exists(filepath):
			os.remove(filepath)

		physics_modifiers = [
		    "CLOTH",
		    "COLLISION",
		    "SOFT_BODY",
		    "DYNAMIC_PAINT",
		    "FLUID",
		]

		for modifier_name in obj.modifiers.keys():
			if (obj.modifiers[modifier_name].type in physics_modifiers):
				bpy.ops.object.modifier_remove(modifier=modifier_name)

		# TODO: cant tell if its on or off
		# try:
		# 	bpy.ops.object.forcefield_toggle()
		# except:
		# 	pass

		try:
			bpy.ops.rigidbody.object_remove()
		except:
			pass

		try:
			bpy.ops.rigidbody.constraint_remove()
		except:
			pass

		# TODO: restore scale and rotation?

		return {"FINISHED"}