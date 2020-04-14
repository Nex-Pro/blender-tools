import bpy

from .. import utils

class BakeScene(bpy.types.Operator):
	bl_idname = "tivoli.bake_scene"
	bl_label = "Tivoli: Bake Scene"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		scene = context.scene
		objects = scene.objects

		def getTextureNode(material):
			for node in material.node_tree.nodes:
				if node.name.startswith("Tivoli_Lightmap"):
					return node

		def unlinkDiffuse(material_slots):
			old_links = []

			for material_slot in material_slots:
				material = material_slot.material
				nodes = material.node_tree.nodes
				links = material.node_tree.links

				bsdf = nodes["Principled BSDF"]

				for link in links:
					if (
					    link.to_node != bsdf or
					    link.to_socket.name != "Base Color"
					):
						continue

					color = bsdf.inputs["Base Color"].default_value

					old_links.append(
					    {
					        "links": links,
					        "from": link.from_socket,
					        "to": link.to_socket,
					        "color": color,
					        # TODO: do this better
					        "color_r": color[0],
					        "color_g": color[1],
					        "color_b": color[2],
					        "color_a": color[3],
					    }
					)

					links.remove(link)

				bsdf.inputs["Base Color"].default_value = (1, 1, 1, 1)

			return old_links

		def relinkDiffuse(old_links):
			for old_link in old_links:
				old_link["links"].new(old_link["from"], old_link["to"])
				old_link["color"][0] = old_link["color_r"]
				old_link["color"][1] = old_link["color_g"]
				old_link["color"][2] = old_link["color_b"]
				old_link["color"][3] = old_link["color_a"]

		bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

		for obj in objects:
			if not utils.isObjBakeable(obj):
				continue

			print("Baking: " + obj.name)

			# select obj
			utils.deselectAll()
			obj.select_set(state=True)
			context.view_layer.objects.active = obj

			# necessary for diffuse light map
			# TODO: this must happen for all objects before bake
			links = unlinkDiffuse(obj.material_slots)

			# select texture node
			first_material = obj.material_slots[0].material
			node = getTextureNode(first_material)
			first_material.node_tree.nodes.active = node

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

			relinkDiffuse(links)

		utils.deselectAll()

		return {"FINISHED"}
