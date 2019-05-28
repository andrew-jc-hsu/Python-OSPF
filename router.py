#!/usr/bin/env python

# router.py

import sys, struct, socket

# -1. Predefined structures, constants
NBR_ROUTER = 5

pkt_HELLO = struct.Struct("<II") 		# router_id, link_id
pkt_LSPDU = struct.Struct("<IIIII") 	# sender, router_id, link_id, cost, via
pkt_INIT = struct.Struct("<I")			# router_id
link_cost = struct.Struct("<II")		# link, cost
''' struct circuit_DB {
	unsigned int nbr_link; // number of links attached to a router
	struct link_cost linkcost[NBR_ROUTER];
};
''' # circuit_DB instead done by manual pack/unpacking


# 0. Usage, variable initialization, logging functions
if ( len( sys.argv ) != 5 ):
	sys.exit( "Usage: " + sys.argv[0] + " <router_id> <nse_host> <nse_port> <router_port>" )

my_router_id = int( sys.argv[1] )
router_port = int( sys.argv[4] )
nse_host = sys.argv[2]
nse_port = int( sys.argv[3] )
nse = ( nse_host, nse_port )

router_log = open( "router"+str( my_router_id )+".log", 'w' )

routerSocket = socket.socket( socket.AF_INET, socket.SOCK_DGRAM ) # UDP
routerSocket.bind( ('', router_port ) )


# Variables declared here for clarity
nbr_link = 0 		# Number of links this router is connected to
cdb = [] 			# Circuit database: List of tuples ( link_id, link_cost )
LSDB = []			# Link State Database. Each item is a router. Each router is a list of links.
for i in range( NBR_ROUTER ):
	LSDB.append([])	# Initialize NBR_ROUTER empty spaces. We assume the router id's are i=1,2,...,NBR_ROUTER.
					# LSDB[0] is R1, LSDB[1] is R2, etc.

RIB = [] 			# Routing Information Base. Each entry is ( string of next hop router, min cost of path ).
for i in range( NBR_ROUTER ):
	RIB.append( ( 'INF', 65535 ) ) # Initialize NBR_ROUTER entries. 65535 is used if unreachable.
					# RIB[0] is R1, RIB[1] is R2, etc.
RIB[ my_router_id - 1 ] = ( "Local", 0 ) # Entry for self.

discovered = []		# List of "discovered" neighbours. Stores the link_id of their HELLO.


# Logging functions
def log_RIB(): # Logs the RIB for current topology.
	router_log.write( "# RIB\n" )
	for i in range( NBR_ROUTER ): # Iterate through entries in RIB
		msg = "R" + str( my_router_id ) + " -> "
		msg = msg + "R" + str( i+1 ) + " -> " + RIB[i][0] + ", " + str( RIB[i][1] ) + "\n"
		router_log.write( msg ) # eg. R1 -> R1 -> Local, 0

def log_LSDB(): # Logs the current topology database.
	router_log.write( "# Topology database\n" )
	for i in range( NBR_ROUTER ): # Iterate through routers in LSDB
		if LSDB[i] == []:	# If this entry in LSDB is empty, we don't know about that router.
			continue		# Go to next entry without logging the "Rx -> Ry nbr link z" msg. 

		msg = "R" + str( my_router_id ) + " -> "
		msg = msg + "R" + str( i+1 ) + " nbr link " + str( len( LSDB[i] ) ) + "\n"
		router_log.write( msg ) # eg. R1 -> R1 nbr link 2

		for link in LSDB[i]:
			msg = "R" + str( my_router_id ) + " -> R" + str( i+1 ) + " link " + str( link[0] )
			msg = msg + " cost " + str( link[1] ) + "\n"	
			router_log.write( msg ) # eg. R1 -> R1 link 1 cost 1	

def log_LSPDU( action, sender, rid, link_id, cost, via ): # ( str, int, int...) Logs sending/rcving a LS PDU.
	# action = " receives " OR " sends "
	msg = "R" + str( my_router_id ) + action
	msg = msg + "an LS PDU: sender " + str( sender )
	msg = msg + ", router_id " + str( rid )
	msg = msg + ", link_id " + str( link_id )
	msg = msg + ", cost " + str( cost )
	msg = msg + ", via " + str( via ) + "\n"
	router_log.write( msg )

