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
        global node
        node.newTerm()
        startElection()

class SelectTimeoutEvent(Event):
    """selectTimeout事件类"""
    def __init__(self):
        super(SelectTimeoutEvent, self).__init__('selectTimeout')

    def behave(self):
        global node
        node.newTerm()
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
    """
    拥有最新的已提交的log entry的Follower才有资格成为Leader。
    其他节点收到消息时，如果发现自己的日志比请求中携带的更新，则拒绝该投票。
    日志比较的原则是，如果本地的最后一条log entry的term更大，则term大的更新，如果term一样大，则log index更大的更新。
    """
    assert msg.type == VOTE_TYPE_REQ
    global node
    cs = msg.content.split(',')
    logIdx = cs[1]
    termIdx = cs[2]
    if node.logEntries.tail.logTerm > termIdx:
        return (VoteMsg(node.getCurrentTerm(), VOTE_TYPE_ACK, node.getNodeName()), None)
    elif node.logEntries.tail.logTerm < termIdx:
        return (VoteMsg(node.getCurrentTerm(), VOTE_TYPE_ACK, addr.name), None)
    else:
        if node.logEntries.tail.logIndex > logIdx:
            return (VoteMsg(node.getCurrentTerm(), VOTE_TYPE_ACK, node.getNodeName()), None)
        elif node.logEntries.tail.logIndex < logIdx:
            return (VoteMsg(node.getCurrentTerm(), VOTE_TYPE_ACK, addr.name), None)
        else:
            # 选谁都行
            return (VoteMsg(node.getCurrentTerm(), VOTE_TYPE_ACK, 'nodeA'), None)

