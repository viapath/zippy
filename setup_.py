from setuptools import setup, find_packages
import os
print("cwd",os.getcwd())
with open("version.dat", "r") as opf:
	version=opf.read()

setup(
    name='zippy',
    version=version,
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[]
)
