"""
Authors: Manuel Gasser, Julian Haldimann
Created: 05.03.2021
Last Modified: 17.03.2021
"""


class Command:

    def __init__(self, prefix, data):
        self.prefix = prefix
        self.data = data

    def get_prefix(self):
        return self.prefix

    def get_data(self):
        return self.data
