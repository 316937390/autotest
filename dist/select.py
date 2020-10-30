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

# vote信息类型
VOTE_TYPE_REQ = 0
VOTE_TYPE_ACK = 1

# 节点状态
NODE_ALIVE = 0
NODE_DEATH = 1

class RaftHeartBeat(object):
	"""Raft心跳消息"""
	def __init__(self, termId, roleType, msgType):
		self.term = termId
		self.role = roleType
		self.type = msgType

class VoteMsg(object):
	"""vote消息"""
	def __init__(self, termId, msgType, content):
		self.term = termId
		self.type = msgType
		self.content = content

def newTerm():
	"""生成新的term任期"""
	return 1

def getCurrentTerm():
	"""获取当前的term任期"""
	return 0

def getCurrentRole():
	"""获取当前节点角色"""
	return LEADER

def getNodeName():
	"""获取节点标识"""
	return "Node1"

def getPeers():
	return []


def requestVote(peers):
	# 首先给自己投票
	votes = {}
	votes[getNodeName()] = 1
	termId = getCurrentTerm()
	msgType = VOTE_TYPE_REQ
	content = 'vote for me'
	voteMsg = VoteMsg(termId, msgType, content)
	for _, p in enumerate(peers):
		resp = RequestVoteRpc(p, voteMsg)
		if resp.term > termId:
			# 触发 newTerm 事件
			break
		elif resp.term < termId:
			continue
		else:
			if resp.type == VOTE_TYPE_ACK:
				nodeName = resp.content # 被选为leader的节点标识
				if votes.get(nodeName) != None:
					votes[nodeName] += 1
				else:
					votes[nodeName] = 1
			else:
				continue
	return votes

def findLeader(votes, peers):
	threshold = (len(peers) + 1) >> 1
	for k,v in votes.items():
		if v > threshold:
			return k, True
	return None, False

def startElection():
	"""leader选举"""
	peers = getPeers()
	votes = requestVote(peers)
	leader, flag = findLeader(votes, peers):
	if flag:
		# 选举成功，触发 recvMajorVotes 事件
		pass
	else:
		# 选举失败，重新选举
		pass


def sendHeartBeat(peerAddr, termId, roleType, msgType):
	"""发送心跳消息"""
	heartBeatReq = RaftHeartBeat(termId, roleType, msgType)

def recvHeartBeat(peerAddr, heartBeatMsg):
	"""处理接收的心跳信息"""
	assert isinstance(heartBeatMsg, RaftHeartBeat)
	roleState = getCurrentRole()
	termId = getCurrentTerm()
	if roleState == LEADER:
		if heartBeatMsg.term > termId:
			# 触发 higherTerm 事件
			return
		elif heartBeatMsg.type == HEART_BEAT_TYPE_ACK:
			pass
	elif roleState == FOLLOWER:
		sendHeartBeat(peerAddr, termId, roleState, HEART_BEAT_TYPE_ACK)
	elif roleState == CANDIDATE:
		if heartBeatMsg.role == LEADER:
			# 触发 discoverLeader 事件
			sendHeartBeat(peerAddr, termId, getCurrentRole(), HEART_BEAT_TYPE_ACK)
			return
		if heartBeatMsg.term > termId:
			# 触发 newTerm 事件
			return



class RoleStateMachine(object):
	"""节点角色状态机"""
    def __init__(self):
    	self.state = FOLLOWER

    def next(self, event):
    	if self.state == FOLLOWER:
    		if event == 'timeout':
    			self.state = CANDIDATE
    			newTerm()
    			startElection()
    	elif self.state == CANDIDATE:
    		if event == 'timeout':
    			self.state = CANDIDATE
    			newTerm()
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


class Node(object):
	"""节点信息"""
	def __init__(self, nodeName, peers):
		self.nodeName = nodeName
		self.roleState = RoleStateMachine()
		self.term = 0
		self.peers = peers


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
