# -*- coding: utf-8 -*-
from interface import ICalculate


class Foo(ICalculate):
    def __init__(self, feeder):
        ICalculate.__init__(self)
        self.feeder = feeder

    def avg(self):
        print("Foo avg")

    def max(self):
        print("Foo max")

    def run(self):
        self.avg()
        self.max()
'''
# duck-typing
def runnable(obj):
    obj.run()
'''
