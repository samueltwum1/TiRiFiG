#!/usr/bin/env python
#########################################################################################
# Author: Samuel (samueltwum1@gmail.com) with MSc supervisors                           #
# Copyright 2019 Samuel N. Twum                                                         #
#                                                                                       #
# MIT license - see LICENSE.txt for details                                             #
#########################################################################################

from os import path
from setuptools import setup, find_packages

this_directory = path.abspath(path.dirname(__file__))
files = {'Readme': 'README.md',
         'Changelog': 'CHANGELOG.md'}
long_description = ""
for name, filename in files.items():
    long_description += "{}\n\n".format(name)
    with open(path.join(this_directory, filename)) as f:
        file_contents = f.read()
    long_description += file_contents + "\n\n"


setup(
    name="TiRiFiG",
    version="2.0.0",
    description="A graphical user interface that allows users of TiRiFiC to modify tilted-ring parameters interactively.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Samuel Twum",
    author_email="samueltwum1@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    url="https://github.com/samueltwum1/TiRiFiG",
    download_url="https://pypi.org/project/TiRiFiG/",
    # home_page='http://under-construction',
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    platforms=["OS Independent"],
    keywords = "TiRiFiC"
    python_requires=">=3.0"
    install_requires=[
        "numpy",
        "matplotlib"],
    zip_safe=False,
    include_package_data=True,
    package_data={'TiRiFiG': ['icons/*.png']},
    data_files=[('parameter_files', ['example_data/*.def']),
                ('fit_files', ['example_data/*.fits'])],
    entry_points={
        'gui_scripts': ['TiRiFiG = TiRiFiG.launcher:main']}
      )
