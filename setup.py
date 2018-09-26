from setuptools import setup
import os

VERSION_FILE = '__version__.py'

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as file_readme:
    long_description = file_readme.read()

exec(compile(open(VERSION_FILE).read(), VERSION_FILE, 'exec'))

setup(
    name="beanstalktop",
    description="A simple, top-like monitoring tool for beanstalkd",
    long_description=long_description,
    url='https://github.com/OldhamMade/beanstalktop',
    author=__author__,
    version=__version__,
    license=__licence__,
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
