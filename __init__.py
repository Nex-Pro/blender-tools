bl_info = {
    "name" : "Tivoli Blender Tools",
    "author" : "Tivoli Cloud VR, Inc.",
    "description" : "",
    "version" : (0, 0, 1),
    "blender" : (2, 82, 0),
    "location" : "View 3D > Tool Shelf > Tivoli",
    "warning" : "",
    "category" : "3D View"
}

import bpy
import random

def deselectAll():
    bpy.ops.object.select_all(action="DESELECT")

def selectOnly(obj):
    deselectAll()
    obj.select_set(state=True)

# def generateString(length):
#     chars = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
#     result = ""

#     for i in range(length):
#         result += random.choice(chars)

#     return result

class PrepareLightmapUVs(bpy.types.Operator):
    bl_idname = "tivoli.prepare_lightmap_uvs"
    bl_label = "Tivoli: Prepare Lightmap UVs"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        objects = scene.objects

        UV_NAME = "Tivoli_Lightmap"
        
        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        for obj in objects:
            if obj.visible_get() == False or obj.type != "MESH":
                continue

            # print("Preparing UVs for: " + obj.name)
        
            uv_layers = obj.data.uv_layers
            pre_active_index = uv_layers.active_index

            # delete uv map
            if UV_NAME in uv_layers:
                uv_layers.remove(uv_layers[UV_NAME])

            # create uv
            uv_layers.new(name=UV_NAME, do_init=True)
            uv_layers[UV_NAME].active = True

            # TODO: move uv layer to second slot

            selectOnly(obj)
            bpy.ops.uv.lightmap_pack()

            # cleanup
            if pre_active_index != -1:
                uv_layers.active_index = pre_active_index

        deselectAll()

        return {"FINISHED"}

def findMaterial(name):
    for mat in bpy.data.materials:
        if name == mat.name:
            return mat

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
    return material

class PrepareMaterials(bpy.types.Operator):
    bl_idname = "tivoli.prepare_materials"
    bl_label = "Tivoli: Prepare Materials"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        objects = scene.objects

        MATERIAL_PREFIX = "Tivoli_Lightmap_"
        # RANDOM_STRING_LENGTH = 8

        def serializeName(obj, material):
            return (
                MATERIAL_PREFIX + 
                obj.name + "_" +
                material.name
            )

        def deserializeName(obj, material):
            return material.name[
                len(MATERIAL_PREFIX + "_" + obj.name + "_") - 1
                :
                99999
            ]

        materials_in_use = []

        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        for obj in objects:
            if obj.visible_get() == False or obj.type != "MESH":
                continue

            # print("Preparing materials for: " + obj.name)

            material_slots = obj.material_slots.values()

            # for each material slot
            for index in range(len(material_slots)):
                material_slot = material_slots[index]
                material = material_slot.material

                if material == None:
                    material = findOrCreateDefaultMaterial()

                #  undo tivoli material
                if material.name.startswith(MATERIAL_PREFIX):
                    old_material_name = deserializeName(obj, material)
                    old_material = findMaterial(old_material_name)

                    if old_material != None:
                        material = old_material
                    else:
                        # cant find old material so use default
                        material = findOrCreateDefaultMaterial()

                # find or clone new material and replace
                new_material_name = serializeName(obj, material)
                new_material = findMaterialOrCloneWithName(
                    new_material_name,
                    material
                )

                obj.material_slots[index].material = new_material
                materials_in_use.append(new_material)

            # if no material slots, use default material
            if len(material_slots) == 0:
                material = findOrCreateDefaultMaterial()

                new_material_name = serializeName(obj, material)
                new_material = findMaterialOrCloneWithName(
                    new_material_name,
                    material
                )

                obj.data.materials.append(new_material)
                materials_in_use.append(new_material)

        deselectAll() # not being used
        
        # remove all unused lightmap materials     
        for material in bpy.data.materials:
            if material.name.startswith(MATERIAL_PREFIX) == False:
                continue

            if material not in materials_in_use:
                print("Deleting unused material: " + material.name)
                bpy.data.materials.remove(material)

                
        return {"FINISHED"}

# class Bake(bpy.types.Operator):
#     bl_idname = "tivoli.bake"
#     bl_label = "Tivoli: Bake"
#     bl_options = {"REGISTER", "UNDO"}

#     def execute(self, context):
#         scene = context.scene

#         return {"FINISHED"}

class ToolPanel(bpy.types.Panel):
    bl_idname = "3D_VIEW_TS_TIVOLI"
    bl_label = "Tivoli Tools"

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tivoli"

    def draw(self, context):
        layout = self.layout

        layout.row().operator("tivoli.prepare_lightmap_uvs")
        layout.row().operator("tivoli.prepare_materials")
        # layout.row().operator("tivoli.bake")

classes = (
    PrepareLightmapUVs,
    PrepareMaterials,
    # Bake,
    ToolPanel
)

main_register, main_unregister = bpy.utils.register_classes_factory(classes)    

def register():
    main_register()

def unregister():
    main_unregister()
