import re

from .tivoli_settings_node import *

def color_to_array(color):
	return [color[0], color[1], color[2]]

def make_material_map(objects):
	material_map = {}
	images_to_save = []

	for obj in objects:
		material_slots = obj.material_slots.values()
		for material_slot in material_slots:
			material = material_slot.material
			material_map_key = "mat::" + material.name

			# skip if already exists
			if material_map_key in material_map:
				continue

			# get principled shader
			nodes = material.node_tree.nodes

			bsdf = None
			for node in nodes:
				if node.type == "BSDF_PRINCIPLED":
					bsdf = node
					break
			if bsdf == None:
				continue

			tivoli = None
			for node in nodes:
				if node.type == "GROUP":
					if node.node_tree == get_tivoli_settings_node():
						tivoli = node
						break

			# get tivoli shader
			nodes = material.node_tree.nodes
			bsdf = None
			for node in nodes:
				if node.type == "BSDF_PRINCIPLED":
					bsdf = node
					break
			if bsdf == None:
				continue

			# write material data
			material_data = {
			    # "name": material.name,
			}

			def process_color(
			    input_key, output_key, map_only=False, use_tivoli=False
			):
				if tivoli and use_tivoli:
					node_input = tivoli.inputs[input_key]
				else:
					node_input = bsdf.inputs[input_key]

				if len(node_input.links) > 0:
					node = node_input.links[0].from_node

					if node.type == "TEX_IMAGE":
						filepath = node.image.filepath
						filename = re.split("[\\/\\\]", filepath).pop()
						material_data[output_key + "Map"] = filename

						if tivoli and use_tivoli:
							images_to_save.append(node.image)

					elif node.type == "NORMAL_MAP":
						normal_input = node.inputs["Color"]
						if len(normal_input.links) > 0:
							node = normal_input.links[0].from_node
							if node.type == "TEX_IMAGE":
								filepath = node.image.filepath
								filename = re.split("[\\/\\\]", filepath).pop()
								material_data[output_key + "Map"] = filename

								if tivoli and use_tivoli:
									images_to_save.append(node.image)

				elif map_only == False:
					material_data[output_key] = color_to_array(
					    node_input.default_value
					)

			def process_value(
			    input_key, output_key, map_only=False, use_tivoli=False
			):
				if tivoli and use_tivoli:
					node_input = tivoli.inputs[input_key]
				else:
					node_input = bsdf.inputs[input_key]

				if (len(node_input.links) > 0):
					node = node_input.links[0].from_node
					if node.type == "TEX_IMAGE":
						filepath = node.image.filepath
						filename = re.split("[\\/\\\]", filepath).pop()
						material_data[output_key + "Map"] = filename

						if tivoli and use_tivoli:
							images_to_save.append(node.image)

				elif map_only == False:
					material_data[output_key] = node_input.default_value

			# https://apidocs.tivolicloud.com/Graphics.html#.Material

			if tivoli and tivoli.inputs["Unlit"].default_value:
				process_color("Base Color", "albedo")
				material_data["unlit"] = True

			else:
				process_color("Base Color", "albedo")
				process_value("Alpha", "opacity")
				process_value("Roughness", "roughness")
				process_value("Metallic", "metallic")
				process_color("Normal", "normal", True)
				process_value("Subsurface", "scattering")
				process_color("Emission", "emissive")

				if tivoli:
					process_value("Occlusion", "occlusion", True, True)
					# process_value("Lightmap", "light", True, True)

				if material.blend_method == "OPAQUE":
					material_data["opacityMapMode"] = "OPACITY_MAP_OPAQUE"
				elif material.blend_method == "CLIP":
					material_data["opacityMapMode"] = "OPACITY_MAP_MASK"
					material_data["opacityCutoff"] = material.alpha_threshold
				elif material.blend_method == "HASHED" or material.blend_method == "BLEND":
					material_data["opacityMapMode"] = "OPACITY_MAP_BLEND"

				if material.use_backface_culling:
					material_data["cullFaceMode"] = "CULL_BACK"
				else:
					material_data["cullFaceMode"] = "CULL_NONE"

			# add to map
			material_map[material_map_key] = {"materials": material_data}

	return {"material_map": material_map, "images_to_save": images_to_save}
