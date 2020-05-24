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

	def getLightmapNode(self, material):
		for node in material.node_tree.nodes:
			if node.name.startswith("Tivoli_Lightmap"):
				return node

	def canBake(self):
		if self.current_object_index > len(self.objects_to_bake) - 1:
			return False
		return True

	def updateBakeProgress(self, context):
		tivoli_settings = context.scene.tivoli_settings

		progress = self.current_object_index / len(self.objects_to_bake) * 100
		print(
		    "Baked " + str(self.current_object_index) + "/" +
		    str(len(self.objects_to_bake)) + ", " + "{:.2f}".format(progress) +
		    "%"
		)
		tivoli_settings.bake_progress = progress

		if self.canBake():
			obj = self.objects_to_bake[self.current_object_index]
			tivoli_settings.bake_current = obj.name

			for material_slot in obj.material_slots:
				material = material_slot.material
				node = self.getLightmapNode(material)

				tivoli_settings.bake_current_texture_size = (
				    str(node.image.size[0]) + " x " + str(node.image.size[1])
				)
				break
		else:
			tivoli_settings.bake_current = ""
			tivoli_settings.bake_current_texture_size = ""
			tivoli_settings.bake_progress = -1

	def bakeNextObj(self, context):
		scene = context.scene

		if self.canBake() == False:
			return False

		obj = self.objects_to_bake[self.current_object_index]

		print("\nBaking: " + obj.name + "...")

		# select obj
		utils.deselectAll()
		obj.select_set(state=True)
		context.view_layer.objects.active = obj

		# select texture
		for material_slot in obj.material_slots:
			material = material_slot.material
			node = self.getLightmapNode(material)

			for node in material.node_tree.nodes:
				node.select = False

			material.node_tree.nodes.active = node
			node.select = True

		obj.active_material_index = 0

		# https://docs.blender.org/api/current/bpy.ops.object.html#bpy.ops.object.bake
		bpy.ops.object.bake(
		    type="COMBINED",
		    # pass_filter={"EMIT","DIRECT","INDIRECT"},
		    uv_layer="Tivoli_Lightmap",
		    # filepath=os.path.join(basedir, obj.name+".png"),
		    # width=128,
		    # height=128,
		    # margin=2,
		    # save_mode="EXTERNAL",
		    margin=8192
		)

		# save image otherwise it all gets allocated in the memory
		image = self.getLightmapNode(obj.material_slots[0].material).image

		# denoise
		if scene.tivoli_settings.bake_oidn:
			denoise(image)

		image.filepath_raw = os.path.join(self.tmp_dir, image.name) + ".hdr"
		image.file_format = "HDR"
		image.save()

		# update current index and text
		self.current_object_index += 1

		return True

	def unlinkDiffuse(self, objects):
		old = {"colors": [], "links": []}

		for obj in objects:
			for material_slot in obj.material_slots:
				material = material_slot.material
				nodes = material.node_tree.nodes
				links = material.node_tree.links

				bsdf = nodes["Principled BSDF"]
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

	def relinkDiffuse(self, old):
		for color in old["colors"]:
			color["color"][0] = color["r"]
			color["color"][1] = color["g"]
			color["color"][2] = color["b"]
			color["color"][3] = color["a"]

		for link in old["links"]:
			link["links"].new(link["from"], link["to"])

	def execute(self, context):
		scene = context.scene
		objects = scene.objects

		self.tmp_dir = os.path.join(os.path.dirname(bpy.data.filepath), "tmp")
		if not os.path.exists(self.tmp_dir):
			os.makedirs(self.tmp_dir)

		bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

		# TODO: dont bake if materials not prepared

		self.objects_to_bake = [
		    obj for obj in objects if utils.isObjBakeable(obj)
		]
		self.current_object_index = 0

		# necessary for diffuse light map
		self.links = self.unlinkDiffuse(self.objects_to_bake)

		print("Starting bake...")

		self.updateBakeProgress(context)

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
			if self.bakeNextObj(context):
				self.updateBakeProgress(context)
				return {"PASS_THROUGH"}

			self.relinkDiffuse(self.links)

			utils.deselectAll()

			context.window_manager.event_timer_remove(self.timer)
			return {"FINISHED"}

		return {"PASS_THROUGH"}