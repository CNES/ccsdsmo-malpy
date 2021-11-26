#!/usr/bin/env python3

from distutils.core import setup
from distutils import util

packages = [
    "malpy",
    "malpy.mo",
    "malpy.mo.com",
    "malpy.mo.com.services",
    "malpy.mo.mal",
    "malpy.mo.mc",
    "malpy.mo.mc.services",
    "malpy.transport"
]

def define_package_dir(packages):
    d = {}
    for p in packages:
        path = 'src/{}'.format(p.replace('.', '/'))
        d[p] = util.convert_path(path)
    return d

setup(
    name='malpy',
    version='0.1',
    description='CCSDS MO implementation in Python',
    author='CNES',
    maintainer='Olivier Churlaud',
    maintainer_email='olivier.churlaud@cnes.fr',
    packages=packages,
    package_dir=define_package_dir(packages),
    license='MIT',
    install_requires=['PyYAML']
)
