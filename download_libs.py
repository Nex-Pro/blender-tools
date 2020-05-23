import os
import shutil
import tarfile
import urllib.request
import subprocess

def github_release(project, version, filename):
	return "https://github.com/" + project + "/releases/download/" + version + "/" + filename

if os.name == "posix":
	oidn_filename = "oidn-1.2.0.x86_64.linux.tar.gz"
	magick_filename = "magick"

elif os.name == "nt":
	oidn_filename = "oidn-1.2.0.x64.vc14.windows.zip"
	magick_filename = "ImageMagick-7.0.10-13-Q16-x64-static.exe"

oidn_url = github_release("OpenImageDenoise/oidn", "v1.2.0", oidn_filename)
magick_url = "https://imagemagick.org/download/binaries/" + magick_filename

# make libs folder
libs_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "libs")
if os.path.exists(libs_dir):
	shutil.rmtree(libs_dir)
os.makedirs(libs_dir)

# install oidn
oidn_tar_path = os.path.join(libs_dir, oidn_filename)
print("Downloading: " + oidn_url)
urllib.request.urlretrieve(oidn_url, oidn_tar_path)
print("Extracting: " + oidn_tar_path)
tar = tarfile.open(oidn_tar_path, "r:gz")
tar.extractall(libs_dir)
tar.close()
os.rename(oidn_tar_path.replace(".tar.gz", ""), os.path.join(libs_dir, "oidn"))
os.remove(oidn_tar_path)

# install imagemagick
magick_path = os.path.join(
    libs_dir, "magick.exe" if os.name == "nt" else "magick"
)
print("Downloading: " + magick_url)
urllib.request.urlretrieve(magick_url, magick_path)
if os.name == "posix":
	subprocess.Popen(
	    ["chmod", "+x", magick_path],
	    stdout=subprocess.PIPE,
	    stderr=subprocess.PIPE
	)
