# -*- coding: utf-8 -*-
from interface import ICalculate
from interface import IDisplay


class Foo(ICalculate):
    def __init__(self, feeder):
        ICalculate.__init__(self)
        self.feeder = feeder

    def avg(self):
        print("Foo cal avg")

    def max(self):
        print("Foo cal max")

    def run(self):
        self.avg()
        self.max()
'''
# duck-typing
def runnable(obj):
    obj.run()
'''

class Dss(IDisplay):
    def __init__(self, ctx):
        IDisplay.__init__(self)
        self.ctx = ctx

    def run(self):
        print("Dss display {}".format(self.ctx))
