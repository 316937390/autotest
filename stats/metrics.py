# -*- coding: utf-8 -*-
import example


class BaseHandler(object):
    def __init__(self, api, e):
        self.apiName = api
        self.executor = e

class BaseMetricsProc(object):
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
    bm = BaseMetricsProc()
    ctx = "ctx"
    foo = example.Foo(None, ctx)
    ds  = example.Dss(ctx)
    hdl = BaseHandler("/login",foo)
    bm.register(hdl)
    hdlx = BaseHandler("/login",ds)
    bm.register(hdlx)
    bm.stat()
