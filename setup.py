from setuptools import setup, find_packages
import os, pip, sys
#from pip import _internal as pipinternal
#print("cwd",os.getcwd())
from pip._internal.cli.main import main as _main
requires = [line.strip() for line in open("requirements.txt").readlines()]
try:
    with open("version.dat", "r") as opf:
	    version=opf.read()
except FileNotFoundError:
	version = '9.6'

_main(["install", "-r", "requirements.txt"])
os.system("{0} -mpip install -r requirements.txt".format(sys.executable))
#os.system("make zippy-install")
setup(
    name='zippy',
    version=version,
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires
)
