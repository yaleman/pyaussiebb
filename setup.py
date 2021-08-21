""" setup script for packaging the module """

import setuptools

with open("README.md", "r") as fh:
    LONGDESCRIPTION = fh.read()

setuptools.setup(
    name="pyaussiebb",
    version="0.0.4",
    author="James Hodgkinson",
    author_email="yaleman@ricetek.net",
    description="Aussie Broadband API module",
    long_description=LONGDESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/yaleman/aussiebb",
    packages=setuptools.find_packages(),
    install_requires=['requests', 'loguru'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