def requestVote(peers):
    # 首先给自己投票
    global node
    votes = {}
    votes[node.getNodeName()] = 1
    termId = node.getCurrentTerm()
    msgType = VOTE_TYPE_REQ
    # Candidate在发送RequestVote RPC时，要带上自己的最后一条日志的term和log index
    content = 'vote for me,{},{}'.format(node.logEntries.tail.logIndex, node.logEntries.tail.logTerm)
    voteMsg = VoteMsg(termId, msgType, content)
    for _, p in enumerate(peers):
        resp, err = RequestVoteRpc(p, voteMsg)
        if err != None:
            print('RequestVoteRpc Error!')
            continue
        if resp.term > termId:
            # 触发 newTerm 事件
            global newterm
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
    global leader
    global node
    peers = node.getPeers()
    votes = requestVote(peers)
    leader, flag = findLeader(votes, peers):
    if flag:
        # 选举成功，可触发 recvMajorVotes 事件
        if node.getNodeName() == leader:
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
        self.nodeName = nodeName            # 节点标识
        self.roleState = RoleStateMachine() # 角色
        self.term = 0             # 任期
        self.leader = None        # 主节点
        self.logEntries = Log()   # 日志条目列表
        self.committedLogEntry = None   # 最后一条已提交的日志条目
        self.hasCopiedLogEntry = []     # 复制成功的日志条目列表
        self.peerState = { v:NODE_UNKNOWN for _,v in enumerate(peers) }

    def updatePeerState(self, peerName, state):
        if self.peerState.get(peerName) != None:
            self.peerState[peerName] = state

    def determineLeader(self, name):
        """设置leader节点"""
        self.leader = name

    def determineTerm(self, term):
        """设置term任期"""
        self.term = term

    def newTerm(self):
        """生成新的term任期"""
        self.term += 1
        return self.term

    def getCurrentTerm(self):
        """获取当前的term任期"""
        return self.term

    def getCurrentRole(self):
        """获取当前节点角色"""
        return self.roleState.state

    def getNodeName(self):
        """获取当前节点标识"""
        return self.nodeName

    def getPeers(self):
        """获取peer节点列表"""
        return self.peerState.keys()

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
    global node
    roleState = node.getCurrentRole()
    termId = node.getCurrentTerm()
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
leader 向 follower 周期性发送心跳消息
"""


"""
日志同步
Leader把客户端请求作为日志条目（Log entries）加入到它的日志中，然后向其他服务器发起 AppendEntriesRPC 复制日志条目。
日志由有序编号（log index）的日志条目组成。每个日志条目包含它被创建时的 term 任期。
"""
class LogEntry(object):
    """日志条目"""
    def __init__(self, index, term):
        self.logIndex = index
        self.logTerm = term
        self.prev = None
        self.next = None

    def equal(self, l):
        """判断两个日志条目是否相同"""
        if l == None:
            return False
        if self.logIndex == l.logIndex and self.logTerm == l.logTerm:
            return True
        else:
            return False

class Log(object):
    """日志，采用链表实现"""
    def __init__(self):
        self.head = None
        self.tail = None

    def append(self, logEntry):
        if self.tail != None:
            self.tail.next = logEntry
            logEntry.prev = self.tail
            self.tail = logEntry
        else:
            self.head = logEntry
            self.tail = logEntry

def AppendEntriesRPC(prevLogEntry, newLogEntry):
    """
    简单的一致性检查：
      当发送一个 AppendEntries RPC 时，Leader会把新日志条目紧接着之前条目的log index和term都包含在里面。
      如果Follower没有在它的日志中找到log index和term都相同的日志，它就会拒绝新的日志条目。
    """
    global node
    log = node.logEntries
    if prevLogEntry == None:
        log.append(newLogEntry)
        return True
    cur = log.tail
    while cur:
        if cur.logIndex == prevLogEntry.logIndex and cur.logTerm == prevLogEntry.logTerm:
            break
        else:
            cur = cur.prev
    if cur == None:
        #raise Exception('refuse AppendEntriesRPC new log entries')
        return False
    """
    Leader通过强制Followers复制它的日志来处理日志的不一致，Followers上的不一致的日志会被Leader的日志覆盖。
    Leader需要找到Followers同它的日志一致的地方，然后覆盖Followers在该位置之后的条目。
    Leader会从后往前试，每次AppendEntries失败后尝试前一个日志条目，直到成功找到与每个Follower的日志一致位点，然后向后逐条覆盖Followers在该位置之后的条目。
    """
    log.tail = cur
    log.append(newLogEntry)
    return True

def newLogEntry(l):
    assert isinstance(l, LogEntry)
    return LogEntry(l.logIndex, l.logTerm)

def copyEntries(peers, newLog):
    """
    Leader把客户端请求作为日志条目（Log entries）加入到它的日志中，
    然后向Followers发起 AppendEntriesRPC 复制日志条目。
    """
    global node
    log = node.logEntries
    log.append(newLog)
    suc = 0
    threshold = len(peers) >> 1
    for _,p in enumerate(peers):
        if AppendEntriesRPC(log.tail.prev, newLogEntry(newLog)):
            suc += 1
            continue
        else:
            """
            每次AppendEntries失败后尝试前一个日志条目，直到成功找到与每个Follower的日志一致位点，
            然后向后逐条覆盖Followers在该位置之后的条目。
            """
            curLogEntry  = log.tail.prev
            while curLogEntry:
                if curLogEntry.prev == None:
                    curLogEntry = None
                    break
                if not AppendEntriesRPC(curLogEntry.prev, newLogEntry(curLogEntry)):
                    curLogEntry = curLogEntry.prev
                    continue
                else:
                    break
            if curLogEntry == None:
                """
                当Leader要发给某个日志落后太多的Follower的log entry被丢弃，Leader会将snapshot发给Follower。
                """
                pass
            else:
                while curLogEntry.next:
                    AppendEntriesRPC(curLogEntry, newLogEntry(curLogEntry.next))
                    curLogEntry = curLogEntry.next
                suc += 1

    if suc > threshold:
        node.hasCopiedLogEntry.append(log.tail)
        return True
    else:
        return False

def commitLogEntries(peers):
    """Leader向Followers发起提交日志"""
    global node
    assert len(node.hasCopiedLogEntry) != 0
    log = node.logEntries
    cur = log.head
    commitIndex = -1
    if node.committedLogEntry != None:
        cur = node.committedLogEntry
        commitIndex = node.committedLogEntry.logIndex
    """
    Leader只能推进commit index来提交当前term的已经复制到大多数服务器上的日志，
    旧term日志的提交要等到提交当前term的日志来间接提交（log index 小于 commit index的日志被间接提交）。
    之所以要这样，是因为可能会出现已提交的日志又被覆盖的情况。
    """
    while cur:
        if cur.logTerm == node.getCurrentTerm():
            if cur.logIndex > commitIndex and \
            cur.logIndex in [ v.logIndex for _,v in enumerate(node.hasCopiedLogEntry)]:
                for _,p in enumerate(peers):
                    CommitLogRPC(newLogEntry(cur))
                node.committedLogEntry = cur
                commitIndex = cur.logIndex
        cur = cur.next

def CommitLogRPC(logEntry):
    """日志提交RPC"""
    global node
    log = node.logEntries
    cur = log.head
    commitIndex = -1
    if node.committedLogEntry != None:
        cur = node.committedLogEntry
        commitIndex = node.committedLogEntry.logIndex
    while cur:
        if cur.logIndex > commitIndex and cur.logIndex <= logEntry.logIndex:
            node.committedLogEntry = cur
            commitIndex = cur.logIndex
        cur = cur.next



"""
日志压缩
在实际的系统中，不能让日志无限增长，否则系统重启时需要花很长的时间进行回放，从而影响可用性。
Raft采用对整个系统进行snapshot来解决，snapshot之前的日志都可以丢弃。

每个副本独立的对自己的系统状态进行snapshot，并且只能对已经提交的日志记录进行snapshot。
Snapshot中包含以下内容：
- 日志元数据。最后一条已提交的log entry的log index和term。
  这两个值在snapshot之后的第一条log entry的AppendEntries RPC的完整性检查的时候会被用上。
- 系统当前状态。

当Leader要发给某个日志落后太多的Follower的log entry被丢弃，Leader会将snapshot发给Follower。
或者当新加进一台机器时，Leader也会发送snapshot给它。发送snapshot使用InstalledSnapshot RPC。

推荐当日志达到某个固定的大小做一次snapshot。
"""
class SnapShot(object):
    """日志压缩快照类"""
    def __init__(self, committedLogEntry, nodeState):
        self.logMeta = {'logIndex':committedLogEntry.logIndex, "logTerm":committedLogEntry.logTerm}
        self.curState = nodeState

def copyFromNodeState(state):
    """加载snapshot的系统状态，来更新当前节点的系统状态"""
    assert isinstance(state, dict)
    global node
    for k,v in state.items():
        if hasattr(node,k):
            setattr(node,k,v)

def InstalledSnapshotRPC(snapshot):
    """Leader将snapshot发给Follower"""
    assert isinstance(snapshot, SnapShot)
    global node
    node.committedLogEntry = LogEntry(snapshot.logMeta["logIndex"], snapshot.logMeta["logTerm"])
    copyFromNodeState(snapshot.curState)


