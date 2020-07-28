import os
import sys
import shutil
import tarfile
import urllib.request
import subprocess
import tempfile
import xml.etree.ElementTree as ElementTree
from zipfile import ZipFile

if len(sys.argv) > 1:
	os.name = sys.argv[1]

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
		# TODO: --version doesn't show webp. users will have to system install
		# magick_path = download(magick_url + "magick", libs_dir)
		# subprocess.Popen(
		#     ["chmod", "+x", magick_path],
		#     stdout=subprocess.PIPE,
		#     stderr=subprocess.PIPE
		# )
		print("Download ImageMagick with your system's package manager")
	elif os.name == "nt":

		# get latest release url
		digest_res = urllib.request.urlopen(magick_url + "digest.rdf")
		digest_xml = ""
		for line in digest_res:
			digest_xml += line.decode("utf-8")
		digest = ElementTree.fromstring(digest_xml)
		releases = list(
		    filter(
		        lambda filename: filename.endswith("portable-Q16-x64.zip"),
		        map(
		            lambda content: content.
		            get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about"),
		            digest.findall(
		                "{http://www.wizards-toolkit.org/digest/1.0/}Content"
		            )
		        )
		    )
		)
		release_filename = releases[len(releases) - 1]

		magick_archive_path = download(magick_url + release_filename, libs_dir)
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