from helpers import *

class Grid():
    """
    Contains the environment, the auctioneer
    
    Grid is small grid of 6 hexagons surrounding 7th center (q, r, s)
    
    
        (0, -1, 1)   (1, -1, 0)
    (-1, 0, 1)  (0,0,0)  (1, 0, -1)
        (-1, 1, 0)   (0, 1, -1)
    """
    
    
    def __init__(self, radius=1, seed=None):
        """
        Creates Grid object
        
        Inputs:
            agents: list, agents in the environment

        """
        self._revenue = 0
        self.coords = create_hex_grid(radius)
        self.coords_l = list(self.coords)
        # if you want to do capacities, make a dictionary with {hex: capacity}
        
        # track the number of rounds an agent has been waiting {agent id: rounds waited}
        self._roundrobin = {}
        
        # track type of prioritization - default random
        # can be [random, roundrobin, backpressure]
        self._priority = "random"
        
        self.num_conflicts = 0
        self.seed = seed
        self.radius = radius

    @property
    def revenue(self):
        """
        Returns current revenue of grid
        Returns:
            out: integer
        """
        return self._revenue
    
    @property
    def priority(self):
        return self._priority
    
    def set_priority(self, method):
        """
        Set the prioritization method
        Inputs:
            method: string of type of prioritization
        """
        assert method in ["random", "roundrobin", "backpressure", "accrueddelay", "reversals","secondprice", "secondback"]
        self._priority = method
        
    def step_sim(self, locations, bids):
        """
        Step through one step of Chris's protocol - this handles cycles on until hold/motion (lines 4 to 24 in Alg 1)
        Inputs:
            locations: {id : loc} all active agent locations (if you're trying to depart also active)
            bids: {id : (next_loc, price)} all active agent bids
            
        Returns:
            commands: dictionary of tuples {id : (next loc, winning price)} of size (# agents) (None, 0) means hold
        """
        # price = -1 means it's still undecided 
        # price = 0 means it's on hold
        # init commands
        commands = {_id: (None, -1) for (_id, (_, _)) in bids.items()}
        
        # build node graph - all departing flights are treated as coming from one massive ground node -1
        in_graph = {}   # inverse graph - points from inbound to outbound
        requests = {}   # dictionary of all locations requested and hwho's requesting
        for loc, (_id, (next_loc, price)) in zip(locations.values(), bids.items()):

            if price == -1: continue
            assert loc == -1 or loc in self.coords, "Coordinate does not exist in the grid"
            
            # build graph for cycle and backpressure
            if next_loc in in_graph.keys(): in_graph[next_loc].append(loc)
            else: in_graph[next_loc] = [loc]
            
            # buidl the request list - essentially all the bid info the agents gave
            # right now its {location: (id, stated value)}            
            if next_loc not in requests: requests[next_loc] = []
            requests[next_loc].append((_id, price))
            
            # add to round robin priority list
            if _id not in self._roundrobin: self._roundrobin[_id] = 0

        # print("graph\n", in_graph)
        # identify cycles (skipping for now)
        # print('requests', requests)
        cycle_ids = []
        for req in requests.keys():
            temp = self.find_cycles(in_graph, req)
            for loc in temp:
                count = 0
                for _id in locations.keys():
                    if _id not in cycle_ids and locations[_id] == loc and bids[_id][0] in temp and count < CAPACITY:
                        cycle_ids.append(_id)
                        count += 1
                        
        # print("cycling _id", cycle_ids)
        for _id in cycle_ids:
            commands[_id] = bids[_id]
        
        
        # calculate backpressure and sort - order is which sectors to deconflict first
            # NOTE: both backpressure and cycles requires building a graph at each step
        pressures = {req: self.calc_backpressure(in_graph, req) for req in requests.keys()}
        order = sorted(requests, key=lambda req: pressures[req], reverse=True)

        # handling every sector now
        for loc in order:
            asks = requests[loc]
            
            # print(asks)
            # assert 1 == 0
            
            # create a list of (index, price of bid)
            undecided = []
            decided = []
            for (_id, price) in asks:
                if commands[_id][1] == -1: undecided.append((_id, price))
                else: decided.append((_id, price))

            # resolve capacities
            # check if you still have capacity
            assert len(decided) <= CAPACITY, print(decided, "\n", locations, "\n", bids, "\n", commands, "\n", loc)     # sanity check
            if len(decided) < CAPACITY:
                
                # if you still have capacity and still have flights waiting
                if len(undecided) <= CAPACITY - len(decided):

                    # function for moving undecided into G (aka all go)
                    # the 4 line block is the key
                    # assert bids[i][0] == loc
                    for i in range(len(undecided)):
                        (win_i, price) = undecided.pop(i)
                        commands[win_i] = (bids[win_i][0], 0)   # append comamnd
                        self._revenue += 0
                        decided.append((win_i, price))
                        
                # if you don't have capacity and have to decide
                else: 
