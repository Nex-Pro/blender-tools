import os
import shutil
import tarfile
import urllib.request
import subprocess
import tempfile
from zipfile import ZipFile

def github_release(project, version, filename):
	return "https://github.com/" + project + "/releases/download/" + version + "/" + filename

def download(url, path):
	filename = url.split("/").pop()
	file_path = os.path.join(path, filename)

	print("Downloading: " + url)
	urllib.request.urlretrieve(url, file_path)
	return file_path

def untar(file_path, extract_dir):
	print("Extracting: " + file_path)
	tar = tarfile.open(file_path, "r:gz")
	tar.extractall(extract_dir)
	tar.close()
	os.remove(file_path)

def unzip(file_path, extract_dir):
	print("Extracting: " + file_path)
	zip = ZipFile(file_path, "r")
	zip.extractall(extract_dir)
	zip.close()
	os.remove(file_path)

def download_oidn():
	oidn_version = "1.2.0"

	if os.name == "posix":
		oidn_filename = "oidn-" + oidn_version + ".x86_64.linux.tar.gz"
	elif os.name == "nt":
		oidn_filename = "oidn-" + oidn_version + ".x64.vc14.windows.zip"

	oidn_url = github_release(
	    "OpenImageDenoise/oidn", "v" + oidn_version, oidn_filename
	)
	oidn_archive_path = download(oidn_url, libs_dir)
	oidn_path = os.path.join(libs_dir, "oidn")

	if os.name == "posix":
		untar(oidn_archive_path, libs_dir)
		os.rename(oidn_archive_path.replace(".tar.gz", ""), oidn_path)
	elif os.name == "nt":
		unzip(oidn_archive_path, libs_dir)
		os.rename(oidn_archive_path.replace(".zip", ""), oidn_path)

	shutil.rmtree(os.path.join(oidn_path, "doc"))
	shutil.rmtree(os.path.join(oidn_path, "include"))
	if os.name == "nt":
		shutil.rmtree(os.path.join(oidn_path, "lib"))

def download_imagemagic():
	magick_url = "https://imagemagick.org/download/binaries/"

	if os.name == "posix":
		magick_path = download(magick_url + "magick", libs_dir)
		subprocess.Popen(
		    ["chmod", "+x", magick_path],
		    stdout=subprocess.PIPE,
		    stderr=subprocess.PIPE
		)
	elif os.name == "nt":
		magick_archive_path = download(
		    magick_url + "ImageMagick-7.0.10-13-portable-Q16-x64.zip", libs_dir
		)
		magick_extract_dir = os.path.join(libs_dir, "magick")
		unzip(magick_archive_path, magick_extract_dir)
		os.rename(
		    os.path.join(magick_extract_dir, "magick.exe"),
		    os.path.join(libs_dir, "magick.exe")
		)
		shutil.rmtree(magick_extract_dir)

# make libs folder
libs_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "libs")
if os.path.exists(libs_dir):
	shutil.rmtree(libs_dir)
os.makedirs(libs_dir)

# download libs!
download_oidn()
download_imagemagic()