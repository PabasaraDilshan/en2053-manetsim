class PKT_TYPE:
    RREQ = 'REQ'
    RREP = 'REP'
    DPKT = 'DATA'


class Packet:
    def __init__(self, id, type_):
        """

            id: Unique packet id
            In case RREQ/RREP the id should be the same id as the DATA packet that generated them
            type: Packet type
            source_route: The list of nodes the packet should hop
            source: Packet origin of the DATA packet.
            target: destination of the DATA packet
             In case of RREQ/RREP it should still be the source and destination of the corresponding data packet.

        """
        self.id = id
        self.type = type_
        self.target = None
        self.source_route = []
        self.data = None
        self.next_hop = 0
        self.source = None

    def add_id(self, id):
        self.source_route.append(id)

    def check_id(self, id):
        if id in self.source_route:
            return True
        return False
