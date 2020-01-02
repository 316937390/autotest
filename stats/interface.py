# -*- coding: utf-8 -*-


class IFeeder(object):
    def __init__(self):
        pass

    def put(self, data):
        raise Exception("Feeder no put")

    def get(self):
        raise Exception("Feeder no get")

class ICalculate(object):
    def __init__(self):
        pass

    def run(self):
        raise Exception("no exec")

class IDisplay(object):
    def __init__(self):
        pass

    def run(self):
        raise Exception("no display")
