import bpy
import os
import shutil
import json
from mathutils import Vector, Quaternion
from .. import utils
from ..functions.gltf_webp_optimizer import *

def vec_swap_yz(vec):
	return Vector((vec.x, vec.z, vec.y))

def vec_swap_nzy(vec):
	return Vector((vec.x, vec.z, -vec.y))

def quat_swap_nzy(q):
	q = Quaternion(q)
	axis = q.axis
	angle = q.angle

	axis_z = axis.z
	axis.z = -axis.y
	axis.y = axis_z
	return Quaternion(axis, angle)

def tivoli_registration_point(obj):
	bounding_box = [
	    vec_swap_yz(Vector(corner)) for corner in obj.bound_box
	]  # of mesh
	bounding_box_min = Vector(bounding_box[0])
	bounding_box_max = Vector(bounding_box[0])
	for corner in bounding_box:
		if corner.x < bounding_box_min.x:
			bounding_box_min.x = corner.x
		if corner.y < bounding_box_min.y:
			bounding_box_min.y = corner.y
		if corner.z < bounding_box_min.z:
			bounding_box_min.z = corner.z
		if corner.x > bounding_box_max.x:
			bounding_box_max.x = corner.x
		if corner.y > bounding_box_max.y:
			bounding_box_max.y = corner.y
		if corner.z > bounding_box_max.z:
			bounding_box_max.z = corner.z

	origin = (bounding_box_min + bounding_box_max) / 2
	dimensions = bounding_box_max - bounding_box_min

	# -1 to 1
	normalized_origin = utils.vecDivide(
	    origin, utils.vecDivide(dimensions, Vector((2, 2, 2)))
	)
	# 0 to 1
	registration_point = (
	    (
	        utils.vecMultiply(normalized_origin, Vector((-1, -1, 1))) +
	        Vector((1, 1, 1))
	    ) / 2
	)

	return registration_point

# def tivoli_registration_point(obj, rotation, as_position_delta=False):
# 	origin = 0.125 * sum((Vector(corner) for corner in obj.bound_box), Vector())

def tivoli_vec(vec):
	return {
	    "x": vec.x,
	    "y": vec.y,
	    "z": vec.z,
	}

def tivoli_quat(quat):
	return {
	    "x": quat.x,
	    "y": quat.y,
	    "z": quat.z,
	    "w": quat.w,
	}

def tivoli_empty(name, position=Vector(), rotation=Quaternion()):
	return {
	    "id": utils.tivoliUuid(),
	    "type": "Box",
	    "visible": False,
	    "name": name,
	    "position": tivoli_vec(position),
	    "dimensions": tivoli_vec(Vector()),
	    "rotation": tivoli_quat(rotation),
	    "grab": {
	        "grabbable": False
	    },
	    "shape": "Cube",
	}

