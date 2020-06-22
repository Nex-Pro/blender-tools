import bpy
import os

from ... import utils
from ...functions.denoise import *

class LightmapBakeScene(bpy.types.Operator):
	bl_idname = "tivoli.lightmap_bake_scene"
	bl_label = "Tivoli: Lightmap Bake Scene"
	bl_options = {"REGISTER", "UNDO", "INTERNAL"}

	tmp_dir = None

	objects_to_bake = []
	current_object_index = 0

	def get_lightmap_node(self, material):
		for node in material.node_tree.nodes:
			if node.name.startswith("Tivoli_Lightmap"):
				return node

	def can_bake(self):
		if self.current_object_index > len(self.objects_to_bake) - 1:
			return False
		return True

	def update_bake_progress(self, context):
		tivoli_settings = context.scene.tivoli_settings

		progress = self.current_object_index / len(self.objects_to_bake) * 100
		print(
		    "Baked " + str(self.current_object_index) + "/" +
		    str(len(self.objects_to_bake)) + ", " + "{:.2f}".format(progress) +
		    "%"
		)
		tivoli_settings.bake_progress = progress

		if self.can_bake():
			obj = self.objects_to_bake[self.current_object_index]
			tivoli_settings.bake_current = obj.name

			for material_slot in obj.material_slots:
				material = material_slot.material
				node = self.get_lightmap_node(material)

				tivoli_settings.bake_current_texture_size = (
				    str(node.image.size[0]) + " x " + str(node.image.size[1])
				)
				break
		else:
			tivoli_settings.bake_current = ""
			tivoli_settings.bake_current_texture_size = ""
			tivoli_settings.bake_progress = -1

	def bake_next_obj(self, context):
		scene = context.scene

		if self.can_bake() == False:
			return False

		obj = self.objects_to_bake[self.current_object_index]

		print("\nBaking: " + obj.name + "...")

		# select obj
		utils.deselect_all()
		obj.select_set(state=True)
		context.view_layer.objects.active = obj

		# select texture
		for material_slot in obj.material_slots:
			material = material_slot.material
			node = self.get_lightmap_node(material)

			for node in material.node_tree.nodes:
				node.select = False

			material.node_tree.nodes.active = node
			node.select = True

		obj.active_material_index = 0

		image = self.get_lightmap_node(obj.material_slots[0].material).image
		image.file_format = "HDR"
		image.filepath_raw = os.path.join(
		    self.tmp_dir,
		    image.name,
		) + "." + utils.image_ext(image)

		# https://docs.blender.org/api/current/bpy.ops.object.html#bpy.ops.object.bake
		bpy.ops.object.bake(
		    type="COMBINED",
		    # pass_filter={"EMIT","DIRECT","INDIRECT"},
		    filepath=image.filepath_raw,
		    margin=8192,
		    # save_mode="EXTERNAL",
		    save_mode="INTERNAL",
		    uv_layer="Tivoli_Lightmap",
		)

		# denoise
		if scene.tivoli_settings.bake_oidn:
			denoise(image)

		# currently saving internally then manually saving externally
		# https://developer.blender.org/D4162
		image.save()

		# update current index and text
		self.current_object_index += 1

		return True

	def unlink_diffuse(self, objects):
		old = {"colors": [], "links": []}

		for obj in objects:
			for material_slot in obj.material_slots:
				material = material_slot.material
				nodes = material.node_tree.nodes
				links = material.node_tree.links

				bsdf = None
				for node in nodes:
					if node.type == "BSDF_PRINCIPLED":
						bsdf = node
						break
				if bsdf == None:
					raise Exception(
					    "Can't find Principled BSDF in " + material.name
					)

				base_color = bsdf.inputs["Base Color"]

				# save color and set to white
				color = base_color.default_value
				old["colors"].append(
				    {
				        "color": color,
				        # TODO: do this better
				        "r": color[0],
				        "g": color[1],
				        "b": color[2],
				        "a": color[3],
				    }
				)
				base_color.default_value = (1, 1, 1, 1)

				# save link and unlink
				if len(base_color.links) > 0:
					link = base_color.links[0]  # can only be one link
					old["links"].append(
					    {
					        "links": links,
					        "from": link.from_socket,
					        "to": link.to_socket
					    }
					)
					links.remove(link)

		return old

	def relink_diffuse(self, old):
		for color in old["colors"]:
			color["color"][0] = color["r"]
			color["color"][1] = color["g"]
			color["color"][2] = color["b"]
			color["color"][3] = color["a"]

		for link in old["links"]:
			link["links"].new(link["from"], link["to"])

	def execute(self, context):
		if not bpy.data.is_saved:
			raise Exception("Save first before exporting")

		scene = context.scene

		scene.render.engine = "CYCLES"
		scene.render.tile_x = 8192
		scene.render.tile_y = 8192
		scene.cycles.device = "GPU"
		if scene.cycles.samples > 32:
			raise Exception("Samples should be less than 32")

		self.tmp_dir = os.path.join(os.path.dirname(bpy.data.filepath), "tmp")
		if not os.path.exists(self.tmp_dir):
			os.makedirs(self.tmp_dir)

		bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

		# TODO: dont bake if materials not prepared

		self.objects_to_bake = []
		self.current_object_index = 0

		for obj in scene.objects:
			if utils.is_obj_bakeable(obj):
				self.objects_to_bake.append(obj)

		# necessary for diffuse light map
		self.links = self.unlink_diffuse(self.objects_to_bake)

		print("Starting bake...")

		self.update_bake_progress(context)

		self.timer = context.window_manager.event_timer_add(
		    0.01, window=context.window
		)
		context.window_manager.modal_handler_add(self)

		return {"RUNNING_MODAL"}

		# rest of the code down below

	timer = None
	links = None

	def modal(self, context, event):
		if event.type == "TIMER":
			if self.bake_next_obj(context):
				self.update_bake_progress(context)
				return {"PASS_THROUGH"}

			self.relink_diffuse(self.links)

			utils.deselect_all()

			context.window_manager.event_timer_remove(self.timer)
			return {"FINISHED"}

		return {"PASS_THROUGH"}