import bpy
import subprocess
import os
from uuid import uuid4
from mathutils import Vector

def is_obj_bakeable(obj):
	return (
	    obj.visible_get() and obj.cycles_visibility.camera == True and
	    obj.type == "MESH"
	)

def get_context_with_area(areaType, context=bpy.context):
	# https://docs.blender.org/api/current/bpy.types.Area.html#bpy.types.Area.type
	for window in bpy.context.window_manager.windows:
		screen = window.screen
		for area in screen.areas:
			if area.type == areaType:
				return {"window": window, "screen": screen, "area": area}
	return None

def select_all(context=bpy.context):
	bpy.ops.object.select_all(
	    get_context_with_area("VIEW_3D", context), action="SELECT"
	)

def deselect_all(context=bpy.context):
	bpy.ops.object.select_all(
	    get_context_with_area("VIEW_3D", context), action="DESELECT"
	)

def deselect_all_outliner(context=bpy.context):
	bpy.ops.outliner.select_all(
	    get_context_with_area("OUTLINER", context), action="DESELECT"
	)

def select_only(obj):
	deselect_all()
	obj.select_set(state=True)

def find_material(name):
	for mat in bpy.data.materials:
		if name == mat.name:
			return mat

def find_image(name):
	for image in bpy.data.images:
		if name == image.name:
			return image

def image_ext(image):
	# https://docs.blender.org/api/current/bpy.types.Image.html?highlight=filepath_raw#bpy.types.f
	f = image.file_format
	if f == "JPEG":
		return "jpg"
	if f == "JPEG2000":
		return "jp2"
	if f == "TARGA" or f == "TARGA_RAW":
		return "tga"
	if f == "OPEN_EXR_MULTILAYER" or f == "OPEN_EXR":
		return "exr"
	return f.lower()

# def generateString(length):
#     chars = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
#     result = ""

#     for i in range(length):
#         result += random.choice(chars)

#     return result

def find_material_or_clone_with_name(name, clone_material):
	material = find_material(name)
	if material == None:
		material = clone_material.copy()
		material.name = name
	return material

def find_or_create_default_material():
	material = find_material("Material")
	if material == None:
		material = bpy.data.materials.new(name="Material")
		material.use_nodes = True  # makes principled
	return material

def find_object(name):
	for obj in bpy.context.scene.objects:
		if obj.name == name:
			return obj

def find_object_from_material_name(name):
	for obj in bpy.context.scene.objects:
		for material_slot in obj.material_slots:
			if (
			    material_slot.material != None and
			    material_slot.material.name == name
			):
				return obj

def tivoli_uuid():
	return "{" + str(uuid4()) + "}"

def vec_multiply(a, b):
	return Vector((a[0] * b[0], a[1] * b[1], a[2] * b[2]))

def vec_divide(a, b):
	try:
		return Vector((a[0] / b[0], a[1] / b[1], a[2] / b[2]))
	except ZeroDivisionError:
		return Vector((0, 0, 0))

def rotate_around_pivot(position, rotation, pivot=Vector((0, 0, 0))):
	vec = position - pivot
	vec.rotate(rotation)
	return vec

def which(program):
	return subprocess.check_output(["which", program]).decode("utf-8").strip()

def get_oidn_path():
	return os.path.join(
	    os.path.dirname(os.path.realpath(__file__)), "libs/oidn/bin/denoise"
	) + (".exe" if os.name == "nt" else "")

# def get_magick_path():
# 	if os.name == "posix":
# 		return which("magick")
# 	elif os.name == "nt":
# 		return os.path.join(
# 		    os.path.dirname(os.path.realpath(__file__)), "libs/magick.exe"
# 		)

def get_cwebp_path():
	return os.path.join(
	    os.path.dirname(os.path.realpath(__file__)), "libs/cwebp"
	) + (".exe" if os.name == "nt" else "")

def replace_filename_ext(filename, new_ext):
	new_filename = filename.split(".")
	new_filename.pop()
	return ".".join(new_filename) + new_ext

def is_in_parent_tree(start_obj, query_obj):
	current_obj = start_obj

	while current_obj != None:
		if current_obj == query_obj:
			return True
		current_obj = current_obj.parent

	return False