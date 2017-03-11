
# Link State Routing Protocol

import sys
import time
import json
import math
import queue
import socket
import datetime
import threading
from priodict import priorityDictionary

# Dijkstra's algorithm for shortest paths
# David Eppstein, UC Irvine, 4 April 2002

# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/117228

def Dijkstra(graph, start_node, end_node = None):
	distances = {}	                                                     # dictionary of final distances
	predecessors = {}	                                             # dictionary of predecessors
	priority_dictionary = priorityDictionary()	                     # estimated distances of non-final vertices
	priority_dictionary[start_node] = 0.0
	for vertex in priority_dictionary:
		distances[vertex] = priority_dictionary[vertex]
		if vertex == end_node:
			break
		for w in graph[vertex]:
			vwLength = float(format(distances[vertex] + graph[vertex][w], ".2f"))
			if w in distances:
				if vwLength < distances[w]:
					pass
			elif w not in priority_dictionary or vwLength < priority_dictionary[w]:
				priority_dictionary[w] = vwLength
				predecessors[w] = vertex
	return (distances, predecessors)
			
def shortestPath(G, start, end):
	D, P = Dijkstra(G, start, end)
	Path = []
	while 1:
		Path.append(end)
		if end == start:
			break
		end = P[end]
	Path.reverse()
	return D, Path

# Graph class to be used by Dijkstra to calculate the shortest path to each router

class Graph(object):

    def __init__(self):
        self.nodes = set()                           # a set of nodes so no duplicate nodes are added
        self.edges = {}                              # a dictionary to store edges
        self.distances = {}                          # a dictionary to store distances
        
    def add_node(self, node):                        # add node function adds a new router to the graph
        self.nodes.add(node)

    def remove_node(self, node):                     # remove node function removes a router from the graph
    	try:                                         # this is when we are finally able to conclude that a router is dead
    		self.nodes.discard(node)
    	except Exception:
    		pass
    	try:
    		self.edges.pop(node, None)
    	except Exception:
    		pass
    	for edge, neighbors in self.edges.items():
    		try:
    			self.distances.pop((node, edge), None)
    		except Exception:
    			pass
    		try:
    			self.distances.pop((edge, node), None)
    		except Exception:
    			pass
    		try:
    			self.edges[edge].pop(node, None)
    		except Exception:
    			pass

    def add_edge(self, from_node, to_node, distance):                           # add edge function adds an edge from and to a router
        self._add_edge(from_node, to_node, distance)                            # it uses helper function _add_edge
        self._add_edge(to_node, from_node, distance)

    def check_duplicate_edge(self, from_node, to_node, distance):               # this function checks if a duplicate edge is being added to the graph
        try:
            for j,k in enumerate(self.edges[from_node]):
                if (k[0] == to_node):
                    return True
            return False
        except Exception:
            return False
        
    def _add_edge(self, from_node, to_node, distance):                          # helper function to add an edge to the graph
        Check = self.check_duplicate_edge(from_node,to_node,distance)           # first check if this edge is not in the graph
        if (Check == False):                                                    # if it is not in the graph
            self.edges.setdefault(from_node, {})                                # append a dictionary to the new router received
            self.edges[from_node].update({to_node : distance})                  # update the edges from and to a new router
            self.distances[(from_node, to_node)] = distance                     # initialize the distance from and to a new router  

    def print(self):                                                            # helper function we used to print our graph
    	print(self.edges)

    def clearGraph(self):                                                       # function used to clear the graph after every 30 seconds
        self.edges.clear()
        self.distances.clear()
        self.nodes.clear()

def send(sequence_number):              # send function that runs in a separate thread, receives a global sequence number, the first time a router runs
	while True:
		sequence_number = sequence_number.split(" ")[0] + " " + str((int(sequence_number.split(" ")[1]) + 1))      # incrementing sequence number
		packet_contents = []                                                                                       # packet to be sent
		
		alive_routers = []                                               # a list to check for alive routers
		while routers_queue.empty() != True:                             # while the queue that contains alive routers is not empty
			alive_routers.append(routers_queue.get())                # get router names and append it to alive routers

		for router, state in routers_state.items():                      # run a for loop on router_state list
			if router in alive_routers:                              # if a router in the list is also in the alive router list
				lock.acquire()
				routers_state[router] = 1                        # initialize that router as 1 (it is alive)
				lock.release()
				lock.acquire()
				router_packets[router] = 3                       # and initialize router_packets to 3 as it is not dead
				lock.release()
			else:                                                    # if a router is not alive router list
				lock.acquire()
				router_packets[router] = router_packets[router] - 1      # decrement its counter making it closer to be delared as dead
				lock.release()
		
		lock.acquire()
		routers_state[router_id] = 1                                     # a router declaring itself as alive
		lock.release()
		lock.acquire()
		router_packets[router_id] = 3                                    # and initializing its own router_packets id to 3
		lock.release()

		for router, packets in router_packets.items():          # run a loop on router_packets list to check which has the value less than or equal to 0
			if packets <= 0:                                         # if a router's value is less than or equal to 0, it means that it is dead
				lock.acquire()
				routers_state[router] = 0                        # initialize the router_state to 0 (dead) 
				lock.release()
				received_packets.pop(router, None)      # and pop that router from the received packets list so we reset the sequence numbers of that router

		packet_contents.append(router_id)
		packet_contents.append(port)
		packet_contents.append(sequence_number)
		packet_contents.append(number_of_neighbors)
		packet_contents.append(neighbors)                                # making the packet
		packet_contents.append(routers_state)
		packet_contents.append(weights)
		packet_contents.append(port_numbers)
		packet = json.dumps(packet_contents)
		for neighbor_port in port_numbers:                               # iterating over all the neighbors and sending the packet to them
			clientSocket.sendto(packet.encode(), ("localhost", neighbor_port))
		time.sleep(1)                                                    # sleep for 1 second

