#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 10 10:31:44 2021

@author: jorge
"""


import os


class Paths:
    def __init__(self, project_dir):
        self.project_dir = project_dir

    @property
    def data(self):
        return os.path.join(self.project_dir, "pydeflate", "data")


paths = Paths(os.path.dirname(os.path.dirname(__file__)))
