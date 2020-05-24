bl_info = {
    "name": "Tivoli Blender Tools",
    "author": "Tivoli Cloud VR, Inc.",
    "description": "",
    "version": (0, 0, 1),
    "blender": (2, 82, 0),
    "location": "View 3D > Tool Shelf > Tivoli",
    "warning": "",
    "category": "3D View",
}

import bpy

from .settings import *

from .operators.lightmap.prepare_uv_maps import *
from .operators.lightmap.prepare_materials import *
from .operators.lightmap.bake_scene import *
from .operators.lightmap.export_scene import *
from .operators.export_scene import *

from .panels.lightmap import *
from .panels.export_scene import *

operators = (
    LightmapPrepareUVMaps,
    LightmapPrepareMaterials,
    LightmapBakeScene,
    LightmapExportScene,
    ExportScene,
)

panels = (ExportScenePanel, LightmapPanel)

classes = (TivoliSettings, ) + operators + panels

main_register, main_unregister = bpy.utils.register_classes_factory(classes)

def register():
	main_register()

	bpy.types.Scene.tivoli_settings = bpy.props.PointerProperty(
	    type=TivoliSettings
	)

def unregister():
	main_unregister()
