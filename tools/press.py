# -*- coding: utf-8 -*-

from threading import Timer
from multiprocessing import Process
import configparser
import getopt
import sys
import os
import re
import time
import grpc
import json
import random,string
import traceback
import math
import statistics

current_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_dir)
sys.path.append(current_dir+'/protocol/grpc')
sys.path.append(current_dir+'/protocol/thrift/advanced_search')

from protocol.grpc.juno_pb2 import JunoRequest,JunoResponse,SErrorCode
from protocol.grpc.juno_pb2_grpc import JunoServiceStub
from protocol.thrift.advanced_search import RecommendSrv
from protocol.thrift.advanced_search.constants import *
from protocol.thrift.advanced_search.ttypes import QueryParam,QueryResult
from thrift.protocol import TCompactProtocol
from thrift.transport import TSocket
from contextlib import closing



class AdServerClient(object):
    """adServer客户端"""
    def __init__(self, ip='localhost', port=9099):
        socket = TSocket.TSocket(ip, port)
        socket.setTimeout(5000)
        self._transport = TTransport.TBufferedTransport(socket)
        self._protocol = TCompactProtocol.TCompactProtocol(self._transport)
        self._client = RecommendSrv.Client(self._protocol)

    def get(self):
        self._transport.open()
        return self._client

    def close(self):
        self._transport.close()

class ConfigParam(object):
    """参数对象"""
    def __init__(self, parallelNum=None,\
                totalReq=None,\
                totalQPS=None,\
                transProtocol=None,\
                dstAddr=None,\
                inputSource=None):
        self.parallelNum = parallelNum
        self.totalReq = totalReq
        self.totalQPS = totalQPS
        self.transProtocol = transProtocol
        self.dstAddr = dstAddr
        self.inputSource = inputSource

class ConfFileParser(object):
    """配置文件解析类"""
    def __init__(self, filePath):
        self.filePath = filePath
    def parse(self):
        configParam = ConfigParam()
        return configParam

class CliParamParser(object):
    """命令行解析类"""
    def __init__(self,argv):
        self.argv = argv
    def parse(self):
        configParam = ConfigParam()
        opts, args = getopt.getopt(self.argv,"t:q:n:p:d:i:",["protocol=","dst=","input="])
        for opt, value in opts:
            if opt == '-t':
                configParam.parallelNum = int(value)
            elif opt == '-q':
                configParam.totalQPS = int(value)
            elif opt == '-n':
                configParam.totalReq = int(value)
            elif opt in ['-p','--protocol']:
                configParam.transProtocol = str(value)
            elif opt in ['-d','--dst']:
                configParam.dstAddr = str(value)
            elif opt in ['-i','--input']:
                configParam.inputSource = str(value)
        return configParam


class PerfStats(object):
    """性能数据统计类"""
    def __init__(self):
        self.elapsedTimes = []
        self.reqTotal = 0
        self.reqSuccess = 0
        self.reqError = 0
        self.reqTimeout = 0

    def sort(self):
        self.elapsedTimes.sort()

    def dumps(self, fileName=None):
        strLine = json.dumps(self.__dict__)
        with open('./{}.stat'.format(fileName), 'w') as f:
            f.write(strLine)


class DataStore(object):
    """数据源类"""
    def __init__(self):
        self.buffer = []
        self.length = 0
        self.curse = 0

    def put(self, data):
        self.buffer.append(data)
        self.length = self.length + 1

    def get_r(self):
        assert self.length != 0
        data = self.buffer[(self.curse % self.length)]
        self.curse = self.curse + 1
        return data

    def get(self):
        if self.curse >= self.length:
            return None
        data = self.buffer[self.curse]
        self.curse = self.curse + 1
        return data

    def offset(self, index):
        assert index >= 0
        assert index < self.length
        self.curse = index

    def reset(self):
        self.curse = 0

class DataCollector(object):
    """数据采集类"""
    def __init__(self, dataStores=None, dataParser=None):
        self.dataStores = dataStores
        self.dataParser = dataParser

    def collect(self):
        raise Exception('collect not implemented')
        
