from __future__ import print_function
import os
import download
import sys
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("filename")
parser.add_argument("url")
options=parser.parse_args()
if options.url.endswith(".tar.gz"):
	kind = "tar.gz"
elif options.url.endswith(".gz"):
	kind = "gz"
elif options.url.endswith(".tar"):
	kind = "tar"
elif options.url.endswith(".zip"):
	kind = "zip"
else:
	kind = "file"
download.download(options.url, options.filename, kind=kind, replace=False)
print("downloaded file with ",options)