#                     print("contested", loc)
                    self.num_conflicts += 1
                    while CAPACITY > len(decided):
                        
                        #PRIORITIZATION METHODS - win returns id of winning agent
                        if self._priority == "roundrobin": 
                            win, win_id, price = self.roundrobin_prioritization(undecided)
                            undecided.pop(win)
                        elif self._priority == "backpressure": 
                            win, win_id, price = self.backpressure_prioritization(undecided, locations, in_graph)
                            undecided.pop(win)
                        elif self._priority == "secondprice" :
                            win, win_id, price = self.secondprice_prioritization(undecided)
                            undecided.pop(win)
                        elif self._priority == "secondback":
                            win, win_id, price, moves = self.secondback_prioritization(undecided, locations, in_graph, bids)
                            undecided.pop(win)
                        else: 
                            win, win_id, price = self.random_prioritization(undecided)   # PRIORITIZATION using random prioritization
                            undecided.pop(win)
                            
                        if self._priority == "secondback":
                            # print(commands)
                            for _id, price in moves:
                                commands[_id] = [bids[_id][0], price]
                            # print(commands)
                            
                        else:
                            commands[win_id] = (bids[win_id][0], price)

                        self._revenue += price
                        decided.append((win_id, price))
                        # assert 1 == 0
                        
            # end dealing with the sector - mark undecided as hold
            for (_id, price) in undecided:
                commands[_id] = (None, 0)
                self._roundrobin[_id] += 1
                if locations[_id] in requests: requests[locations[_id]].append((_id, price))

        # print("locs", locations)
        # print("bids", bids)
        # print("comms", commands)
        return commands


    
    def random_prioritization(self, undecided, seed = None):
        """
        Random prioritization method by merged queue, flight
        Inputs:
            undecided: list of tuples (index, price) of undecided flights
            seed: RNG seeder
        Returns:
            high_index: integer of an index in undecided
            win_id: id of winning agent
            price: price the agent pays
        """
        if seed: rand = np.random.default_rng(seed)
        else: rand = np.random.default_rng()
        
        win = rand.integers(len(undecided))
        (win_id, price) = undecided[win]
                                                                             
        return win, win_id, price
    
    def roundrobin_prioritization(self, undecided):
        """
        Trying to set up round robin prioritization around the grid
        If tied, first instance in undecided gets to go
        Inputs:
            undecided: list of tuples (index, price) of undecided flights
        Returns:
            high_index: integer of an index in undecided
            win_id: id of winning agent
            price: price the agent pays
        """
        
        high_wait = 0
        high_index = 0
        
        # find the highest wait
        for i, (_id, price) in enumerate(undecided):
            if self._roundrobin[_id] > high_wait:
                high_wait = self._roundrobin[_id]
                high_index = i
        
        # set highest wait to 0, b/c they're getting to move
        self._roundrobin[undecided[high_index][0]] = 0
        
        (win_id, price) = undecided[high_index]
                                                                             
        return high_index, win_id, price
        
        
    def backpressure_prioritization(self, undecided, locations, graph):
        """
        Using backpressure to resolve conflicts
        Inputs:
            undecided: list of tuples (_id, price) of undecided flights
            locations: {id:Hex} dictionary of all locations of agents
            graph: dictionary of Hex {inbound sector: [outbound sectors]}
        Returns:
            high_index: integer of current flights following
        """
        
        high_press = 0
        high_index = 0
        
        # find the highest backpressure
        for i, (_id, price) in enumerate(undecided):
            back_press = self.calc_backpressure(graph, locations[_id])
            
            if back_press > high_press:
                high_press = back_press
                high_index = i
       
        (win_id, price) = undecided[high_index]
                                                                             
        return high_index, win_id, price
    
    
    def secondprice_prioritization(self, undecided):
        """
        Sealed second price auction for locations - single square bid
    
        Inputs:
            requests: dictionary of (loc, (agent_id, bid)) to resolve
            num_agents: number of agents bidding
        
        Returns:
            output: list of tuples (next loc, winning bid) of size (# agents)
        """
        
        # get high bid
        high_index, winner = max(enumerate(undecided), key=lambda x:x[1][1])
        # print(undecided)
        
        # get price of second bid
        new = set(undecided)
        new.remove(winner)
    
        if not new: price = 0
        else: price = max(new, key=lambda x: x[1])[1]
    
        # self._revenue += price
        
        # print(high_index, winner, price)
        
        return high_index, winner[0], price
        
    def secondback_prioritization(self, undecided, locations, graph, bids):
        """
        Inputs:
            undecided: list of tuples (_id, price) of undecided flights
            locations: {id:Hex} dictionary of all locations of agents
            graph: dictionary of Hex {inbound sector: [outbound sectors]}
            bids: {id : (next_loc, price)} all active agent bids
        Outputs:
            
        """
        
        # calculate sum total value on every chain
        # create inverted locations dictionary - should be one to one IF capacity = 1
        assert CAPACITY <= 1, "Change this entire setup"
        invlocations = {v: k for k, v in locations.items()}
        # for every undecided branch
            # recursive helper function - input of undecided, graph - append that node's value to
        chains = [] # store chains
        for (_id, _) in undecided:

            chains.extend(self.secondback_helper(locations, invlocations, graph, bids, _id))

        for chain in chains:
            chain["total"] = sum(chain["price"])

        # print("chains\n", chains)
        # find the winner and price
            # search like in second price
        
        # high_index, winner = max(enumerate(chains), key=lambda c: c[1]["total"])
        
        # # new = set(chains)
        # # new.remove(winner)
        # # print(chains)
        # chains.remove(winner)

        # if not chains: price = 0
        # else: price = max(chains, key=lambda x: x["total"])["total"]
        
        chains = sorted(chains, key = lambda c: c["total"], reverse=True)
        # print(chains)
        winner = chains[0]
        price = chains[1]["total"]
        
        high_index = None
        for j, (_id, _) in enumerate(undecided):
            if not high_index and _id == winner["chain"][-1]:
                high_index = j

        # print(chains)
        # print(winner, high_index)
        # print(price)

        # commands
        commands = []
        for _id, bid in zip(winner["chain"], winner["price"]):
            if winner["total"] == 0:
                cost = 0
            else:
                cost = float(bid / winner["total"]) * price

            commands.append((_id, cost))
        
        # print(high_index, winner["chain"][-1], price, commands)

        return high_index, winner["chain"][-1], price, commands

        # clear the conflicts that have been resolved
            # this could be done by making sure all the commands are logged, then
            # the backpressure sort will enforce decided category
        
        # output commands - list the winners and the price paid, using proportional 

    
    def secondback_helper(self, locations, invlocations, graph, bids, _id):
        """
        Assume for now that it's just one transition every time - can break this problem later
        
        Return a []
        """
        
        # take in an _id
        
        in_loc = locations[_id]
        # print("helper", _id, in_loc)
        # base case - there's no inbound to this id, so no entry in graph
        if in_loc == -1 or in_loc not in graph:
            return [{"chain": [_id], "price": [bids[_id][1]]}]
        
        # run the function on outbound locations from graph, being careful of -1
        # get # get the location from locations - inverted lookup location from locations - inverted lookup
            # duplicate a query for every outbound sector listed
        chains = []
        for out_loc in graph[in_loc]:
            # dealing with the -1 case
            out_id = None
            if out_loc == -1:

                for test_id, hex in locations.items():
                    if not out_id and hex == -1 and bids[test_id][0] == in_loc:
                        out_id = test_id
                
                # print("-1", out_id)

                chain_add = [{"chain": [out_id], "price": [bids[out_id][1]]}]

            else:   
                out_id = invlocations[out_loc]

            # print(out_id)
                chain_add = self.secondback_helper(locations, invlocations, graph, bids, out_id)
                       
            chains += chain_add
        
        
        # look up price and sum to every element of [chain, chain, ....] returned from above
            # where chain is {chain: [_ids], price: int}
        
        for chain in chains:
            chain["chain"].append(_id)
            chain["price"].append(bids[_id][1])
        
        # return that array of chains
        # print("helper", chains)
        return chains