def log_INIT(): # Logs sending an INIT to NSE.
	msg = "R" + str( my_router_id ) + " sends an INIT: router_id " + str( my_router_id ) + "\n"
	router_log.write( msg )

def log_HELLO( action, rid, link_id ): # ( str, int, int) Logs sending/rcving a HELLO.
	# action = " receives " OR " sends "
	msg = "R" + str( my_router_id ) + action
	msg = msg + "an HELLO: router_id " + str( rid )
	msg = msg + ", link_id " + str( link_id ) + "\n"
	router_log.write( msg )

def log_CDB(): # Logs rcving circuit_db from NSE.
	msg = "R" + str( my_router_id ) + " receives an circuit_DB: nbr_link "
	msg = msg + str( nbr_link )
	msg = msg + ", linkcost: "
	for link in cdb:
		msg = msg + "( link " + str( link[0] ) + " cost " + str( link[1] ) + "), "
	msg = msg[:-2] + "\n" # Remove the last ", " and add newline character
	router_log.write( msg )


# 1. Send INIT pkt to NSE
init = pkt_INIT.pack( my_router_id )
routerSocket.sendto( init, nse )
log_INIT() # Log sendng the INIT msg


# 2. Receive circuit_DB structure from NSE
nse_CDB = routerSocket.recv( 4 + 4*2*NBR_ROUTER ) # See below
args = struct.unpack( "<I" + NBR_ROUTER*"II", nse_CDB ) # Little endian, 1 + 2*NBR_ROUTER unsigned ints
nbr_link = args[0]
for i in range( nbr_link ):
	cdb.append( ( args[ 2*i+1 ], args[ 2*i+2 ] ) ) # Each link in cdb is a tuple ( link_id, link_cost )
log_CDB() # Log receiving the CDB msg

temp = []
for link in cdb:
	temp.append( link ) # Create a router for this router with the links from CDB.
LSDB[ my_router_id - 1 ] = temp # Add /this/ router to LSDB.


# 3. Send a HELLO pkt to all neighbours.
for neighb in cdb:
	hello = pkt_HELLO.pack( my_router_id, neighb[0] )
	routerSocket.sendto( hello, nse )
	log_HELLO( " sends ", my_router_id, neighb[0] ) # Log sending each HELLO msg


# 4. Operating loop where router receives HELLO and LS PDU packets.
def reply_to_HELLO( datastring ):
	router_id, link_id = pkt_HELLO.unpack( datastring )
	log_HELLO( " receives ", router_id, link_id ) # Log rcving each HELLO msg
	discovered.append( link_id ) # Add HELLO-er to list of "discovered" neighbours	

	for router in LSDB: # Send current LSDB state in reply.
		for link in router:
			lspdu = pkt_LSPDU.pack( my_router_id, my_router_id, link[0], link[1], link_id ) # sender, router_id, link_id, cost, via
			routerSocket.sendto( lspdu, nse )
			log_LSPDU( " sends ", my_router_id, my_router_id, link[0], link[1], link_id ) # Log sending each LSPDU msg


