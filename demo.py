from simulator.graph import Graph
from simulator.visualizer import step
import cv2

manet = Graph()

# initialize network
"""
Make sure  the ranges of all nodes are the same to enable bidirectional 
communication so as to simplify the protocol
"""
tx_range = 200
dynamic = False  # True to use mobile model

manet.add_node(500, 550, tx_range)  # "Add node 0 at 500,550"
manet.add_node(690, 600, tx_range)  # "Add node 1 at 690,600"
manet.add_node(780, 700, tx_range)  # "Add node 2 at 780,700"
manet.add_node(780, 600, tx_range)
manet.add_node(780, 500, tx_range)
manet.add_node(800, 400, tx_range)
manet.add_node(900, 500, tx_range)
#
manet.send(0, 6, 1, 'Test')# send a data packet at time step 1 from node 0 to 2
manet.send(0, 6, 10, 'Test1')
manet.send(1, 3, 10, 'Test2')
manet.send(2, 6, 10, 'Test3')
# manet.send(1, 6, 2, 'Test1')
for t in range(20):  # Simulate for 20 time steps # Do not increase the timesteps beyond 30. If you want to increase set self.expire_time in node.py to a high value
    step(manet, t, dynamic)
manet.printresults()
cv2.destroyAllWindows()
