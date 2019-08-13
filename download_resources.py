import download.download
import sys
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("filename")
parser.add_argument("url")
options=parser.parse_args()
if options.url.endswith(".gz"):
	mode="gz"
else:
	mode="file"
download.download(options.url, options.filename)
print("downloaded file with ",options)