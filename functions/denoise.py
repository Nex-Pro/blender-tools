import sys
import os
import subprocess
import numpy
import tempfile
import re
import bpy

# https://github.com/Naxela/The_Lightmapper/blob/d3451a3f6739cfba9d069d559c4bc2e3bcf39969/Addon/Utility/utility.py

def loadPfm(file, as_flat_list=False):
	#start = time()

	header = file.readline().decode("utf-8").rstrip()
	if header == "PF":
		color = True
	elif header == "Pf":
		color = False
	else:
		raise Exception("Not a PFM file.")

	dim_match = re.match(r"^(\d+)\s(\d+)\s$", file.readline().decode("utf-8"))
	if dim_match:
		width, height = map(int, dim_match.groups())
	else:
		raise Exception("Malformed PFM header.")

	scale = float(file.readline().decode("utf-8").rstrip())
	if scale < 0:  # little-endian
		endian = "<"
		scale = -scale
	else:
		endian = ">"  # big-endian

	data = numpy.fromfile(file, endian + "f")
	shape = (height, width, 3) if color else (height, width)
	if as_flat_list:
		result = data
	else:
		result = numpy.reshape(data, shape)
	#print("PFM import took %.3f s" % (time() - start))
	return result, scale

def savePfm(file, image, scale=1):
	# start = time()

	if image.dtype.name != "float32":
		raise Exception(
		    "Image dtype must be float32 (got %s)" % image.dtype.name
		)

	if len(image.shape) == 3 and image.shape[2] == 3:  # color image
		color = True
	elif len(
	    image.shape
	) == 2 or len(image.shape) == 3 and image.shape[2] == 1:  # greyscale
		color = False
	else:
		raise Exception(
		    "Image must have H x W x 3, H x W x 1 or H x W dimensions."
		)

	file.write(b"PF\n" if color else b"Pf\n")
	file.write(b"%d %d\n" % (image.shape[1], image.shape[0]))

	endian = image.dtype.byteorder

	if endian == "<" or endian == "=" and sys.byteorder == "little":
		scale = -scale

	file.write(b"%f\n" % scale)

	image.tofile(file)

	# print("PFM export took %.3f s" % (time() - start))

# https://github.com/Naxela/The_Lightmapper/blob/d3451a3f6739cfba9d069d559c4bc2e3bcf39969/Addon/Utility/denoise.py

def denoise(image):
	print("Denoising: " + image.name + "...")
	width = image.size[0]
	height = image.size[1]

	# create and write pfm
	original_array = numpy.array(image.pixels)
	original_array = original_array.reshape(height, width, 4)
	original_array = numpy.float32(original_array[:, :, :3])

	original_dest = tempfile.mkstemp(suffix=".pfm")[1]
	denoised_dest = tempfile.mkstemp(suffix=".pfm")[1]

	with open(original_dest, "wb") as file:
		savePfm(file, original_array)

	# run oidn
	# TODO: use oidn stored in git repo and write how to in readme
	oidn_path = "/home/maki/oidn/bin/denoise"
	oidn_args = [
	    oidn_path + " -f RTLightmap --hdr " + original_dest + " -o " +
	    denoised_dest
	]
	oidn = subprocess.Popen(
	    oidn_args, stdout=subprocess.PIPE, stderr=None, shell=True
	)
	oidn.communicate()[0]

	# read and save denoised pfm
	with open(denoised_dest, "rb") as file:
		denoised_data, scale = loadPfm(file)

	ndata = numpy.array(denoised_data)
	ndata2 = numpy.dstack((ndata, numpy.ones((width, height))))
	denoised_array = ndata2.ravel()
	bpy.data.images[image.name].pixels = denoised_array

	tmp_dir = os.path.join(os.path.dirname(bpy.data.filepath), "tmp")
	if not os.path.exists(tmp_dir):
		os.makedirs(tmp_dir)

	# TODO: use dwaa compression
	bpy.data.images[image.name
	               ].filepath_raw = os.path.join(tmp_dir, image.name) + ".exr"
	bpy.data.images[image.name].file_format = "OPEN_EXR"
	bpy.data.images[image.name].save()
