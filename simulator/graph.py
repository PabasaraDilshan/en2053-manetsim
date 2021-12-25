from .node import Node
from .packet import Packet, PKT_TYPE
import random
import copy


class Graph:
    def __init__(self):
        """
            nodes : list of nodes in the network
        """
        self.nodes = []
        self.count = 0
        self.buffer = {}

    def add_node(self, x, y, range=100):
        """ 
            Add a node to the network
            Args:
                x: x-coordinate of the node
                y: y-coordinate of the node
                range: maximum transmision range
        """
        self.nodes.append(Node(str(self.count), x, y, range))
        self.count += 1

    def move_nodes(self, dynamic=False):
        """
            Move nodes within the network
            if dynamic is False a stationary network is implemented
            if dynamic is True move_nodes based on deviations derived from a Gaussian distribution
        """
        if dynamic == False:
            return
        for n in self.nodes:
            dx = min(40, random.gauss(0, 20))
            dy = min(40, random.gauss(0, 20))
            dx = max(-40, dx)
            dy = max(-40, dy)
            n.x += int(dx)
            n.y += int(dy)

    def get_dist(self, n1, n2):
        """
            Args:
                n1: Node 1
                n2: Node 2
            Returns: The ecludean distance between the nodes
        """
        return ((n1.x - n2.x) ** 2 + (n1.y - n2.y) ** 2) ** 0.5

    def add_neighbors(self, ):
        """
            Update the neighbors of each node based on the distances
        """
        for n1 in self.nodes:
            n1.adjacent_nodes = {}
            for n2 in self.nodes:
                if n1 == n2:
                    continue
                if self.get_dist(n1, n2) < n1.range:
                    n1.adjacent_nodes[n2.id] = n2

    def send(self, n1, n2, t, data="Test"):
        """
            Initiate a data packet from node n1 to n2
            Args:
                n1: Node 1
                n2: Node 2
                t: Time when the data packet is sent
                data : Data to sent in the packet
        """
        pkt_id = self.nodes[n1].generate_pkt_id()
        Data_pkt = Packet(pkt_id, PKT_TYPE.DPKT)
        Data_pkt.source = self.nodes[n1].id
        Data_pkt.target = self.nodes[n2].id
        Data_pkt.data = data
        try:
            self.buffer[t].append([Data_pkt, n1])
        except:
            self.buffer[t] = [[Data_pkt, n1]]

        #self.nodes[n1].queue_in.append(Data_pkt)
    def printresults(self):
        totalhops = 0
        packets = 0
        totaltranspkts =0
        totalrecpkts = 0
        for n in self.nodes:
            print("hops at target",n.id,"for",n.hops,"packets")
            totalhops += sum(n.hops.values())
            packets += len(n.hops.values())
            totaltranspkts += n.transmitted
            totalrecpkts += n.received
        print("Average Hops for",packets,"packets is",totalhops//packets)
        print("Packet loss", totaltranspkts-totalrecpkts)
    
        
    def step(self, t, dynamic=False):
        """
            Updates the network in each time step
        """
        try:
            for dp in self.buffer[t]:
                self.nodes[dp[1]].queue_in.append(dp[0])
        except:
            pass
        self.move_nodes(dynamic)
        self.add_neighbors()
       
        transmissions = []
        for n in self.nodes:
            n.forward()
        for n in self.nodes:
            
            if n.queue_out != []:
            
                pkt = n.queue_out.pop(0)
                
                if pkt.type == PKT_TYPE.RREQ:
                
                    for adj in n.adjacent_nodes.keys():
                        try:
                            n.adjacent_nodes[adj].queue_in.append(copy.deepcopy(pkt))
                            
                            transmissions.append((n.id, adj, pkt.type, (pkt.source, pkt.target)))
                        except:
                            continue
                else:
                    try:
                       
                        n.adjacent_nodes[pkt.source_route[pkt.next_hop]].queue_in.append(copy.deepcopy(pkt))
                        transmissions.append(
                            (n.id, pkt.source_route[pkt.next_hop], pkt.type, (pkt.source, pkt.target)))
                    except:
                        continue
        for n in self.nodes:
            del_list = []
            for k in n.routing_cache.keys():
                n.routing_cache[k][1] -= 1
                if n.routing_cache[k][1] <= 0:
                    del_list.append(k)
            for k in del_list:
                del n.routing_cache[k]
        return transmissions



