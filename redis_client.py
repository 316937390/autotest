# -*- coding: utf-8 -*-

import frequency_pb2
import time
import redis
from rediscluster import RedisCluster

fc = frequency_pb2.RedisFrequency()

fcInfo = fc.FrequencyInfo.add()
fcInfo.adType = 297
fcInfo.businessType = 1
fcInfo.usersActivation = 1
fcInfo.timeStamp = 5000
fcInfo.timeStampList.extend([10,4])

def iterFc(fc):
    for f in fc.FrequencyInfo:
        print(f.adType)
        print(f.businessType)
        print(f.usersActivation)
        print(f.timeStamp)
        print(f.timeStampList)

iterFc(fc)

proto_str = fc.SerializeToString()
print(proto_str)

client = redis.Redis('192.168.1.245', 7002)
nodes = [{"host": "192.168.1.245", "port": "7000"},\
{"host": "192.168.1.245", "port": "7001"},\
{"host": "192.168.1.245", "port": "7002"},\
{"host": "192.168.1.245", "port": "7003"},\
{"host": "192.168.1.245", "port": "7004"},\
{"host": "192.168.1.245", "port": "7005"}]
#client = RedisCluster(startup_nodes=nodes, decode_responses=True)

client.hset('5c42b0344e5ca11e146124a427b25e72','com.servertest-380135_1',proto_str)
print('redis hget:{}'.format(client.hget('5c42b0344e5ca11e146124a427b25e72','com.servertest-380135_1')))
start = time.time()
redis_resp = client.hget('5c42b0344e5ca11e146124a427b25e72','com.servertest-380135_1')
end = time.time()
print('redis hget timespan:{}'.format(end-start))
fp = frequency_pb2.RedisFrequency()
fp.ParseFromString(redis_resp)
iterFc(fp)
#client.hdel('5c42b0344e5ca11e146124a427b25e72','com.servertest-380135_1')
#print(client.hget('5c42b0344e5ca11e146124a427b25e72','com.servertest-380135_1'))

