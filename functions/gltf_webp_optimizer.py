import os
import json
import subprocess

magick_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "../libs/magick"
)
if os.name == "nt":
	magick_path += ".exe"

def gltf_webp_optimizer(gltf_path):
	print("WebP optimizing: " + gltf_path)
	gltf_dir = os.path.dirname(gltf_path)

	file = open(gltf_path, "r")
	gltf = json.load(file)

	if "images" not in gltf:
		return

	write_new_gltf = False

	for image in gltf["images"]:
		filename = image["uri"]
		if filename.endswith(".webp"):
			continue

		path = os.path.join(gltf_dir, filename)
		if not os.path.exists(path):
			continue

		print("Optimizing image: " + filename)

		webp_filename = filename.split(".")
		webp_filename.pop()
		webp_filename = ".".join(webp_filename) + ".webp"
		webp_path = os.path.join(gltf_dir, webp_filename)

		if not os.path.exists(webp_path):
			magick_args = [magick_path, path, webp_path]
			magick = subprocess.Popen(
			    magick_args,
			    stdout=subprocess.PIPE,
			    stderr=None,
			)
			magick.communicate()

			if magick.returncode != 0:
				continue

		image["uri"] = webp_filename
		write_new_gltf = True
		os.remove(path)

	file.close()

	if write_new_gltf:
		file = open(gltf_path, "w")
		json.dump(gltf, file, indent=4)