class DataParser(object):
    """数据解析类"""
    def __init__(self):
        pass

    def parse(self, rawData):
        raise Exception('parse not implemented')

class MockDataParser(DataParser):
    """MockDataParser"""
    def __init__(self):
        super(MockDataParser, self).__init__()
    def parse(self, rawData):
        jr = JunoRequest()
        #jr.requestId = "".join(random.sample(string.digits + string.ascii_letters,16))
        #jr.clientLable = "as"
        #jr.Exchange = "as"
        return jr

class MockAsParser(DataParser):
    """MockAsParser"""
    def __init__(self):
        super(MockAsParser, self).__init__()
    def parse(self, rawData):
        cmd = json.loads('{"orientation": 1, "countryCode": "TEST", "requestType": 7, "ip": "211.147.253.235", "devId": "", "GP_version": "", "testMode": 666, "mnc": "", "appVersionCode": "", "deviceModel": "", "recallADNOffer": 1, "ifSupportBigTemplate": 1, "platform": 1, "requestId": "VXczMx5FJAu3OQjS", "unitId": 3620090, "lowDevice": false, "adTypeStr": "rewarded_video", "adNum": 1, "randNum": 102, "timestamp": 1601460787, "osVersionCodeV2": 6000000, "mcc": "", "mac": "", "idfa": "", "offset": 2, "appId": 9099, "imei": "", "networkType": 9, "osVersion": "6.0.0", "trueNum": 1, "sdkVersion": "mal_10.6.0", "language": "", "packageName": "", "unitSize": "480x320", "apiVersion": 1090000, "screenSize": "1280x600", "adnServerIp": "54.251.108.183", "ifSupportSeperateCreative": 3, "appVersionName": ""}')
        queryParam = QueryParam(**cmd)
        #queryParam = QueryParam()
        return queryParam

class localFileDataCollector(DataCollector):
    """本地文件数据采集类"""
    def __init__(self, filePath=None, dataStores=None, fileParser=None):
        super(localFileDataCollector, self).__init__(dataStores, fileParser)
        self.filePath = filePath
    def collect(self):
        with open(self.filePath, 'r') as f:
            lineNo = 0
            storesNo = len(self.dataStores.keys())
            assert storesNo != 0
            for line in f:
                slot = lineNo % storesNo
                dataElement = self.__process(line)
                self.dataStores[slot].put(dataElement)
                lineNo = lineNo + 1
    def __process(self, line):
        result = self.dataParser.parse(line)
        return result


class RepeatingTimer(Timer):
    def run(self):
        while not self.finished.is_set():
            if not self.function(*self.args, **self.kwargs):
                self.finished.set()
                continue
            self.finished.wait(self.interval)

class Worker(object):
    """压测工作对象"""
    def __init__(self, dataSource=None, perfStats=None, reqNum=None, reqQPS=None, remoteUri=None):
        self.dataSource = dataSource
        self.perfStats = perfStats
        self.reqNum = reqNum
        self.reqQPS = reqQPS
        self.remoteUri = remoteUri
        

# 支持grpc协议的压测客户端 for junoServer
def junoClientSend(**kwargs):
    #print('{},{}'.format(kwargs, os.getpid()))
    Flag = True
    for i in range(kwargs['reqQPS']):
        if kwargs['perfStats'].reqTotal >= kwargs['reqNum']:
            Flag = False
            break
        jr = kwargs['dataSource'].get_r()
        if not jr:
            Flag = False
            break
        startTimestamp = time.time()
        try:
            with grpc.insecure_channel(kwargs['remoteUri']) as channel:
                stub = JunoServiceStub(channel)
                resp = stub.junoSearch(jr)
            rtt = (time.time() - startTimestamp) * 1000 # 毫秒
            kwargs['perfStats'].reqSuccess += 1
            kwargs['perfStats'].elapsedTimes.append(rtt)
            if resp.JunoStatus.errorCode == SErrorCode.kFail:
                kwargs['perfStats'].reqError += 1
        except Exception as err:
            print('error: {}'.format(err))
            kwargs['perfStats'].reqError += 1
        finally:
            kwargs['perfStats'].reqTotal += 1
    return Flag

