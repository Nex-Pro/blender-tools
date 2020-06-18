import sys
import os
import subprocess
import numpy
import tempfile
import re
import bpy
from .. import utils

# https://github.com/Naxela/The_Lightmapper/blob/master/Addon/Utility/utility.py

def load_pfm(file, as_flat_list=False):
	# start = time()

	header = file.readline().decode("utf-8").rstrip()
	if header == "PF":
		color = True
	elif header == "Pf":
		color = False
	else:
		raise Exception("Not a PFM file")

	dim_match = re.match(r"^(\d+)\s(\d+)\s$", file.readline().decode("utf-8"))
	if dim_match:
		width, height = map(int, dim_match.groups())
	else:
		raise Exception("Malformed PFM header")

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

def save_pfm(file, image, scale=1):
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

# https://github.com/Naxela/The_Lightmapper/blob/master/Addon/Utility/denoise.py

def denoise(image):
	print("Denoising: " + image.name + "...")
	width = image.size[0]
	height = image.size[1]

	# create and write pfm
	original_array = numpy.array(image.pixels)
	original_array = original_array.reshape(height, width, 4)
	original_array = numpy.float32(original_array[:, :, :3])

	original_file = tempfile.NamedTemporaryFile(suffix=".pfm", delete=True)
	denoised_file = tempfile.NamedTemporaryFile(suffix=".pfm", delete=True)

	save_pfm(original_file, original_array)

	# run oidn
	oidn_args = [
	    utils.getOidnPath() + " -f RTLightmap --hdr " + original_file.name +
	    " -o " + denoised_file.name
	]
	oidn = subprocess.Popen(
	    oidn_args, stdout=subprocess.PIPE, stderr=None, shell=True
	)
	oidn.communicate()[0]

	# read and save denoised pfm
	denoised_data, scale = load_pfm(denoised_file)

	ndata = numpy.array(denoised_data)
	ndata2 = numpy.dstack((ndata, numpy.ones((width, height))))
	denoised_array = ndata2.ravel()
	bpy.data.images[image.name].pixels = denoised_array

	original_file.close()
	denoised_file.close()