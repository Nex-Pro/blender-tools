import bpy

from .. import utils

class BakePrepareUVMaps(bpy.types.Operator):
	bl_idname = "tivoli.prepare_uv_maps"
	bl_label = "Tivoli: Prepare UV maps"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		scene = context.scene
		objects = scene.objects

		UV_NAME = "Tivoli_Lightmap"

		bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

		for obj in objects:
			if not utils.isObjBakeable(obj):
				continue

			print("Preparing UV map for: " + obj.name)

			uv_layers = obj.data.uv_layers
			pre_active_index = uv_layers.active_index

			# delete uv map
			if UV_NAME in uv_layers:
				uv_layers.remove(uv_layers[UV_NAME])

			# create uv
			uv_layers.new(name=UV_NAME, do_init=True)
			uv_layers[UV_NAME].active = True

			# TODO: move uv layer to second slot

			utils.selectOnly(obj)

			try:
				# bpy.ops.uv.lightmap_pack(PREF_CONTEXT="ALL_FACES")
				bpy.ops.uv.smart_project()
			except:
				print("Can't generate UV map for:" + obj.name)

			# cleanup
			if pre_active_index != -1:
				uv_layers.active_index = pre_active_index

		utils.deselectAll()

		return {"FINISHED"}
