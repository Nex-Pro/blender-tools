import bpy
import bmesh
import math
from mathutils import Vector

# def mesh_area(bm):
# 	return sum(f.calc_area() for f in bm.faces)

def tri_area(co1, co2, co3):
	return (co2 - co1).cross(co3 - co1).length / 2.0

# https://git.tivolicloud.com/tivolicloud/interface/-/blob/master/libraries/image/src/image/TextureProcessing.cpp#L56
# powers of 2 till SPARSE_PAGE_SIZE then multiples of SPARSE_PAGE_SIZE until 8192
def rectify_dimension(dimension):
	SPARSE_PAGE_SIZE = 512

	if dimension == 0:
		return 0
	if dimension < SPARSE_PAGE_SIZE:
		new_size = SPARSE_PAGE_SIZE
		while (dimension <= new_size / 2):
			new_size /= 2
		return new_size
	else:
		pages = (
		    math.floor(dimension / SPARSE_PAGE_SIZE) +
		    (0 if dimension % SPARSE_PAGE_SIZE == 0 else 1)
		)
		new_size = pages * SPARSE_PAGE_SIZE
		if new_size > 8192:
			new_size = 8192
		return new_size

# for i in range(1, 1024, 10):
# 	print(i, "=>", rectify_dimension(i))
# for i in range(1, 9000, 100):
# 	print(i, "=>", rectify_dimension(i))

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

	if uv_area > 1:
		uv_area = 1

	density = 128
	res = math.sqrt(face_area / uv_area) * density
	if res < 128:
		res = 128

	res = rectify_dimension(res)

	# print()
	# print(obj.name)
	# print("face area:", face_area)
	# print("uv area:", uv_area)
	# print("res:", res)

	return res