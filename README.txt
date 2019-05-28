README
Overview:
- Written for CS 458 Computer Networks W19, taught by Dr. N. Limam.
- The assignment specification asks for:
A router program, which uses OSPF with Djikstra's algorithm to calculate minimum cost paths to all other routers, and sends various packets (INIT, HELLO, LS PDU) to each other through the Network State Emulator. (router.py)
	INITs are sent to the NSE to register each router's id. The NSE replies with that router's circuit database (circuit_DB structure).
	HELLOs are then sent to all neighbouring routers, who must reply with a set of LS PDUs containing their circuit database.
	Upon receiving an LS PDU, router must update its topology database, recalculate its minimum cost paths, and forward the LS PDU to its neighbours.
A Network State Emulator, which has the circuit databases hardcoded into it, and sends them to the routers by their id, and forwards packets to their correct receiver (nse, provided).
A diagram of the network topology (nse_test_topology.pdf, provided).


Built on ubuntu1604-004
Tested on ubuntu1604-004
Version of make: N/A (using Python 2.7.12)
Compilers used: N/A (using Python 2.7.12)

How to run:
First run the Network State Emulator:
	./nse <routers_host> <nse_port>

Then run this program:
	python router.py <router_id> <nse_host> <nse_port> <router_port>
	OR
	./router.py <router_id> <nse_host> <nse_port> <router_port>

You will need 5 different instances of router.py with router_id 1,2,3,4,5 for proper execution.


NOTES:
This program runs on the assumption that the router IDs are numbered exactly 1,2,3,4,5.
Choosing a different combination of 5 IDs will cause the program to crash or otherwise misbehave.
You must run the router programs in order from 1 to 5.
