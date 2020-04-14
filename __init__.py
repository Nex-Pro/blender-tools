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
import os
import json
import shutil

def isObjBakeable(obj):
    return obj.visible_get() == True and obj.type == "MESH"

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

class PrepareUVMaps(bpy.types.Operator):
    bl_idname = "tivoli.prepare_uv_maps"
    bl_label = "Tivoli: Prepare UV maps"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        objects = scene.objects

        UV_NAME = "Tivoli_Lightmap"
        
        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        for obj in objects:
            if not isObjBakeable(obj):
                continue

            print("Preparing UV map for: " + obj.name)
        
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
            try:
                # bpy.ops.uv.lightmap_pack(PREF_CONTEXT="ALL_FACES")
                bpy.ops.uv.smart_project(angle_limit=33)
            except:
                print("Can't generate UV map for:" + obj.name)

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
        material.use_nodes = True # makes principled
    return material

class PrepareMaterials(bpy.types.Operator):
    bl_idname = "tivoli.prepare_materials"
    bl_label = "Tivoli: Prepare Materials"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        objects = scene.objects

        MATERIAL_PREFIX = "Tivoli_Lightmap"
        # RANDOM_STRING_LENGTH = 8

        def serializeName(obj, material):
            return (
                MATERIAL_PREFIX + "_" +
                obj.name + "_" +
                material.name
            )

        def deserializeName(obj, material):
            return material.name[
                len(MATERIAL_PREFIX + "_" + obj.name + "_")
                :
                99999
            ]

        materials_in_use = []
        images_in_use = []

        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        for obj in objects:
            if obj.visible_get() == False or obj.type != "MESH":
                continue

            print("Preparing materials for: " + obj.name)

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

            # add image for baking to the first material 
            material = obj.material_slots[0].material
            material.use_nodes = True
            nodes = material.node_tree.nodes

            for node in nodes:
                if node.name == MATERIAL_PREFIX:
                    nodes.remove(node)

            node = nodes.new("ShaderNodeTexImage")
            node.name = MATERIAL_PREFIX
            # node.show_preview = True
            # node.mute = True

            new_image_name = MATERIAL_PREFIX + "_" + obj.name

            for image in bpy.data.images:
                if image.name == new_image_name:
                    bpy.data.images.remove(image)

            new_image = bpy.data.images.new(
                name=MATERIAL_PREFIX + "_" + obj.name, 
                width=1,
                height=1,
                alpha=False,
                float_buffer=True, # TODO: neccessary?
                # is_data=True
            )
            new_image.file_format = "OPEN_EXR"

            node.image = new_image
            images_in_use.append(new_image)

            # just for testing
            # bsdf = nodes["Principled BSDF"]
            # material.node_tree.links.new(
            #     node.outputs["Color"],
            #     bsdf.inputs["Emission"]
            # )

        deselectAll() # not being used
        
        # remove all unused lightmap materials and textures   
        for material in bpy.data.materials:
            if material.name.startswith(MATERIAL_PREFIX) == False:
                continue
            if material not in materials_in_use:
                print("Deleting unused material: " + material.name)
                bpy.data.materials.remove(material)

        for image in bpy.data.images:
            if image.name.startswith(MATERIAL_PREFIX) == False:
                continue
            if image not in images_in_use:
                print("Deleting unused image: " + image.name)
                bpy.data.images.remove(image)

                
        return {"FINISHED"}

