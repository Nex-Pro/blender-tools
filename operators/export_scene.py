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
	normalized_origin = utils.vec_divide(
	    origin, utils.vec_divide(dimensions, Vector((2, 2, 2)))
	)
	# 0 to 1
	registration_point = (
	    (
	        utils.vec_multiply(normalized_origin, Vector((-1, -1, 1))) +
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
	    "id": utils.tivoli_uuid(),
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

	def execute(self, context):
		if not bpy.data.is_saved:
			raise Exception("Save first before exporting")

		utils.deselect_all(context)
		utils.deselect_all_outliner(context)

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

		# make sure all objects are valid
		for obj in scene.objects:
			if (
			    obj.visible_get() == False or
			    obj.cycles_visibility.camera == False
			):
				continue

			scale = obj.matrix_world.to_scale()
			if scale.x < 0 or scale.y < 0 or scale.z < 0:
				utils.select_only(obj)
				raise Exception(
				    obj.name +
				    " has a negative scale which is not supported in Tivoli"
				)

		# collect all objects including instanced collections
		objects = []
		instanced_objects = []  # to be cleaned up

		for obj in scene.objects:
			if (
			    obj.visible_get() == False or
			    obj.cycles_visibility.camera == False
			):
				continue

			if obj in objects:
				continue

			if obj.type == "MESH":
				objects.append(obj)
				continue

			if obj.type == "EMPTY" and obj.instance_type == "COLLECTION":
				utils.select_only(obj)

				bpy.ops.object.duplicate()  # changes selection
				for obj in context.selected_objects:
					instanced_objects.append(obj)  # cleanup

				bpy.ops.object.duplicates_make_real()  # changes selection
				for obj in context.selected_objects:
					instanced_objects.append(obj)  # cleanup

					if obj.type == "MESH":
						objects.append(obj)

		# iterate and write to export
		meshes = []

		export = {"Id": utils.tivoli_uuid(), "Version": 129, "Entities": []}

		root_entity = tivoli_empty(project_name)
		export["Entities"].append(root_entity)

		for obj in objects:
			# child parented to a child?
			if obj.type != "MESH":
				continue

			mesh = obj.data

			# tivoli doesn't render loose vertices so remove them
			# note, this happens on the object in the scene which is destructive
			utils.select_only(obj)
			bpy.ops.object.mode_set(mode="EDIT")
			bpy.ops.mesh.select_all(action="SELECT")
			bpy.ops.mesh.delete_loose(
			    use_verts=True, use_edges=False, use_faces=False
			)
			bpy.ops.mesh.select_all(action="DESELECT")
			bpy.ops.object.mode_set(mode="OBJECT")

			# export mesh to gltf
			mesh_filename = mesh.name + ".gltf"
			# mesh_export_dir = os.path.join(project_export_dir, mesh.name)
			# mesh_filepath = os.path.join(mesh_export_dir, mesh_filename)
			mesh_filepath = os.path.join(project_export_dir, mesh_filename)

			if mesh not in meshes:
				meshes.append(mesh)

				# os.makedirs(mesh_export_dir)

				export_object = bpy.data.objects.new(utils.tivoli_uuid(), mesh)
				context.collection.objects.link(export_object)

				utils.select_only(export_object)

				# remove doubles from mesh
				bpy.ops.object.mode_set(mode="EDIT")
				bpy.ops.mesh.select_all(action="SELECT")
				bpy.ops.mesh.remove_doubles(threshold=0.0001)
				bpy.ops.mesh.select_all(action="DESELECT")
				bpy.ops.object.mode_set(mode="OBJECT")

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
			url = "./" + mesh_filename

			matrix = obj.matrix_world

			position = vec_swap_nzy(matrix.to_translation())
			dimensions = vec_swap_yz(obj.dimensions)
			rotation = quat_swap_nzy(matrix.to_quaternion())
			registration_point = tivoli_registration_point(obj)

			export["Entities"].append(
			    {
			        "id": utils.tivoli_uuid(),
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
			utils.select_only(obj)
			bpy.ops.object.delete()

		utils.deselect_all()

		# write to json
		filepath = os.path.join(project_export_dir, project_name) + ".json"
		with open(filepath, "w") as file:
			json.dump(export, file, separators=(",", ":"))

		return {"FINISHED"}
