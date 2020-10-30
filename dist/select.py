# -*- coding: utf-8 -*-

'''
raft协议
'''
# 三种角色
LEADER = 0
FOLLOWER = 1
CANDIDATE = 2

# heartbeat心跳消息类型
HEART_BEAT_TYPE_REQ = 1
HEART_BEAT_TYPE_ACK = 2

class RoleStateMachine(object):
	"""节点角色状态机"""
    def __init__(self):
    	self.state = FOLLOWER
    	self.term = 0

    def next(self, event):
    	if self.state == FOLLOWER:
    		if event == 'timeout':
    			self.state = CANDIDATE
    			self.term += 1
    			startElection()
    	elif self.state == CANDIDATE:
    		if event == 'timeout':
    			self.state = CANDIDATE
    			self.term += 1
    			startElection()
    		if event == 'recvMajorVotes':
    			self.state = LEADER
    		if event == 'discoverLeader':
    			self.state = FOLLOWER
    		if event == 'newTerm':
    			self.state = FOLLOWER
    	elif self.state == LEADER:
    		if event == 'higherTerm':
    			self.state = FOLLOWER

class RaftHeartBeat(object):
	"""Raft心跳"""
	def __init__(self, termId, roleType, msgType):
		self.term = termId
		self.role = roleType
		self.type = msgType


'''
zab协议
全局唯一标识zxid
<投票轮数，被投节点的zxid，被投节点的编号>
'''
zxid = (epoch << 32) | (incId & 0xffffffff)
(voteRound, votedZxid, votedNodeId)

class VoteMsg(object):
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
	assert isinstance(msg, VoteMsg)
