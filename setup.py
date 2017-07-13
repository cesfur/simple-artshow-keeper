#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='artshowkeeper',
        version='2017.2',
        description='Artshow-Keeper (a part of Con Tools)',
        author='scheriff, takeru',
        author_email='scheriff@furry.cz',
        url='https://www.cesfur.org',
        license='GNU GPL 3',
        packages=['artshowkeeper',
                  'artshowkeeper.auction',
                  'artshowkeeper.common',
                  'artshowkeeper.controller',
                  'artshowkeeper.items',
                  'artshowkeeper.locale',
                  'artshowkeeper.model',
                  'artshowkeeper.reconciliation',
                  'artshowkeeper.settings'],
        package_data={'artshowkeeper': [
                'deployment/*',
                'locale/*.xml',
                'static/*',
                'templates/*',
                '*/static/*',
                '*/templates/*'
                ]},
        install_requires=['flask', 'pillow', 'netifaces'],
        scripts=['postinstall.py'],
        )