# 支持thrift协议的压测客户端
def thriftClientSend(**kwargs):
    Flag = True
    for i in range(kwargs['reqQPS']):
        if kwargs['perfStats'].reqTotal >= kwargs['reqNum']:
            Flag = False
            break
        qp = kwargs['dataSource'].get_r()
        if not qp:
            Flag = False
            break
        startTimestamp = time.time()
        addr = kwargs['remoteUri'].split(':')[0]
        port = int(kwargs['remoteUri'].split(':')[1])
        try:
            with closing(AdServerClient(addr, port)) as asClient:
                ac = asClient.get()
                resp = ac.getCampaigns(qp)
            rtt = (time.time() - startTimestamp) * 1000 # 毫秒
            kwargs['perfStats'].reqSuccess += 1
            kwargs['perfStats'].elapsedTimes.append(rtt)
        except Exception as err:
            print('error: {}'.format(err))
            exc_type, value, tb = sys.exc_info()
            print('{}'.format(''.join(traceback.format_tb(tb))))
            kwargs['perfStats'].reqError += 1
        finally:
            kwargs['perfStats'].reqTotal += 1
    return Flag

# Worker进程启动
def procStart(worker=None):
    assert worker != None
    t = RepeatingTimer(interval=1.0-1.0/(1+math.pow(math.e,-math.log10(worker.reqQPS))), function=junoClientSend, args=[], kwargs=worker.__dict__)
    t.start()
    # ----> python3.6(bug) 在此处解决，若使用python3.8则不需要此处的 while 语句
    while not t.finished.is_set():
        continue
    # <---- end
    #print('{}--->{}'.format(worker.perfStats.__dict__, os.getpid()))
    worker.perfStats.dumps(os.getpid())

# Worker进程启动
def procThriftStart(worker=None):
    assert worker != None
    t = RepeatingTimer(interval=math.cos(math.pi/2-1.0/worker.reqQPS), function=thriftClientSend, args=[], kwargs=worker.__dict__)
    t.start()
    # ----> python3.6(bug) 在此处解决，若使用python3.8则不需要此处的 while 语句
    while not t.finished.is_set():
        continue
    # <---- end
    #print('{}--->{}'.format(worker.perfStats.__dict__, os.getpid()))
    worker.perfStats.dumps(os.getpid())

