import re

from typing import Union

from .tivoli_settings_node import *
from .. import utils

def color_to_array(color):
	return [color[0], color[1], color[2]]

def make_material_map(objects, to_webp=False):
	material_map = {}
	images_to_save = []
	images_to_convert = []

	for obj in objects:
		material_slots = obj.material_slots.values()
		for material_slot in material_slots:
			material = material_slot.material
			material_map_key = "mat::" + material.name

			# skip if already exists
			if material_map_key in material_map:
				continue

			# get principled shader and tivoli settings node
			nodes = material.node_tree.nodes

			material_output = None
			for node in nodes:
				if node.type == "OUTPUT_MATERIAL":
					material_output = node
			if material_output == None:
				continue

			bsdf = None
			if (len(material_output.inputs["Surface"].links) > 0):
				bsdf = material_output.inputs["Surface"].links[0].from_node
			if bsdf == None or bsdf.type != "BSDF_PRINCIPLED":
				continue

			tivoli = None
			for node in nodes:
				if node.type == "GROUP":
					if node.node_tree == get_tivoli_settings_node():
						tivoli = node
						break

			# write material data
			material_data = {
			    # "name": material.name,
			}

			def process(
			    input_type: Union["value", "color"],
			    input_key,
			    output_key,
			    map_only=False,
			    use_tivoli=False
			):
				if tivoli and use_tivoli:
					node_input = tivoli.inputs[input_key]
				else:
					node_input = bsdf.inputs[input_key]

				def set_image(image):
					filepath = image.filepath
					filename = re.split("[\\/\\\]", filepath).pop()

					if to_webp:
						old_filename = filename
						filename = utils.replace_filename_ext(filename, ".webp")
						images_to_convert.append([old_filename, filename])

					material_data[output_key + "Map"] = filename

					if tivoli and use_tivoli:
						images_to_save.append(image)

				if len(node_input.links) > 0:
					node = node_input.links[0].from_node

					if node.type == "TEX_IMAGE":
						set_image(node.image)

					elif node.type == "NORMAL_MAP":
						normal_input = node.inputs["Color"]
						if len(normal_input.links) > 0:
							node = normal_input.links[0].from_node
							if node.type == "TEX_IMAGE":
								set_image(node.image)

				elif map_only == False:
					if input_type == "value":
						material_data[output_key] = node_input.default_value
					else:
						material_data[output_key] = color_to_array(
						    node_input.default_value
						)

			# https://apidocs.tivolicloud.com/Graphics.html#.Material

			if tivoli and tivoli.inputs["Unlit"].default_value:
				# export emissive as unlit color
				process("color", "Emission", "albedo")
				material_data["unlit"] = True

			else:
				process("color", "Base Color", "albedo")
				process("value", "Alpha", "opacity")
				process("value", "Roughness", "roughness")
				process("value", "Metallic", "metallic")
				process("color", "Normal", "normal", True)
				process("value", "Subsurface", "scattering")
				process("color", "Emission", "emissive")

				if tivoli:
					process("value", "Occlusion", "occlusion", True, True)
					# process("value", "Lightmap", "light", True, True)

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

	return {
	    "material_map": material_map,
	    "images_to_save": images_to_save,
	    "images_to_convert": images_to_convert
	}
