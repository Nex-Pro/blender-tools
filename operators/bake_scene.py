import bpy
import threading

from .. import utils
from ..functions.denoise import *

class BakeScene(bpy.types.Operator):
	bl_idname = "tivoli.bake_scene"
	bl_label = "Tivoli: Bake Scene"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		scene = context.scene
		objects = scene.objects

		def getLightmapNode(material):
			for node in material.node_tree.nodes:
				if node.name.startswith("Tivoli_Lightmap"):
					return node

		def unlinkDiffuse(objects):
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

		def relinkDiffuse(old):
			for color in old["colors"]:
				color["color"][0] = color["r"]
				color["color"][1] = color["g"]
				color["color"][2] = color["b"]
				color["color"][3] = color["a"]

			for link in old["links"]:
				link["links"].new(link["from"], link["to"])

		bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

		render = {
		    "objects_to_bake":
		        [obj for obj in objects if utils.isObjBakeable(obj)],
		    "current_object_index": 0
		}

		def bakeNextObj(self, render):

			objects_to_bake = render["objects_to_bake"]
			current_object_index = render["current_object_index"]
			scene = context.scene

			if current_object_index > len(objects_to_bake) - 1:
				return False

			obj = objects_to_bake[current_object_index]
			scene.tivoli_settings.bake_current = obj.name

			print("\nBaking: " + obj.name + "...")

			# select obj
			utils.deselectAll()
			obj.select_set(state=True)
			context.view_layer.objects.active = obj

			# select texture
			for material_slot in obj.material_slots:
				material = material_slot.material
				node = getLightmapNode(material)

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
			)

			# denoise
			image = getLightmapNode(obj.material_slots[0].material).image
			denoise(image)

			# update current index and text
			render["current_object_index"] += 1
			progress = render["current_object_index"
			                 ] / len(objects_to_bake) * 100
			print(
			    "Baked " + str(render["current_object_index"]) + "/" +
			    str(len(objects_to_bake)) + ", " + "{:.2f}".format(progress) +
			    "%"
			)
			scene.tivoli_settings.bake_progress = progress

			return True

		# TODO: dont bake if materials not prepared

		# necessary for diffuse light map
		links = unlinkDiffuse(render["objects_to_bake"])

		print("Starting bake...")

		# TODO: fix ui lock
		while (bakeNextObj(self, render) == True):
			dont_do_anything = None

		relinkDiffuse(links)

		scene.tivoli_settings.bake_current = ""
		scene.tivoli_settings.bake_progress = -1

		utils.deselectAll()

		return {"FINISHED"}