def receive():                          # receive function used to receive packets from all neighboring routers
	while True:
		encoded_packet, clientAddress = serverSocket.recvfrom(2048)                   # receive a packet from a neighbor
		packet = encoded_packet.decode()                                              # decode it
		packet_contents = json.loads(packet)                                          # convert it to a list from a stream

		node = packet_contents[0]                                                     # save the senders name in a variable
		sequence_number = packet_contents[2]                                          # save the sequence number in a variable
		neighbor_nodes = packet_contents[4]                                           # save the neighbors in a new list
		neighbor_ports = packet_contents[7]                                           # save the neighbor ports in a new list
		distances = packet_contents[6]                                                # save the distances of the neighbors in a new list

		routers_state.update({node : 1})                                              # update the sender's state as 1 (alive)
		router_packets.update({node : 3})                                             # update it's counter to 3

		routers_queue.put(node)                                                       # put the senders name in the queue so it can be declared as alive

		if node not in received_packets:                                              # if the router has sent the packet first time
			received_packets.setdefault(node, [])                                 # create its place in the received packets list
			received_packets[node].append(sequence_number)                        # and append its sequence number in it
		
		if sequence_number not in received_packets[node]:                             # if the packet received is a new sequence number
			received_packets[node].append(sequence_number)                        # append this sequence number to received packets list
			#print(packet_contents)
			lock.acquire()
			graph.add_node(node)                                                  # add the arrived router in the graph
			lock.release()
			for index, neighbor_node in enumerate(neighbor_nodes):                # iterate over neighbor names of the sender
				if neighbor_node not in routers_state or routers_state[neighbor_node] != 0:      # if a neighbor is not dead or it is not in the router_state list altogether
					lock.acquire()
					graph.add_edge(node, neighbor_node, distances[index])                    # make an edge from the sender and its neighbors with their distances
					# print("node: ", node, ", neighbor_node: ", neighbor_node, ", distance: ", distances[index])
					lock.release()
			# print()

			# print("Received:")
			# print(packet_contents)
			# print()
			
			for neighbor_port in port_numbers:                                     # iterate over the neighboring router's port numbers
				if neighbor_port != packet_contents[1] and neighbor_port not in neighbor_ports:     # don't send the packet to the one it received from
					clientSocket.sendto(packet.encode(), ("localhost", neighbor_port))          # else send the packet to all other neighbors
					# time.sleep(1)

                                                               # main

if len(sys.argv) != 4:                                                                         # if the arguments are not 4 display an error
	print("Error!")
	sys.exit()

file_name = sys.argv[3]                                                                        # save filename in a variable
router_id = sys.argv[1]                                                                        # save router id in a variable
port = int(sys.argv[2])                                                                        # save router port number in a variable

file_opener = open("10\\" + file_name, "r")                                                     # open the file
file_data = file_opener.read()                                                                 # read its data

number_of_neighbors = file_data[0]                                              # the first word in the file is the number of neighbors, save it in a variable
neighbors = []                                                                  # a list to store neighbors of this router
weights = []                                                                    # a list to store neighbor distances
port_numbers = []                                                               # a list to store neighbor port numbers

for line in file_data.split("\n"):                                              # read the file line by line
	if len(line.split(" ")) == 3:                                           # split the data by spaces
		neighbors.append(line.split(" ")[0])                            # store neighbors
		weights.append(float(line.split(" ")[1]))                       # store weights
		port_numbers.append(int(line.split(" ")[2]))                    # store port numbers

file_opener.close()                                                             # close the file

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)                 # create a serverSocket
serverSocket.bind(("localhost", port))
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)                 # create a clientSocket

sequence_number = router_id + " " + "1"                                         # starting sequence number by 1

received_packets = {}                                   # initialize received_packets dictionary used to keep track of duplicate packets using sequence numbers

routers_state = {}                                      # intialize router_state dictionary used to keep track of a routers state (dead or alive)
routers_state[router_id] = 1                            # initialize this router as 1 (alive)

router_packets = {}                                     # initialize router_packets dictionary used to keep track of dead router and waiting for atleast 3 seconds
router_packets[router_id] = 3                           # initializing this router's variable as 3

graph = Graph()                                         # initialize Graph()
routers_queue = queue.Queue()           # initialize routers_queue used by receive and send functions to keep track of alive routers on the basis of newly arrived packets                           

lock = threading.Lock()                                 # a lock used for synchronization between shared variables

send_thread = threading.Thread(target = send, args = (sequence_number, ))            # send function thread
send_thread.start()                                                                  # starting the thread

receive_thread = threading.Thread(target = receive, args = ())                       # receive function thread
receive_thread.start()                                                               # starting the thread

routers = []

while True:                                                                          # Dijkstra running in an infinite loop
	time.sleep(30)                                                               # with a delay of 30 seconds
	print("I am Router ", router_id)
	for router in graph.nodes:                                                   # iterating over graph nodes
		if router_id != router:                                              # don't show path for this router, otherwise show paths for all other routers
			D, Path = shortestPath(graph.edges, router_id, router)
			print("Least cost path to router ", router, ": ", "".join(Path), " and the cost: ", D[router])           # print path with the least cost
	print()
	graph.clearGraph()                                                                                                       # clear Graph