class ExportScene(bpy.types.Operator):
	bl_idname = "tivoli.export_scene"
	bl_label = "Tivoli: Export scene to JSON"
	bl_options = {"REGISTER", "UNDO", "INTERNAL"}

	webp_textures: bpy.props.BoolProperty(
	    name="WebP textures", default=False, options={"HIDDEN"}
	)

	base_url: bpy.props.StringProperty(
	    name="Base URL", default="", options={"HIDDEN"}
	)

	def execute(self, context):
		if not bpy.data.is_saved:
			raise Exception("Save first before exporting")

		utils.deselectAll()
		utils.deselectAllOutliner(context)

		scene = context.scene

		# make export dir
		project_name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
		project_dir = os.path.dirname(bpy.data.filepath)
		project_export_dir = os.path.join(project_dir, project_name)

		if os.path.exists(project_export_dir):
			shutil.rmtree(project_export_dir)
		os.makedirs(project_export_dir)

		# textures_dir = os.path.join(project_export_dir, "textures")
		# os.makedirs(textures_dir)
		textures_dir = os.path.join(project_export_dir)

		# make export dir
		base_url = self.base_url.strip()
		if base_url == "":
			base_url = "file://" + project_export_dir
		if not base_url.endswith("/"):
			base_url += "/"

		# collect all objects including instanced collections
		objects = []
		instanced_objects = []  # to be cleaned up

		for obj in scene.objects:
			if obj.visible_get() == False:
				continue

			if obj in objects:
				continue

			if obj.type == "MESH":
				objects.append(obj)
				continue

			if obj.type == "EMPTY" and obj.instance_type == "COLLECTION":
				collection = obj.instance_collection
				name = obj.name

				location = obj.location
				scale = obj.scale
				rotation_euler = obj.rotation_euler

				for obj in collection.all_objects:
					instanced_object = bpy.data.objects.new(
					    name + ": " + obj.name, obj.data
					)
					context.collection.objects.link(instanced_object)

					instanced_object.location = utils.vecMultiply(
					    utils.rotateAroundPivot(obj.location, rotation_euler),
					    scale
					) + location
					instanced_object.scale = utils.vecMultiply(
					    scale,
					    obj.scale,
					)
					instanced_object.rotation_euler = (
					    rotation_euler[0] + obj.rotation_euler[0],
					    rotation_euler[1] + obj.rotation_euler[1],
					    rotation_euler[2] + obj.rotation_euler[2],
					)

					objects.append(instanced_object)
					instanced_objects.append(instanced_object)

		# iterate and write to export
		meshes = []

		export = {"Id": utils.tivoliUuid(), "Version": 129, "Entities": []}

		root_entity = tivoli_empty(project_name)
		export["Entities"].append(root_entity)

		for obj in objects:
			mesh = obj.data

			# export mesh to gltf
			mesh_filename = mesh.name + ".gltf"
			# mesh_export_dir = os.path.join(project_export_dir, mesh.name)
			# mesh_filepath = os.path.join(mesh_export_dir, mesh_filename)
			mesh_filepath = os.path.join(project_export_dir, mesh_filename)

			if mesh not in meshes:
				meshes.append(mesh)

				# os.makedirs(mesh_export_dir)

				export_object = bpy.data.objects.new(utils.tivoliUuid(), mesh)
				context.collection.objects.link(export_object)
				utils.selectOnly(export_object)

				bpy.ops.export_scene.gltf(
				    filepath=mesh_filepath,
				    export_format="GLTF_SEPARATE",
				    export_selected=True,
				    export_apply=True,
				    # TODO: duplicate image names will overwrite each other
				    export_texture_dir=textures_dir
				)
				bpy.ops.object.delete()

				if self.webp_textures:
					gltf_webp_optimizer(mesh_filepath)

			# gather information
			url = base_url + mesh_filename
			if url.startswith("file://"):
				url = url.replace("\\", "/")
			if os.name == "nt":
				url = url.replace("file://", "file:///")

			matrix = obj.matrix_world

			position = vec_swap_nzy(matrix.to_translation())
			dimensions = vec_swap_yz(obj.dimensions)
			rotation = quat_swap_nzy(matrix.to_quaternion())
			registration_point = tivoli_registration_point(obj)

			export["Entities"].append(
			    {
			        "id": utils.tivoliUuid(),
			        "type": "Model",
			        "parentID": root_entity["id"],
			        "name": obj.name,
			        "position": tivoli_vec(position),
			        "dimensions": tivoli_vec(dimensions),
			        "rotation": tivoli_quat(rotation),
			        "registrationPoint": tivoli_vec(registration_point),
			        "grab": {
			            "grabbable": False
			        },
			        "modelURL": url,
			    }
			)

		for obj in instanced_objects:
			utils.selectOnly(obj)
			bpy.ops.object.delete()

		utils.deselectAll()

		# write to json
		filepath = os.path.join(project_export_dir, project_name) + ".json"
		with open(filepath, "w") as file:
			json.dump(export, file, separators=(",", ":"))

		return {"FINISHED"}
