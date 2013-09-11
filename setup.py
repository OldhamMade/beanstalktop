from setuptools import setup, find_packages
import os

setup(name="beanstalktop",
      description="A simple, top-like monitoring tool for beanstalkd",
      long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
      url='https://github.com/wewriteapps/beanstalktop',
      author='Phillip B Oldham',
      version='0.0.4',
      entry_points={
          'console_scripts': [
              'beanstalktop = beanstalktop:main',
              ],
          },
      scripts=['beanstalktop.py', ],
      packages=find_packages(),
      install_requires=[
          'beanstalkc',
          'PyYAML',
          ],
      )
