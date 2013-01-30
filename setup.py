import os
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), "asset_tracker", "__version__.py")) as version_file:
    exec(version_file.read())

setup(name="asset_tracker",
      classifiers = [
          "Programming Language :: Python :: 2.7",
          ],
      description="Utility to track your digital assets (photos, videos, etc.)",
      license="BSD",
      author="Rotem Yaari",
      author_email="vmalloc@gmail.com",
      version=__version__,
      packages=find_packages(exclude=["tests"]),
      install_requires=[
          "pushy",
      ],
      scripts=[],
      namespace_packages=[]
      )
