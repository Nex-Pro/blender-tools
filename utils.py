import bpy

def isObjBakeable(obj):
	return obj.visible_get() == True and obj.type == "MESH"

def deselectAll():
	bpy.ops.object.select_all(action="DESELECT")

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
			if material_slot.material.name == name:
				return obj