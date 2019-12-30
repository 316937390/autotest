# -*- coding: utf-8 -*-

class BaseMetrics(object):
    def __init__(self):
        self.FuncMap = {}

    def register(self, handler):
        if handler.apiName not in self.FuncMap:
            self.FuncMap[handler.apiName] = []
        self.FuncMap[handler.apiName].append(handler.func)

    def stat(self):
        print("metrics stat..")
        for k,v in self.FuncMap.items():
            for f in v:
                f()

def calculate(obj):
    obj.stat()

if __name__=='__main__':
    bm = BaseMetrics()
    calculate(bm)