def dijkstra(): # Uses current LSDB to recalculate RIB.
	# INITIALIZATION
	nprime = [ my_router_id ]
	me_and_neighbours = [ my_router_id ] # Temp list of me + neighbours needed in part (***).

	# - RIB: List of (string next hop router, int cost).
	# - cdb: List of (link_id, cost) attached to This router, as given by the NSE.
	# - LSDB: List of routers.
	# - LSDB[i]: List of router i+1's links (int link_id, int cost)
	for i in range( NBR_ROUTER ):
		if i+1 == my_router_id:
			continue # We initialized the RIB entry for ourself to ("Local", 0), so skip.

		adjacent = False # The adjacent link
		for link in cdb:
			if link in LSDB[i]: # If this router has one of the links in your circuit db (is adjacent)
				adjacent = link
				break

		if adjacent == False:	# If router not adjacent
			RIB[i] = ( "INF", 65535 )
		else: 					# Then, router adjacent
			RIB[i] = ( "R" + str( i+1 ), adjacent[1] )
			me_and_neighbours.append( i+1 )
	
	# LOOP (until all routers in nprime) 
	while len( nprime ) < NBR_ROUTER:
		# Find router w not in nprime such that D(w) is a minimum.
		w = 999 						# ID of minimum distance router.
		mindist = 65535					# Current minimum distance.
		for i in range( NBR_ROUTER ): 	# Iterate through entries in RIB:
			if ( i+1 ) in nprime:
				continue 				# Skip over v already in nprime.
			if RIB[i][1] < mindist:
				w = i+1
				mindist = RIB[i][1]		# If you find w with less distance, update w,mindist.

		# Add w to nprime.
		nprime.append( w )

		if w == 999:	# w = 999 could happen if all routers not in nprime are unreachable.
			break 		# Then, it's fine to break.

		# Update D(v) for all v adjacent to w and not in nprime:
		# - LSDB[w-1]: Router w, which is a list of links (int link_id, int cost)
		for i in range( NBR_ROUTER ):
			if ( i+1 ) in nprime:
				continue				# Skip over v already in nprime.
			adjacent = False
			for link in LSDB[w-1]:		# Iterate through router w's links:
				if link in LSDB[i]:		# If this router v has one of w's links, they are adjacent.
					adjacent = link
					break
			if adjacent:				# Then, since this router is adjacent, update its D(v) in RIB.
				if RIB[i][1] >= RIB[w-1][1] + adjacent[1]: 	# If route using w <= previous route,
					# nexthop = "R" + str( w )				#	then update next-hop router to w.
					
					# However, the next-hop router must either be THIS router or adjacent to it;
					# it shouldn't be a router two or more hops away.
					# If it is 2+ hops away, then we actually need to use the next-hop router's next-hop router.
					# And so on, tracing next-hop of next-hop until nexthop in me_and_neighbours.
					v = w
					while v not in me_and_neighbours:
						v = int( RIB[v-1][0][1] ) # Remember, RIB[v-1][0] is "Rx", so RIB[v-1][0][1] is character x.
					nexthop = "R" + str( v )

				else:
					nexthop = RIB[i][0]

				distance = min( RIB[i][1], RIB[w-1][1] + adjacent[1] ) # D(v) = min( D(v), D(w) + c(w,v) )
				RIB[i] = ( nexthop, distance )

	# At function end, RIB has now been recalculated.

def on_rcv_LSPDU( datastring ):
	sender, router_id, link_id, cost, via = pkt_LSPDU.unpack( data )
	log_LSPDU( " receives ", sender, router_id, link_id, cost, via ) # Log receiving the LSPDU msg
	if ( link_id, cost ) in LSDB[ router_id-1 ]: # If this link is already in your LSDB, ignore.
		pass
	else: # Otherwise, this is a unique LS PDU.
		LSDB[ router_id-1 ].append( ( link_id, cost ) ) # Add this (unique) LS PDU info to LSDB.
		# Forward this LS PDU to all discovered neighbours, but not the one that sent you this LS PDU.
		for disc_link in discovered:
			if disc_link == via: # If this neighbour was the one that sent you this LSPDU, skip.
				continue
			lspdu = pkt_LSPDU.pack( my_router_id, router_id, link_id, cost, disc_link ) # Adjust sender and via fields
			routerSocket.sendto( lspdu, nse )
			log_LSPDU( " sends ", my_router_id, router_id, link_id, cost, disc_link ) # Log sending each LSPDU msg

		dijkstra() # Run Dijkstra's algorithm on new LSDB.
		log_LSDB() # Log new LSDB.
		log_RIB() # Log new RIB.

# Actual loop
while True:
	data = routerSocket.recv( 128 )
	if len( data ) == pkt_HELLO.size: # If the data is a HELLO pkt:
		reply_to_HELLO( data )

	else: # Otherwise, the data is a LSPDU pkt:
		on_rcv_LSPDU( data )

# 99. Clean-up, except not really because the while loop doesn't terminate
router_log.close()
routerSocket.close()
