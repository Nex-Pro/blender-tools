import bpy
import os
import shutil
import json
import subprocess

from bpy_extras.io_utils import ExportHelper

from ... import utils
from ...functions.make_material_map import *

class AvatarExportAvatar(bpy.types.Operator, ExportHelper):
	bl_idname = "tivoli.avatar_export_avatar"
	bl_label = "Export Tivoli avatar"
	bl_options = {"REGISTER", "UNDO", "INTERNAL"}

	filename_ext = ".fst"
	filter_glob: bpy.props.StringProperty(default="*.fst", options={"HIDDEN"})

	webp_textures: bpy.props.BoolProperty(
	    default=True,
	    name="WebP texture optimize",
	    description="Convert all textures to WebP"
	)

	# make_folder: bpy.props.BoolProperty(
	#	 default=True,
	#	 name="Make folder for avatar",
	#	 description="Puts everything in a folder instead of the chosen directory"
	# )

	def draw(self, context):
		layout = self.layout
		layout.prop(self, "webp_textures")
		# layout.prop(self, "make_folder")

	def execute(self, context):
		if not self.filepath:
			raise Exception("Filepath not set")

		scene = context.scene

		# active = bpy.context.view_layer.objects.active
		# print(active)
		# check if selecting armature
		# return {"FINISHED"}

		avatar_name = utils.replace_filename_ext(
		    os.path.basename(self.filepath), ""
		)

		# if not os.path.isfile(self.filepath) and self.make_folder:
		if not os.path.isfile(self.filepath):
			folder = os.path.join(os.path.dirname(self.filepath), avatar_name)
			if not os.path.exists(folder):
				os.mkdir(folder)

			self.filepath = os.path.join(
			    folder, os.path.basename(self.filepath)
			)

		fst_filepath = self.filepath
		fbx_filepath = utils.replace_filename_ext(self.filepath, ".fbx")
		export_path = os.path.dirname(self.filepath)
		fbm_path = os.path.join(export_path, avatar_name + ".fbm")

		# select all active from first armature
		utils.deselect_all()

		objects = []
		armature = None

		for obj in scene.objects:
			if obj.visible_get() and obj.type == "ARMATURE":
				obj.select_set(state=True)
				objects.append(obj)
				armature = obj
				break

		if armature == None:
			raise Exception("Armature not found")

		for obj in scene.objects:
			if (
			    obj.visible_get() and obj.type == "MESH" and
			    utils.is_in_parent_tree(obj, armature)
			):
				obj.select_set(state=True)
				objects.append(obj)

		bpy.ops.tivoli.avatar_force_tpose(clear=False)

		bpy.ops.export_scene.fbx(
		    filepath=fbx_filepath,
		    use_selection=True,
		    object_types={"ARMATURE", "MESH"},
		    use_mesh_modifiers=True,
		    path_mode="COPY",
		    embed_textures=False,
		)

		utils.deselect_all()

		# move all from .fbm into export folder
		if os.path.isdir(fbm_path):
			files = os.listdir(fbm_path)
			for filename in files:
				shutil.move(
				    os.path.join(fbm_path, filename),
				    os.path.join(export_path, filename)
				)
			shutil.rmtree(fbm_path)

		# make material map
		make_material_map_output = make_material_map(
		    objects, self.webp_textures
		)
		material_map = make_material_map_output["material_map"]
		images_to_save = make_material_map_output["images_to_save"]
		images_to_convert = make_material_map_output["images_to_convert"]

		# save images from custom tivoli settings node
		for image in images_to_save:
			tmp_image = image.copy()
			tmp_image.update()
			tmp_image.filepath_raw = os.path.join(
			    export_path, os.path.basename(image.filepath_raw)
			)
			tmp_image.save()
			bpy.data.images.remove(tmp_image)

		# convert images to webp
		if self.webp_textures:
			for images in images_to_convert:
				input_path = os.path.join(export_path, images[0])
				output_path = os.path.join(export_path, images[1])
				process = subprocess.Popen(
				    [
				        utils.get_cwebp_path(), "-mt", "-q", "90", input_path,
				        "-o", output_path
				    ],
				    stdout=None,
				    stderr=None
				)
				process.communicate()
				os.remove(input_path)

		# write fst file
		fst_file = open(fst_filepath, "w")
		fst = "name = " + avatar_name + "\n"
		fst += "type = body+head\n"
		fst += "scale = 1\n"
		fst += "filename = " + os.path.basename(fbx_filepath) + "\n"
		fst += "texdir = .\n"
		fst += "joint = jointRoot = Hips\n"
		fst += "joint = jointLean = Spine\n"
		fst += "joint = jointNeck = Neck\n"
		fst += "joint = jointHead = Head\n"
		fst += "joint = jointEyeRight = RightEye\n"
		fst += "joint = jointEyeLeft = LeftEye\n"
		fst += "joint = jointLeftHand = LeftHand\n"
		fst += "joint = jointRightHand = RightHand\n"
		fst += "freeJoint = LeftArm\n"
		fst += "freeJoint = LeftForeArm\n"
		fst += "freeJoint = RightArm\n"
		fst += "freeJoint = RightForeArm\n"
		fst += "materialMap = " + json.dumps(
		    material_map, separators=(",", ":")
		) + "\n"
		fst_file.write(fst)
		fst_file.close()

		return {"FINISHED"}
