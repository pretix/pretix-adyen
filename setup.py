import os
from distutils.command.build import build

from django.core import management
from setuptools import setup, find_packages


try:
    with open(os.path.join(os.path.dirname(__file__), 'README.rst'), encoding='utf-8') as f:
        long_description = f.read()
except:
    long_description = ''


class CustomBuild(build):
    def run(self):
        management.call_command('compilemessages', verbosity=1)
        build.run(self)


cmdclass = {
    'build': CustomBuild
}


setup(
    name='pretix-adyen',
    version='1.1.1',
    description='This plugin allows to use Adyen as a payment provider',
    long_description=long_description,
    url='https://code.rami.io/pretix/pretix-adyen',
    author='Martin Gross',
    author_email='gross@rami.io',
    license='Apache Software License',

    install_requires=['Adyen'],
    packages=find_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,
    cmdclass=cmdclass,
    entry_points="""
[pretix.plugin]
pretix_adyen=pretix_adyen:PretixPluginMeta
""",
)