class BakeScene(bpy.types.Operator):
    bl_idname = "tivoli.bake_scene"
    bl_label = "Tivoli: Bake Scene"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        objects = scene.objects

        def getTextureNode(material):
            for node in material.node_tree.nodes:
                if node.name.startswith("Tivoli_Lightmap"):
                    return node

        def unlinkDiffuse(material_slots):
            old_links = []

            for material_slot in material_slots:
                material = material_slot.material
                nodes = material.node_tree.nodes
                links = material.node_tree.links
                
                bsdf = nodes["Principled BSDF"]

                for link in links:
                    if link.to_node != bsdf or link.to_socket.name != "Base Color":
                        continue

                    color = bsdf.inputs["Base Color"].default_value

                    old_links.append({
                        "links": links,
                        "from": link.from_socket,
                        "to": link.to_socket,
                        
                        "color": color,
                        # TODO: do this better
                        "color_r": color[0],
                        "color_g": color[1],
                        "color_b": color[2],
                        "color_a": color[3]
                    })

                    links.remove(link)
                
                bsdf.inputs["Base Color"].default_value = (1,1,1,1)

            return old_links

        def relinkDiffuse(old_links):
            for old_link in old_links:
                old_link["links"].new(
                    old_link["from"],
                    old_link["to"]
                )
                old_link["color"][0] = old_link["color_r"]
                old_link["color"][1] = old_link["color_g"]
                old_link["color"][2] = old_link["color_b"]
                old_link["color"][3] = old_link["color_a"]

        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        for obj in objects:
            if not isObjBakeable(obj):
                continue

            print("Baking: " + obj.name)

            # select obj
            deselectAll()
            obj.select_set(state=True)
            context.view_layer.objects.active = obj

            # necessary for diffuse light map
            # TODO: this must happen for all objects before bake
            links = unlinkDiffuse(obj.material_slots) 

            # select texture node
            first_material = obj.material_slots[0].material
            node = getTextureNode(first_material)
            first_material.node_tree.nodes.active = node

            # https://docs.blender.org/api/current/bpy.ops.object.html#bpy.ops.object.bake
            bpy.ops.object.bake(
                type="COMBINED",
                # pass_filter={"EMIT","DIRECT","INDIRECT"},
                uv_layer="Tivoli_Lightmap",
                # filepath=os.path.join(basedir, obj.name+".png"),
                # width=128,
                # height=128,
                # margin=2,
                # save_mode="EXTERNAL",
            )

            relinkDiffuse(links)

        deselectAll()

        return {"FINISHED"}

def findObject(name):
    for obj in bpy.context.scene.objects:
        if obj.name == name:
            return obj

def findObjectFromMaterialName(name):
    for obj in bpy.context.scene.objects:
        for material_slot in obj.material_slots:
            if material_slot.material.name == name:
                return obj

class ExportScene(bpy.types.Operator):
    bl_idname = "tivoli.export_scene"
    bl_label = "Tivoli: Export Scene"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        # LIGHTMAP_EXT = ".exr" # for saving
        # LIGHTMAP_TYPE = "OPEN_EXR" # for blender
        # LIGHTMAP_MIMETYPE = "image/exr" # for gltf

        LIGHTMAP_EXT = ".png" # for saving
        LIGHTMAP_TYPE = "PNG" # for blender
        LIGHTMAP_MIMETYPE = "image/png" # for gltf

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
            use_selection=True,
            export_apply=True,
            filepath=filepath
        )

        # export lightmap images
        for image in bpy.data.images:
            if image.name.startswith("Tivoli_Lightmap_") == False:
                continue

            image.filepath_raw = os.path.join(export_dir, image.name) + LIGHTMAP_EXT
            image.file_format = LIGHTMAP_TYPE
            image.save()

        # modify gltf
        with open(filepath, "r") as file:
            data = json.load(file)

            def addTexture(image_name):
                if "images" not in data:
                    data["images"] = []
                if "textures" not in data:
                    data["textures"] = []

                data["images"].append({
			        "mimeType": LIGHTMAP_MIMETYPE,
			        "name": image_name,
			        "uri": image_name + LIGHTMAP_EXT
                })
                source = len(data["images"]) - 1

                data["textures"].append({
                    "source": source
                })
                index = len(data["textures"]) - 1

                return index

            for material in data["materials"]:
                obj = findObjectFromMaterialName(material["name"])

                image_name = "Tivoli_Lightmap_" + obj.name
                texture_index = addTexture(image_name)
                
                print(image_name)
                print(texture_index)
                             
                material["lightmapTexture"] = {
				    "index": texture_index,
				    "texCoord": 1
			    }

            # export gltf
            with open(filepath, "w") as file:
                json.dump(data, file, indent=4)

        deselectAll()

        return {"FINISHED"}

class ToolPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_tivoli"
    bl_label = "Tivoli Blender Tools"

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tivoli"

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(icon="SHADING_RENDERED", text="Baking pipeline")
        box.operator(icon="GROUP_UVS", text="Prepare UV maps", operator="tivoli.prepare_uv_maps")
        box.operator(icon="MATERIAL", text="Prepare materials", operator="tivoli.prepare_materials")
        box.operator(icon="RENDER_STILL", text="Bake scene", operator="tivoli.bake_scene")
        box.operator(icon="EXPORT", text="Export scene", operator="tivoli.export_scene")

classes = (
    PrepareUVMaps,
    PrepareMaterials,
    BakeScene,
    ExportScene,
    ToolPanel
)

main_register, main_unregister = bpy.utils.register_classes_factory(classes)    

def register():
    main_register()

def unregister():
    main_unregister()
