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

	base_url: bpy.props.StringProperty(
	    name="Base URL", default="", options={"HIDDEN"}
	)

	webp_textures: bpy.props.BoolProperty(
	    name="WebP textures", default=False, options={"HIDDEN"}
	)

	as_json: bpy.props.BoolProperty(
	    name="Export as JSON", default=False, options={"HIDDEN"}
	)

	def execute(self, context):
		scene = context.scene

		# TODO: add 32 bit support to tivoli
		# LIGHTMAP_EXT = ".exr"  # for saving
		# LIGHTMAP_TYPE = "OPEN_EXR"  # for blender
		# LIGHTMAP_MIMETYPE = "image/exr"  # for gltf
		LIGHTMAP_EXT = ".png"  # for saving
		LIGHTMAP_TYPE = "PNG"  # for blender
		LIGHTMAP_MIMETYPE = "image/png"  # for gltf

		# export gltf
		project_name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
		project_dir = os.path.dirname(bpy.data.filepath)
		export_dir = os.path.join(project_dir, project_name)

		if self.as_json:
			bpy.ops.tivoli.export_scene(
			    webp_textures=self.webp_textures,
			    base_url=self.base_url,
			)
		else:
			if os.path.exists(export_dir):
				shutil.rmtree(export_dir)
			os.makedirs(export_dir)

			filepath = os.path.join(export_dir, project_name) + ".gltf"

			bpy.ops.object.select_all(action="SELECT")

			bpy.ops.export_scene.gltf(
			    export_format="GLTF_SEPARATE",
			    export_copyright="Tivoli Cloud VR, Inc.",
			    # export_image_format="JPEG",
			    use_selection=True,
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

			if self.webp_textures:
				# dont convert image
				image.filepath_raw = export_path + "." + utils.image_ext(image)
				image.save()
			else:
				image.filepath_raw = export_path + LIGHTMAP_EXT
				image.file_format = LIGHTMAP_TYPE
				image.save()

			# restore image
			image.filepath_raw = previous_filepath_raw
			image.file_format = previous_file_format

		# modify gltf
		def modify_gltf(filepath):
			if self.webp_textures:
				gltf_webp_optimizer(filepath)

			file = open(filepath, "r")
			data = json.load(file)
			file.close()

			def add_texture(image):
				if "images" not in data:
					data["images"] = []
				if "textures" not in data:
					data["textures"] = []

				if self.webp_textures:
					data["images"].append(
					    {
					        "mimeType": "",  # will be written by optimizer
					        "name": image.name,
					        "uri": image.name + "." + utils.image_ext(image),
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

			if "materials" not in data:
				return

			for material in data["materials"]:
				obj = utils.find_object_from_material_name(material["name"])

				image_name = "Tivoli_Lightmap_" + obj.name
				image = utils.find_image(image_name)
				texture_index = add_texture(image)

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

			if self.webp_textures:
				gltf_webp_optimizer(filepath, lossless=True)

		if self.as_json:
			for filename in os.listdir(export_dir):
				ext = filename.split(".").pop().lower()
				if ext == "gltf":
					filepath = os.path.join(export_dir, filename)
					modify_gltf(filepath)
		else:
			modify_gltf(filepath)

		utils.deselect_all()

		return {"FINISHED"}
