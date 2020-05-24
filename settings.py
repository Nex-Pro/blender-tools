import bpy

class TivoliSettings(bpy.types.PropertyGroup):
	export_scene_url: bpy.props.StringProperty(name="Export URL", default="")
	export_scene_webp: bpy.props.BoolProperty(
	    name="WebP texture optimize", default=True
	)

	# ---

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

	bake_current: bpy.props.StringProperty(name="Bake current", default="")
	bake_progress: bpy.props.FloatProperty(
	    name="Bake progress",
	    default=-1,
	    subtype="PERCENTAGE",
	    min=-1,
	    soft_min=0,
	    soft_max=100,
	    max=101
	)
