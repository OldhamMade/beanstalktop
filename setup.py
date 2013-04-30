from setuptools import setup, find_packages
import os, sys

setup(name="beanstalktop",
      description="A top-like monitoring tool for beanstalkd",
      packages=find_packages(),
      install_requires=[
          'beanstalkc',
          'PyYAML',
          ],
      )
