# -*- coding: utf-8 -*-
import example


class BaseHandler(object):
    def __init__(self, api, e):
        self.apiName = api
        self.executor = e

class BaseMetrics(object):
    def __init__(self):
        self.FuncMap = {}

    def register(self, handler):
        if handler.apiName not in self.FuncMap:
            self.FuncMap[handler.apiName] = []
        self.FuncMap[handler.apiName].append(handler.executor)

    def stat(self):
        print("metrics stat..")
        for k,v in self.FuncMap.items():
            print("{}->".format(k))
            for e in v:
                '''example.runnable(e)'''
                e.run()

if __name__=='__main__':
    bm = BaseMetrics()
    foo = example.Foo(None)
    ds  = example.Dss(None)
    hdl = BaseHandler("/login",foo)
    bm.register(hdl)
    hdlx = BaseHandler("/login",ds)
    bm.register(hdlx)
    bm.stat()
