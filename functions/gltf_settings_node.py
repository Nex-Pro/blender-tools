import bpy

def get_gltf_settings_node_name():
	return "glTF Settings"

def get_gltf_settings_node():
	node_group_name = get_gltf_settings_node_name()

	if node_group_name in bpy.data.node_groups:
		node_group = bpy.data.node_groups[node_group_name]
	else:
		# create a new node group
		node_group = bpy.data.node_groups.new(node_group_name, "ShaderNodeTree")

		node_group.inputs.new("NodeSocketFloat", "Occlusion")

		node_group.nodes.new("NodeGroupOutput")
		node_group_input = node_group.nodes.new("NodeGroupInput")
		node_group_input.location = -200, 0

	return node_group