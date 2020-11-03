# -*- coding: utf-8 -*-

'''
zab协议
全局唯一标识zxid
<投票轮数，被投节点的zxid，被投节点的编号> 即(voteRound, votedZxid, votedNodeId)

zk集群的一个节点，有三种状态：
– looking   : 选举状态，当前群龙无首；
– leading   : leader才有的状态；
– following : follower才有的状态；

默认 zab 采用的算法是 fast paxos 算法。
'''


# 三种节点状态
LOOKING   =  0
LEADING   =  1
FOLLOWING =  2

class ZookeeperVoteMsg(object):
    """投票信息类"""
    def __init__(self, roundIdx, zxid, nodeId):
        self.round = roundIdx
        self.zxid = zxid
        self.node = nodeId

    def clear(self):
        self.round = None
        self.zxid = None
        self.node = None

class ZNodeStateMachine(object):
    """zk节点状态机"""
    def __init__(self):
        self.state = FOLLOWING

    def next(self, e):
        pass

class TicketBox(object):
    """票仓类"""
    def __init__(self):
        self.voteTicket = ZookeeperVoteMsg(None, None, None) # 投出的选票
        self.round = 0 # 选举轮数
        self.votes = 0 # 投票数
        self.leader = None

    def copyVote(self, ticket):
        self.voteTicket.round = ticket.round
        self.voteTicket.zxid = ticket.zxid
        self.voteTicket.node = ticket.node

    def clear(self):
        self.voteTicket.clear()
        self.round = 0
        self.votes = 0
        self.leader = None

    def vote(self, ticket):
        """收到投票"""
        global node
        if ticket.round < self.round:
            """
            丢弃
            """
            return
        elif ticket.round > self.round:
            """
            证明自己投票过期了，清空本地投票信息，
            更新投票轮数和结果为收到的内容。
            通知其他所有节点新的投票方案。
            """
            self.clear()
            self.round = ticket.round
            self.copyVote(ticket)
            self.votes = 1
            notifyPeers(ticket)
        else:
            """
            比较收到的选票和自己投出去的选票的优先级
            """
            comparePriority(ticket)
        whetherFindLeader(node)

    def comparePriority(self, ticket):
        """投票优先级：优先比较 zxid ,如果相等,再比较 node 的id,按照从大到小的顺序。"""
        if ticket.zxid > self.voteTicket.zxid:
            """更新自己的投票为对方发过来投票方案，并把投票发出去。"""
            self.copyVote(ticket)
            self.votes = 1
            notifyPeers(ticket)
        elif ticket.zxid < self.voteTicket.zxid:
            """忽略该投票"""
            return
        elif ticket.zxid == self.voteTicket.zxid:
            if ticket.node == self.voteTicket.node:
                """如果收到的优先级相等，则更新对应节点的投票。"""
                self.votes += 1
            elif ticket.node < self.voteTicket.node:
                """忽略该投票"""
                return
            elif ticket.node > self.voteTicket.node:
                """更新自己的投票为对方发过来投票方案，并把投票发出去。"""
                self.copyVote(ticket)
                self.votes = 1
                notifyPeers(ticket)

    def newRound(self):
        self.round += 1

    def determineLeader(self, nodeId):
        self.leader = nodeId

    def voteForSelf(self, d):
        """每个进入looking状态的节点，最开始投票给自己，内容为<第几轮投票，被投节点的zxid，被投节点的编号>，然后把投票消息发给其它机器。"""
        zvm = ZookeeperVoteMsg(self.round, d.zxid, d.nodeId)
        self.copyVote(zvm)
        self.votes = 1
        notifyPeers(zvm)

    def whetherFindLeader(self, d):
        """每收集到一个投票后，查看是否有节点能够达到一半以上的投票数。如果有达到，则终止投票，宣布选举结束，更新自身状态。否则继续收集投票。"""
        nodeNum = len(d.getPeers()) + 1
        threshold = nodeNum >> 1
        if self.votes > threshold:
            self.determineLeader(self.voteTicket.node)
            terminateElection()

class ZookeeperNode(object):
    """zk节点"""
    def __init__(self, idx, peers):
        self.epoch  = 0x10
        self.offset = 0x01
        self.zxid = (self.epoch << 32) | (self.offset & 0xffffffff)
        self.nodeId = idx
        self.peers = peers
        self.state = ZNodeStateMachine()
        self.ticketBox = TicketBox()

    def getPeers(self):
        return self.peers.keys()

    def newZxid(self, newEpoch = False):
        """递增的zxid顺序，保证了能够有优先级最高的节点当leader"""
        if newEpoch:
            self.epoch += 1
            self.offset = 0x01
            self.zxid = (self.epoch << 32) | (self.offset & 0xffffffff)
        else:
            self.offset += 1
            self.zxid = (self.epoch << 32) | (self.offset & 0xffffffff)
        return self.zxid

node = ZookeeperNode(5,{'nodeB':2,'nodeC':3})

def notifyPeers(msg):
    """通知其他所有节点新的投票方案"""
    assert isinstance(msg, ZookeeperVoteMsg)
    global node
    for _,p in enumerate(node.getPeers()):
        sendVoteMsg(p, msg)

def sendVoteMsg(peer, msg):
    assert isinstance(msg, ZookeeperVoteMsg)
    pass

def recvVoteMsg(peer, msg):
    assert isinstance(msg, ZookeeperVoteMsg)
    print('receive from {} vote message'.format(peer.name))
    global node
    node.ticketBox.vote(msg)


def startElection():
    """开始选举"""
    global node
    node.ticketBox.newRound()
    node.ticketBox.voteForSelf(node)

def terminateElection():
    """结束选举"""
    global node
    return node.ticketBox.leader


