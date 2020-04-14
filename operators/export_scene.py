import bpy
import os
import shutil
import json

from .. import utils

class ExportScene(bpy.types.Operator):
    bl_idname = "tivoli.export_scene"
    bl_label = "Tivoli: Export Scene"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        # LIGHTMAP_EXT = ".exr" # for saving
        # LIGHTMAP_TYPE = "OPEN_EXR" # for blender
        # LIGHTMAP_MIMETYPE = "image/exr" # for gltf

        LIGHTMAP_EXT = ".jpg" # for saving
        LIGHTMAP_TYPE = "JPEG" # for blender
        LIGHTMAP_MIMETYPE = "image/jpeg" # for gltf

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
                obj = utils.findObjectFromMaterialName(material["name"])

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

        utils.deselectAll()

        return {"FINISHED"}