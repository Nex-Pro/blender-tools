import bpy

class TivoliSettings(bpy.types.PropertyGroup):
	avatar_extras: bpy.props.BoolProperty(default=False)

	# ---

	export_scene_webp: bpy.props.BoolProperty(
	    name="WebP texture optimize", default=False
	)

	# ---

	bake_enabled: bpy.props.BoolProperty(default=False)

	bake_automatic_texture_size: bpy.props.BoolProperty(
	    name="Auto texture size", default=True
	)
	bake_texture_size: bpy.props.EnumProperty(
	    name="Texture size",
	    items=[
	        ("128", "128", ""),
	        ("256", "256", ""),
	        ("512", "512", ""),
	        ("1024", "1024", ""),
	        ("2048", "2048", ""),
	        ("4096", "4096", ""),
	        ("8192", "8192", ""),
	    ],
	    options={'ENUM_FLAG'},
	    default={"1024"}
	)

	bake_oidn: bpy.props.BoolProperty(
	    name="Denoise with Intel® OIDN", default=True
	)

	bake_export_as_json: bpy.props.BoolProperty(
	    name="Export scene as JSON", default=True
	)
	bake_export_webp: bpy.props.BoolProperty(
	    name="WebP texture optimize", default=False
	)

	bake_current: bpy.props.StringProperty(name="Object", default="")
	bake_current_texture_size: bpy.props.StringProperty(
	    name="Tex. Size", default=""
	)
	bake_progress: bpy.props.FloatProperty(
	    name="Bake progress", default=-1, subtype="PERCENTAGE", min=-1, max=100
	)
