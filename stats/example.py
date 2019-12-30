# -*- coding: utf-8 -*-

class Foo(object):
    def __init__(self, feeder):
        self.feeder = feeder

    def avg(self):
        print("Foo avg")

    def max(self):
        print("Foo max")

    def calculate(self):
        self.avg()
        self.max()
