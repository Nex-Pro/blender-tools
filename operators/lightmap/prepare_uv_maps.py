import bpy

from ... import utils

class LightmapPrepareUVMaps(bpy.types.Operator):
	bl_idname = "tivoli.lightmap_prepare_uv_maps"
	bl_label = "Tivoli: Lightmap Prepare UV maps"
	bl_options = {"REGISTER", "UNDO", "INTERNAL"}

	def execute(self, context):
		scene = context.scene
		objects = scene.objects

		UV_NAME = "Tivoli_Lightmap"

		bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

		for obj in objects:
			if not utils.is_obj_bakeable(obj):
				continue

			print("Preparing UV map for: " + obj.name)

			uv_layers = obj.data.uv_layers
			pre_active_index = uv_layers.active_index

			# delete uv map
			if UV_NAME in uv_layers:
				uv_layers.remove(uv_layers[UV_NAME])

			# create uv
			uv_layers.new(name=UV_NAME, do_init=False)

			# move uv layer to second slot
			def move_to_bottom(index):
				uv_layers.active_index = index
				uv_name = uv_layers.active.name

				new_uv = uv_layers.new(do_init=True)
				if new_uv == None:
					return
				new_uv_name = new_uv.name

				# delete old uv map
				uv_layers.remove(uv_layers[index])
				# rename new map now at the bottom
				uv_layers[new_uv_name].name = uv_name

			if len(uv_layers) != 2:
				for i in range(1, len(uv_layers) - 1):
					move_to_bottom(1)

			# unwrap
			uv_layers[UV_NAME].active = True
			utils.select_only(obj)

			try:
				# bpy.ops.uv.lightmap_pack(PREF_CONTEXT="ALL_FACES")
				# bpy.ops.uv.smart_project(angle_limit=33, island_margin=0.03)
				bpy.ops.uv.smart_project()
			except:
				print("Can't generate UV map for:" + obj.name)

			# cleanup
			if pre_active_index != -1:
				uv_layers.active_index = pre_active_index

		utils.deselect_all()

		return {"FINISHED"}