### CYCLING AND BACKPRESSURE PART
    def find_cycles(self, graph, request, incoming = []):
        """
        Recursive function that finds the cycles active 
        """
        # if the request isn' in the graph, or all elements in [outgoing] are takeoff requests (-1)
        # or the recursion is too deep, there is no cycle and return []
        if request in graph.keys():
            new_ag = True
            for req in graph[request]:
                if req != -1:
                    new_ag = False
        
            if new_ag or len(incoming) > 50:
                return []
        else:
            return []
            
        # if request not in graph.keys() or graph[request][0] == -1 or len(incoming) > 50:
            # return []
  
        # cycle detection, you've found yourself in your own incoming chain
        if request in incoming:
            # print("req", request)
            # print("incoming", incoming)
            return incoming
        
        # recursive call, if pressures is anything it'll return the cycle
        pressures = []
        incoming.append(request)
        for req in graph[request]:
            pressures += self.find_cycles(graph, req, incoming)
        
        incoming.pop()
        return pressures
    
    
    def calc_backpressure(self, graph, request, depth = 0):
        """
        Calculate backpressure recursively, by starting from conflicted sectors
        and following inbound flights
        Inputs:
            graph: dictionary of Hex {inbound sector: [outbound sectors]}
            request: Hex of inbound sector to calculate backpressure from
            incoming: runnign record of 
            //depth: max depth of recursion
        Returns:
            out: integer of current flights following
        """
        # if the request isn' in the graph, or all elements in [outgoing] are takeoff requests (-1)
        # or the recursion is too deep, there is no cycle and return 0
        
        if request in graph.keys():
            new_ag = True
            for req in graph[request]:
                if req != -1:
                    new_ag = False
            
            if new_ag or depth > 50:
                return 0
        else:
            return 0

        # recursion to catch the rest of the pressures
        pressures = [self.calc_backpressure(graph, req, depth + 1) for req in graph[request]]
        return max(pressures) + 1
        