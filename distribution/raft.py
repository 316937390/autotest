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
NODE_ALIVE = 1
NODE_DEATH = 2
NODE_UNKNOWN = 0

# 超时
TIMEOUT_HEART_BEAT = 5
TIMEOUT_SELECTION = 3

# 心跳间隔
INTERVAL_HEART_BEAT = 1

#################################################################################################
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
    global node
    node.term += 1
    return node.term

def getCurrentTerm():
    """获取当前的term任期"""
    global node
    return node.term

def getCurrentRole():
    """获取当前节点角色"""
    global node
    return node.roleState.state

def getNodeName():
    """获取节点标识"""
    global node
    return node.nodeName

def getPeers():
    global node
    return node.peerState.keys()

class Event(object):
    """Event类"""
    def __init__(self, eventType):
        self.eventType = eventType

    def behave(self):
        raise Exception('Event behavior not implemented')

class HeartBeatTimeoutEvent(Event):
    """heartBeatTimeout事件类"""
    def __init__(self):
        super(HeartBeatTimeoutEvent, self).__init__('heartBeatTimeout')

    def behave(self):
        newTerm()
        startElection()

class SelectTimeoutEvent(Event):
    """selectTimeout事件类"""
    def __init__(self):
        super(SelectTimeoutEvent, self).__init__('selectTimeout')

    def behave(self):
        newTerm()
        startElection()

class RecvMajorVotesEvent(Event):
    """recvMajorVotes事件类"""
    def __init__(self):
        super(RecvMajorVotesEvent, self).__init__('recvMajorVotes')

    def behave(self):
        global node
        global leader
        node.determineLeader(leader)

class DiscoverLeaderEvent(Event):
    """discoverLeader事件类"""
    def __init__(self):
        super(DiscoverLeaderEvent, self).__init__('discoverLeader')

    def behave(self):
        global node
        global leader
        node.determineLeader(leader)

class NewTermEvent(Event):
    """newTerm事件类"""
    def __init__(self):
        super(NewTermEvent, self).__init__('newTerm')

    def behave(self):
        global newterm
        global node
        node.determineTerm(newterm)

class HigherTermEvent(Event):
    """higherTerm事件类"""
    def __init__(self):
        super(HigherTermEvent, self).__init__('higherTerm')

    def behave(self):
        global newterm
        global node
        node.determineTerm(newterm)

# 投票信息传输采用 RPC 协议
def RequestVoteRpc(addr, msg):
    return VoteMsg(1, VOTE_TYPE_ACK, 'nodeA')

def requestVote(peers):
    # 首先给自己投票
    votes = {}
    votes[getNodeName()] = 1
    termId = getCurrentTerm()
    msgType = VOTE_TYPE_REQ
    content = 'vote for me'
    voteMsg = VoteMsg(termId, msgType, content)
    for _, p in enumerate(peers):
        resp, err = RequestVoteRpc(p, voteMsg)
        if err != None:
            print('RequestVoteRpc Error!')
            continue
        if resp.term > termId:
            # 触发 newTerm 事件
            global newterm
            global node
            newterm = resp.term
            e = NewTermEvent()
            node.roleState.next(e)
            e.behave()
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
    global leader
    global node
    leader, flag = findLeader(votes, peers):
    if flag:
        # 选举成功，可触发 recvMajorVotes 事件
        if getNodeName() == leader:
            e = RecvMajorVotesEvent()
            node.roleState.next(e)
            e.behave()
    else:
        # 选举失败，重新选举
        node.determineLeader(leader)

class RoleStateMachine(object):
    """节点角色状态机"""
    def __init__(self):
        self.state = FOLLOWER

    def next(self, e):
        if self.state == FOLLOWER:
            if e.eventType == 'heartBeatTimeout':
                self.state = CANDIDATE
        elif self.state == CANDIDATE:
            if e.eventType == 'selectTimeout':
                self.state = CANDIDATE
            if e.eventType == 'recvMajorVotes':
                self.state = LEADER
            if e.eventType == 'discoverLeader':
                self.state = FOLLOWER
            if e.eventType == 'newTerm':
                self.state = FOLLOWER
        elif self.state == LEADER:
            if e.eventType == 'higherTerm':
                self.state = FOLLOWER


class Node(object):
    """节点信息"""
    def __init__(self, nodeName, peers):
        self.nodeName = nodeName
        self.roleState = RoleStateMachine()
        self.term = 0
        self.leader = ''
        self.peerState = { v:NODE_UNKNOWN for _,v in enumerate(peers) }

    def updatePeerState(self, peerName, state):
        if self.peerState.get(peerName) != None:
            self.peerState[peerName] = state

    def determineLeader(self, name):
        self.leader = name

    def determineTerm(self, term):
        self.term = term

"""
节点实例 node
参数1：该节点标识
参数2：其他节点标识列表
"""
node = Node('nodeA', ['nodeB', 'nodeC'])
leader = ''
newterm = 0

def sendHeartBeat(peerAddr, termId, roleType, msgType):
    """发送心跳消息"""
    heartBeatReq = RaftHeartBeat(termId, roleType, msgType)

def recvHeartBeat(peerAddr, heartBeatMsg):
    """处理接收的心跳信息"""
    assert isinstance(heartBeatMsg, RaftHeartBeat)
    roleState = getCurrentRole()
    termId = getCurrentTerm()
    global node
    if roleState == LEADER:
        if heartBeatMsg.term < termId:
            return
        elif heartBeatMsg.term > termId:
            # 触发 higherTerm 事件
            global newterm
            newterm = heartBeatMsg.term
            e = HigherTermEvent()
            node.roleState.next(e)
            e.behave()
            return
        elif heartBeatMsg.type == HEART_BEAT_TYPE_ACK:
            # 更新 Node peerState
            node.updatePeerState(peerAddr.name, NODE_ALIVE)

    elif roleState == FOLLOWER:
        sendHeartBeat(peerAddr, termId, roleState, HEART_BEAT_TYPE_ACK)

    elif roleState == CANDIDATE:
        if heartBeatMsg.term < termId:
            return
        elif heartBeatMsg.term > termId:
            # 触发 newTerm 事件
            global newterm
            newterm = heartBeatMsg.term
            e = NewTermEvent()
            node.roleState.next(e)
            e.behave()
            return
        elif heartBeatMsg.role == LEADER:
            # 触发 discoverLeader 事件
            global leader
            leader = peerAddr.name
            e = DiscoverLeaderEvent()
            node.roleState.next(e)
            e.behave()
            return

"""
心跳消息采用 udp 协议传输，默认端口 13066
连续 k 次心跳消息超时，则认为节点不在线
leader 向 follower 发送心跳消息
"""
