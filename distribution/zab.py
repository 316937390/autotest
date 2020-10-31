# -*- coding: utf-8 -*-

'''
zab协议
全局唯一标识zxid
<投票轮数，被投节点的zxid，被投节点的编号>
'''
zxid = (epoch << 32) | (incId & 0xffffffff)
(voteRound, votedZxid, votedNodeId)

class ZookeeperVoteMsg(object):
	"""投票信息类"""
	def __init__(self, roundIdx, zxid, nodeId):
		self.round = roundIdx
		self.zxid = zxid
		self.node = nodeId

class TicketBox(object):
	"""票仓类"""
	def __init__(self):
		self.box = {}
		self.round = 0
		self.leader = 0


	def leader(self):
		return self.leader

	def vote(self, ticket):
		pass
						

def recvVoteMsg(peer, msg):
	assert isinstance(msg, ZookeeperVoteMsg)