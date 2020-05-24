import bpy
import subprocess
from uuid import uuid4
from mathutils import Vector

def isObjBakeable(obj):
	return obj.visible_get() == True and obj.type == "MESH"

def deselectAll():
	bpy.ops.object.select_all(action="DESELECT")

def deselectAllOutliner(context):
	for window in bpy.context.window_manager.windows:
		screen = window.screen
		for area in screen.areas:
			if area.type == "OUTLINER":
				override = {"window": window, "screen": screen, "area": area}
				bpy.ops.outliner.select_all(override, action="DESELECT")
				break

def selectOnly(obj):
	deselectAll()
	obj.select_set(state=True)

def findMaterial(name):
	for mat in bpy.data.materials:
		if name == mat.name:
			return mat

# def generateString(length):
#     chars = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
#     result = ""

#     for i in range(length):
#         result += random.choice(chars)

#     return result

def findMaterialOrCloneWithName(name, clone_material):
	material = findMaterial(name)
	if material == None:
		material = clone_material.copy()
		material.name = name
	return material

def findOrCreateDefaultMaterial():
	material = findMaterial("Material")
	if material == None:
		material = bpy.data.materials.new(name="Material")
		material.use_nodes = True  # makes principled
	return material

def findObject(name):
	for obj in bpy.context.scene.objects:
		if obj.name == name:
			return obj

def findObjectFromMaterialName(name):
	for obj in bpy.context.scene.objects:
		for material_slot in obj.material_slots:
			if (
			    material_slot.material != None and
			    material_slot.material.name == name
			):
				return obj

def tivoliUuid():
	return "{" + str(uuid4()) + "}"

def vecMultiply(a, b):
	return Vector((a[0] * b[0], a[1] * b[1], a[2] * b[2]))

def vecDivide(a, b):
	try:
		return Vector((a[0] / b[0], a[1] / b[1], a[2] / b[2]))
	except ZeroDivisionError:
		return Vector((0, 0, 0))

def rotateAroundPivot(position, rotation, pivot=Vector((0, 0, 0))):
	vec = position - pivot
	vec.rotate(rotation)
	return vec

def which(program):
	return subprocess.check_output(["which", program]).decode("utf-8").strip()