class Scheduler(object):
    """调度器"""
    ProtoCollector = {'grpc':MockDataParser(),'thrift':MockAsParser()}
    ProtoWorkerFunc = {'grpc':procStart,'thrift':procThriftStart}

    def __init__(self, paramParser=None):
        self.configParser = paramParser
        self.configObj = None  #压测参数对象
        self.dataStores = None #压测数据池
        self.procSeq = []      #压测进程池
        self.workersMap = {}   #压测对象池
        self.startTime = None  #压测开始时间戳
        self.endTime = None    #压测结束时间戳

    def parseConfig(self):
        self.configObj = self.configParser.parse()
        return self.configObj

    def initiate(self):
        # 采集压测数据
        self.dataStores = { i:DataStore() for i in range(self.configObj.parallelNum)}
        collector = localFileDataCollector(self.configObj.inputSource,\
                                           self.dataStores,\
                                           Scheduler.ProtoCollector[self.configObj.transProtocol])
        collector.collect()
        # 构建压测工作对象
        baseQPS = int(self.configObj.totalQPS / self.configObj.parallelNum)
        modQPS = int(self.configObj.totalQPS % self.configObj.parallelNum)
        if modQPS != 0:
            modQPS = baseQPS + modQPS
        else:
            modQPS = baseQPS
        baseNum = int(self.configObj.totalReq / self.configObj.parallelNum)
        modNum = int(self.configObj.totalReq % self.configObj.parallelNum)
        if modNum != 0:
            modNum = baseNum + modNum
        else:
            modNum = baseNum
        for i in range(self.configObj.parallelNum):
            if i == self.configObj.parallelNum - 1:
                self.workersMap[i] = Worker(self.dataStores[i],\
                                   PerfStats(),\
                                   modNum,\
                                   modQPS,\
                                   self.configObj.dstAddr)
            else:
                self.workersMap[i] = Worker(self.dataStores[i],\
                                   PerfStats(),\
                                   baseNum,\
                                   baseQPS,\
                                   self.configObj.dstAddr)
    # 开始并等待压测结束
    def start(self):
        for index, worker in self.workersMap.items():
            p = Process(target=Scheduler.ProtoWorkerFunc[self.configObj.transProtocol],\
                        args=(worker,))
            self.procSeq.append(p)
        self.startTime = time.time() # 记录压测启动时间戳
        for _, proc in enumerate(self.procSeq):
            proc.start()
        for _, proc in enumerate(self.procSeq):
            proc.join()
        self.endTime = time.time() # 记录压测结束时间戳


    # 统计压测数据
    def report(self):
        reqNum = 0
        errNum = 0
        sucNum = 0
        def generator():
            nonlocal reqNum
            nonlocal errNum
            nonlocal sucNum
            fs = os.listdir('./')
            for f in fs:
                if os.path.isfile(os.path.join('./',f)):
                    if re.search('.stat$', f):
                        with open(os.path.join('./',f), 'r') as rf:
                            for line in rf:
                                line = line.strip()
                                if line == '':
                                    continue
                                perfData = json.loads(line)
                                reqNum += perfData['reqTotal']
                                errNum += perfData['reqError']
                                sucNum += perfData['reqSuccess']
                                for i in perfData['elapsedTimes']:
                                    yield i
        sortedTimeSeq = sorted(generator())
        def percentile(xth):
            index = math.floor(len(sortedTimeSeq) * xth)
            return sortedTimeSeq[int(index)-1]
        fifty_th = statistics.median(sortedTimeSeq)
        seventy_th = percentile(0.70)
        eighty_th = percentile(0.80)
        ninety_th = percentile(0.90)
        ninetyfive_th = percentile(0.95)
        ninetynine_th = percentile(0.99)
        minTime = sortedTimeSeq[0]
        maxTime = sortedTimeSeq[-1]
        avgTime = statistics.mean(sortedTimeSeq)
        stdTime = statistics.stdev(sortedTimeSeq, xbar=avgTime)
        def consoleOutPut():
            print('\n[Stats Processing...]\n')
            timeSpanSeconds = self.endTime - self.startTime
            print('\tTime Use(sec): {:.3f}'.format(timeSpanSeconds))
            print('\tTotal Requests:{}'.format(reqNum))
            print('\tActual QPS:{:.3f}'.format(reqNum / timeSpanSeconds))
            print('\tTotal Errors:{}'.format(errNum))
            print('\tTotal Success:{}'.format(sucNum))
            print('\tElapsed Time Distribution(ms):')
            print('\t\tmin:{:.3f}, max:{:.3f}, avg:{:.3f}, std:{:.3f}'.format(minTime, maxTime, avgTime, stdTime))
            print('\t\t50th:{:.3f}'.format(fifty_th))
            print('\t\t70th:{:.3f}'.format(seventy_th))
            print('\t\t80th:{:.3f}'.format(eighty_th))
            print('\t\t90th:{:.3f}'.format(ninety_th))
            print('\t\t95th:{:.3f}'.format(ninetyfive_th))
            print('\t\t99th:{:.3f}'.format(ninetynine_th))
        consoleOutPut()
        # 50% 70% 80% 90% 95% 99% avg min max std
        # timeSpan reqNum qps errs




#######################################################################
def hello():
     print("hello, world")
     return True

t = RepeatingTimer(1.0, hello)
t.start()
t.cancel()


s = Scheduler(paramParser=CliParamParser(sys.argv[1:]))
cf = s.parseConfig()
print(cf.__dict__)
s.initiate()
s.start()
s.report()



