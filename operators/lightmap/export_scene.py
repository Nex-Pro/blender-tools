import bpy
import os
import shutil
import json

from ... import utils
from ...functions.gltf_webp_optimizer import *

class LightmapExportScene(bpy.types.Operator):
	bl_idname = "tivoli.lightmap_export_scene"
	bl_label = "Tivoli: Lightmap Export Scene"
	bl_options = {"REGISTER", "UNDO", "INTERNAL"}

	def execute(self, context):
		scene = context.scene

		# TODO: add 32 bit support to tivoli
		# LIGHTMAP_EXT = ".exr"  # for saving
		# LIGHTMAP_TYPE = "OPEN_EXR"  # for blender
		# LIGHTMAP_MIMETYPE = "image/exr"  # for gltf

		LIGHTMAP_EXT = ".jpg"  # for saving
		LIGHTMAP_TYPE = "JPEG"  # for blender
		LIGHTMAP_MIMETYPE = "image/jpeg"  # for gltf

		# export gltf
		project_name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
		project_dir = os.path.dirname(bpy.data.filepath)
		export_dir = os.path.join(project_dir, project_name)

		if os.path.exists(export_dir):
			shutil.rmtree(export_dir)
		os.makedirs(export_dir)

		filepath = os.path.join(export_dir, project_name) + ".gltf"

		bpy.ops.object.select_all(action="SELECT")

		bpy.ops.export_scene.gltf(
		    export_format="GLTF_SEPARATE",
		    export_copyright="Tivoli Cloud VR, Inc.",
		    export_image_format="JPEG",
		    export_selected=True,
		    export_apply=True,
		    filepath=filepath,
		)

		# export lightmap images
		for image in bpy.data.images:
			if image.name.startswith("Tivoli_Lightmap_") == False:
				continue

			previous_filepath_raw = image.filepath_raw
			previous_file_format = image.file_format

			export_path = os.path.join(export_dir, image.name)

			if scene.tivoli_settings.bake_webp:
				# dont convert image
				image.filepath_raw = export_path + "." + utils.imageExt(image)
				image.save()
			else:
				image.filepath_raw = export_path + LIGHTMAP_EXT
				image.file_format = LIGHTMAP_TYPE
				image.save()

			# restore image
			image.filepath_raw = previous_filepath_raw
			image.file_format = previous_file_format

		# modify gltf
		file = open(filepath, "r")
		data = json.load(file)
		file.close()

		def addTexture(image):
			if "images" not in data:
				data["images"] = []
			if "textures" not in data:
				data["textures"] = []

			if scene.tivoli_settings.bake_webp:
				data["images"].append(
				    {
				        "mimeType": "",  # will be written by optimizer
				        "name": image.name,
				        "uri": image.name + "." + utils.imageExt(image),
				    }
				)
			else:
				data["images"].append(
				    {
				        "mimeType": LIGHTMAP_MIMETYPE,
				        "name": image.name,
				        "uri": image.name + LIGHTMAP_EXT,
				    }
				)

			source = len(data["images"]) - 1

			data["textures"].append({"source": source})
			index = len(data["textures"]) - 1

			return index

		for material in data["materials"]:
			obj = utils.findObjectFromMaterialName(material["name"])

			image_name = "Tivoli_Lightmap_" + obj.name
			image = utils.findImage(image_name)
			texture_index = addTexture(image)

			print(image_name)
			print(texture_index)

			material["lightmapTexture"] = {
			    "index": texture_index,
			    "texCoord": 1,
			}

		# export gltf
		file = open(filepath, "w")
		json.dump(data, file, indent=4)
		file.close()

		if scene.tivoli_settings.bake_webp:
			gltf_webp_optimizer(filepath, quality=90)

		utils.deselectAll()

		return {"FINISHED"}
