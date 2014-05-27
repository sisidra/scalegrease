# !/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(name='scalegrease',
      version='1',
      url='https://github.com/spotify/scalegrease',
      description='A tool chain for executing batch processing jobs',
      packages=['scalegrease'],
      scripts=[
          'bin/greaserun',
          'bin/greaseworker'
      ]
)

