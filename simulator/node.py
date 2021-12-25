from .packet import PKT_TYPE
from .packet import Packet


class Node:
    def __init__(self, id, x, y, range):
        """
            Attributes:
                id: Node address
                x:  x-coordinate
                y:  y-coordinate
                range: Maximum transmission range
                queue_in: Input queue.Packets entering will be present here with the earliest one at index 0
                queue_out: Output queue of node. Packets forwarded to by this node must be appended to this list
                adjacent_nodes: A dictionary of neighboring nodes which  will be updated every time step
                routing_cache: A dictionary containing the routes discovered so far. Implemented with a expiration duration if not used recently.
                expire_time: expire time of a route in cache
                recent: A list of recently recieved packets (RREQ only)
                count : Used to generate a unique id  for data packets originating from this node
                buffer: A dictionary of Buffered DATA packets
                recieved: A list of data packets sent to this node( i.e packet target == node.id)
        """
        self.id = id
        self.x = x
        self.y = y
        self.range = range
        self.queue_in = []
        self.queue_out = []
        self.adjacent_nodes = {}
        self.routing_cache = {}
        self.expire_time = 30
        self.recent = []
        self.count = 1
        self.buffer = {}
        self.received = []
        self.hops = {}
        self.transmitted = 0
        self.received = 0

    def generate_pkt_id(self):
        """
            Generates a unique packet id
        """
        self.count+=1
        return self.id + str(self.count)

    def forward(self):
        """
            Packet forwarding
        """
        pkt = None
        if self.queue_in != []:
            pkt = self.queue_in.pop(0)
            
        if pkt is not None:
            self.route(pkt)

    def check_in_recent(self, pkt):
        """
            Checks whether the given pkt is in the nodes recently forwarded packets.
            For RREQ packets
        """
        assert pkt.type == PKT_TYPE.RREQ,"Invalid packet type"
        if (pkt.source, pkt.target, pkt.id) in self.recent:
            return True
        return False

    def add_to_recent(self, pkt):
        """
            Adds the pkt to the recent history of the node
            For RREQ packets
        """
        assert pkt.type == PKT_TYPE.RREQ,"Invalid packet type"
        self.recent.append((pkt.source, pkt.target, pkt.id))

    def add_to_cache(self, pkt):
        """
            Add the packets source_route to the route cache
            For RREP packets
        """
        self.routing_cache[pkt.target] = [pkt.source_route,self.expire_time]

    def check_in_cache(self, pkt):
        """
            Check whether a route has been already discovered from the node to the target
        """
        if pkt.target in self.routing_cache.keys():
            return True
        return False

    def add_path_from_cache(self, pkt):
        """
            Add route from cache to the source route of the packet
        """
        
        pkt.source_route = self.routing_cache[pkt.target][0]

        self.routing_cache[pkt.target][1] = self.expire_time

        return pkt

    def check_in_buffer(self, pkt):
        if pkt.id in self.buffer.keys():
            return True
        return False

    def add_to_buffer(self, pkt):
        self.buffer[pkt.id] = pkt

    def retrieve_from_buffer(self, pkt):
        try:
            DATA_pkt = self.buffer[pkt.id]
            del self.buffer[pkt.id]
            DATA_pkt.source_route = pkt.source_route
            DATA_pkt.next_hop += 1
            return DATA_pkt
        except:
            print("Error",pkt.id,self.id)

    def generate_RREP(self, pkt):
        assert pkt.type == PKT_TYPE.RREQ, "RREP can be generated only for RREQ pkts. pkt recieved {}".format(pkt.type)
        pkt.type = PKT_TYPE.RREP
        pkt.source_route.append(self.id)

        return pkt

    def generate_RREQ(self, pkt):
        RREQ_pkt = Packet(pkt.id, PKT_TYPE.RREQ)
        # RREQ_pkt.source_route = pkt.source_route
        RREQ_pkt.source = pkt.source
        RREQ_pkt.target = pkt.target
        RREQ_pkt.source_route.append(self.id)
        return RREQ_pkt

    def add_to_queue_out(self, pkt):
        if pkt.type == PKT_TYPE.RREQ and pkt.source != self.id:
            pkt.next_hop += 1
        elif pkt.type == PKT_TYPE.DPKT and pkt.source != self.id:
            # print(pkt.source_route,pkt.type,pkt.next_hop)
            pkt.next_hop += 1
        elif pkt.type == PKT_TYPE.RREP and pkt.target != self.id:
            
            pkt.next_hop -= 1
        self.queue_out.append(pkt)

    def handleDpkt(self,pkt):
        """
        Handling Data Packets(DPKT)
        if path for DPKT doesn't exist and DPKT in source node 
        => add DPKT to buffer and generate a RREQ and broadcast packet.
        if path exists and DPKT in source node
        => get path from cache and send packet to next node in path.
        if DPKT isn't in source node
        => send packet to next node in path.
        """
        if(pkt.source==self.id):
            self.transmitted+=1
        if pkt.source == self.id and not self.check_in_cache(pkt):
            self.add_to_buffer(pkt)
            rreq=self.generate_RREQ(pkt)  
            self.add_to_recent(rreq) 
            self.add_to_queue_out(rreq)
            return
        elif pkt.source == self.id and self.check_in_cache(pkt):
            dpkt = self.add_path_from_cache(pkt)
            dpkt.next_hop+=1
            self.add_to_queue_out(dpkt)
            return
        elif pkt.target == self.id:
            self.received+=1
            self.hops[pkt.id] = len(pkt.source_route)-1
            return
        else:
            self.add_to_queue_out(pkt) 
            return
    
    def handleRrep(self,pkt):
        """
        Handling RREP packets
        if RREP is in source node
        => get buffered DPKT of RREP and send it on cached source route.
        if RREP is not in source node
        => send RREP to next node
        """
        if self.id == pkt.source:
            self.add_to_cache(pkt)
            if self.check_in_cache(pkt):
                dpkt = self.retrieve_from_buffer(pkt)
                dpkt = self.add_path_from_cache(dpkt)
                self.add_to_queue_out(dpkt)
        else:
            self.add_to_queue_out(pkt)
        
    def handleRreq(self,pkt):
        """
        Handling RREQ packets
        if RREQ is in target node
        => add RREQ to recent history of node and send RREP packet to retrieved source route
        if RREQ is not in recent history of node
        => update source route and broadcast RREQ
        if RREQ is in recent history
        => forward to next recieved packets of this node
        """
        if self.id == pkt.target:
            if not self.check_in_recent(pkt):
                self.add_to_recent(pkt)
                self.add_to_queue_out( self.generate_RREP( pkt))
                return
        if not self.check_in_recent(pkt):
            pkt.source_route.append(self.id)
            self.add_to_queue_out(pkt)
            self.add_to_recent(pkt)
            return
        else:
            self.forward()
            return

    def route(self, pkt):
        """
            A packet can be RREQ (Route Request), RREP(Route reply) or a DPKT(Data packet)
            A data packet originating from this node will have an empty list as the pkt.source_route)
            Your task is complete the routing algorithm using the helper functions given. Feel free to add your own
            functions and make sure you add comments appropiately.
            
            If a packet is to be broadcasted or to be forwarded to another node it should be appened to the queue_out.
            Take note next hop should give the index of the next node it must be forwarded in the source route. Make sure you update
            the pkt.next_hop before appending to queue_out.
        """
        if pkt.type == PKT_TYPE.DPKT:
            self.handleDpkt(pkt)

        elif pkt.type == PKT_TYPE.RREQ:
            self.handleRreq(pkt)
        elif pkt.type == PKT_TYPE.RREP:
            self.handleRrep(pkt)
