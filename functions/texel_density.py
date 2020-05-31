import bpy
import bmesh
from mathutils import Vector

# def mesh_area(bm):
# 	return sum(f.calc_area() for f in bm.faces)

def tri_area(co1, co2, co3):
	return (co2 - co1).cross(co3 - co1).length / 2.0

def recommended_texture_size(obj):
	bm = bmesh.new()
	bm.from_mesh(obj.data)
	bmesh.ops.transform(bm, matrix=obj.matrix_world, verts=bm.verts)

	# https://blender.stackexchange.com/a/151217
	bmesh.ops.triangulate(bm, faces=bm.faces)  # for uv_area
	bm.faces.ensure_lookup_table()

	if "Tivoli_Lightmap" not in bm.loops.layers.uv:
		return 0
	uv_loop = bm.loops.layers.uv["Tivoli_Lightmap"]

	face_area = 0  # in meters
	uv_area = 0  # in 1x1 units

	for face in bm.faces:
		face_area += tri_area(*(v.co for v in face.verts))
		uv_area += tri_area(*(Vector((*l[uv_loop].uv, 0)) for l in face.loops))

	density = 16
	res = face_area / uv_area * density
	if res < 128:
		res = 128
	if res > 8192:
		res = 8192

	powers_of_two = [2**i for i in range(0, 14)]  # up to 8192

	for power_res in powers_of_two:
		if power_res < res:
			continue
		res = power_res
		break

	# print()
	# print(obj.name)
	# print("face area:", face_area)
	# print("uv area:", uv_area)
	# print("res:", resolution)

	# im not sure how correct this is but it seems to be okay

	return res