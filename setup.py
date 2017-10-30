from setuptools import setup
import os

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as file_readme:
      long_description = file_readme.read()

setup(name="beanstalktop",
      description="A simple, top-like monitoring tool for beanstalkd",
      long_description=long_description,
      url='https://github.com/wewriteapps/beanstalktop',
      author='Phillip B Oldham',
      version='0.0.4',
      entry_points={
          'console_scripts': [
              'beanstalktop = beanstalktop:main',
              ],
          },
      py_modules=['beanstalktop'],
      install_requires=[
          'beanstalkc',
          'PyYAML',
          ],
      )
