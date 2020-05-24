import os
import json
import subprocess
import threading
from .. import utils

if os.name == "posix":
	magick_path = utils.which("magick")
elif os.name == "nt":
	magick_path = os.path.join(
	    os.path.dirname(os.path.realpath(__file__)), "../libs/magick"
	) + ".exe"

tivoli_max_texture_size = "8192x8192"

class ThreadedCommand(threading.Thread):
	def __init__(self, command):
		self.stdout = None
		self.stderr = None
		self.command = command
		threading.Thread.__init__(self)

	def run(self):
		process = subprocess.Popen(
		    self.command,
		    stdout=subprocess.PIPE,
		    stderr=subprocess.PIPE,
		)
		self.stdout, self.stderr = process.communicate()
		print("Finished: " + " ".join(self.command))

def gltf_webp_optimizer(gltf_path):
	print("WebP optimizing: " + gltf_path)
	gltf_dir = os.path.dirname(gltf_path)

	file = open(gltf_path, "r")
	gltf = json.load(file)

	if "images" not in gltf:
		return

	commands = []
	old_images = []

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
			commands.append(
			    [
			        magick_path, path, "-resize", tivoli_max_texture_size + ">",
			        webp_path
			    ]
			)
			old_images.append(path)

		image["uri"] = webp_filename
		write_new_gltf = True

	file.close()

	threads = []
	for command in commands:
		thread = ThreadedCommand(command)
		thread.start()
		threads.append(thread)
	for thread in threads:
		thread.join()

	for path in old_images:
		os.remove(path)

	if len(old_images) > 0:
		file = open(gltf_path, "w")
		json.dump(gltf, file, indent=4)