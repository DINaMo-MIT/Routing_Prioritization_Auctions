from helpers import *
from grid import *

class GridCapacity(Grid):
    """
    Contains the environment, the auctioneer
    
    Grid is small grid of 6 hexagons surrounding 7th center (q, r, s)
    
    
        (0, -1, 1)   (1, -1, 0)
    (-1, 0, 1)  (0,0,0)  (1, 0, -1)
        (-1, 1, 0)   (0, 1, -1)


        (-1, 1, 0)   (0, 1, -1)
    (-1, 0, 1)  (0,0,0)  (1, 0, -1)
        (0, -1, 1)   (1, -1, 0)
    """
    
        
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
        requests = {}   # dictionary of all locations requested and who's requesting - {loc: [(id, price), ...]}
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
        assert 1==1
        # find cycles
        cycle_ids = self.move_cycles(bids, requests, locations)
        
        # print("cycling _id", cycle_ids)
        # clear cycles to move
        for _id in cycle_ids:
            commands[_id] = bids[_id]
        
        
        # calculate backpressure and sort - order is which sectors to deconflict first
            # NOTE: both backpressure and cycles requires building a graph at each step
        # pressures = {req: self.calc_backpressure(in_graph, req) for req in requests.keys()}     # replace pressures with the find_backpressure new function
        pressures = self.calc_backpressure(bids, requests, locations, cycle_ids)
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
            assert len(decided) <= CAPACITY, print(decided, "\n", locations, "\n", bids, "\n", commands, "\n", loc)
            if len(decided) < CAPACITY:
                
                # if you still have capacity 
                if len(undecided) <= CAPACITY - len(decided):

                    # function for moving undecided into G (aka all go)
                    # the 4 line block is the key
                    # assert bids[i][0] == loc
                    for i in range(len(undecided)):
                        (win_i, price) = undecided[i]
                        commands[win_i] = (bids[win_i][0], 0)   # append comamnd
                        self._revenue += 0
                        decided.append((win_i, price))
                    
                    undecided = []      # clear the entire list

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
                            win, win_id, price = self.backpressure_prioritization(undecided, locations, pressures)
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
                # self._roundrobin[_id] += 1
                if locations[_id] in requests: requests[locations[_id]].append((_id, price))

        # round robin updates
        for _id, (loc, price) in commands.items():
            assert price >= 0
            if loc == None: self._roundrobin[_id] += 1
            else: self._roundrobin[_id] = 0

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
        # if there's a seed use it
        if seed: rand = np.random.default_rng(seed)
        elif self.seed: rand = np.random.default_rng(self.seed)
        else: rand = np.random.default_rng()
        
        win = rand.integers(len(undecided))
        (win_id, price) = undecided[win]
                                                                             
        return win, win_id, price
    
    def roundrobin_prioritization(self, undecided):
        """
        Trying to set up round robin prioritization around the grid
        DEFAULT - If tied, first instance in undecided gets to go
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
        
    def backpressure_prioritization(self, undecided, locations, pressures):
        """
        Using backpressure to resolve conflicts
        Inputs:
            undecided: list of tuples (_id, price) of undecided flights
            locations: {id:Hex} dictionary of all locations of agents
            pressures: dictionary of hex and backpressure on hex {loc (Hex): backpressure (int)}
        Returns:
            high_index: integer of an index in undecided
            win_id: id of winning agent
            price: price the agent pays
        """
        
        high_press = 0
        high_index = 0
        # high_id = -1
        # high_robin = 0
        
        # find the highest backpressure
        for i, (_id, price) in enumerate(undecided):
            # back_press = self.calc_backpressure(graph, locations[_id])
            # back_press = self.calc_backpressure(bids, requests, locations, cycle_ids)
            update = False

            # if hex isn't in pressures, call it 0, it's ground -1
            if locations[_id] not in pressures: back_press = 0
            else: back_press = pressures[locations[_id]]
            
            # check backpressure, tiebreak roundrobin
            if back_press > high_press:
                update = True
            elif back_press == high_press:
                temp = [undecided[high_index], (_id, price)]
                index, _, _ = self.roundrobin_prioritization(temp)
                if index == 1:      # default is first instance goes
                    update = True

            # update step
            if update:
                high_press = back_press
                high_index = i
                # high_id = _id

            # if back_press > high_press or (back_press == high_press and self._roundrobin[_id] > high_robin):    
            #     high_press = back_press
            #     high_index = i
            #     high_id = _id
            #     high_robin = self._roundrobin[_id]
       
        (win_id, price) = undecided[high_index]
                                                                            
        return high_index, win_id, price
    
    def secondprice_prioritization(self, undecided):
        """
        Sealed second price auction for locations - single square bid
    
        Inputs:
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
    def move_cycles(self, bids, requests, locations):
        """
        Function finding all agents that get free pass to move as part of cycle
        Input:
            bids: all active agent bids {id : (next_loc, price)}
            requests: array of {loc: [(id, price), ...]}
            locations: {id: loc}
        Output:
            cycle_ids: [_ids], list of all _ids that get priority move
        """
        
        sectors = {}    # turn from requests to {loc: [id, ...]}
        for (_id, loc) in locations.items():
            if loc not in sectors: sectors[loc] = []
            sectors[loc].append(_id)

        scanned = set()

        # start searching through the list
        cycle_ids = []
        count = 0
        for (_id, req_loc) in locations.items():
            if req_loc == -1 or _id in scanned: continue     # check that this location hasn't been scanned in other parts
            count += 1
            cycle_ids += self.find_cycles(req_loc, sectors, bids, scanned, [[],[]])     # call recursion and search

        return cycle_ids
    

    def find_cycles(self, req_loc, sectors, bids, scanned, incoming=[[],[]]):
        """
        Recursive function finding the cycles - NOTE, WHY NOT USE LOCATIONS/REQUESTS AND BUILD BACKWARDS SEARCH?
        Input:
            req_loc: next_loc, the requested sector
            # requests: array of {loc: [(id, price), ...]}
            sectors: agents at which location, {loc: [id, ...]} 
            bids: all active agent bids, {id : (next_loc, price)}
            scanned: set of all flights already scanned, {id, ...}
            incoming: a chain of requested sectors and ids, [[loc, ...],[id, ...]]
        Output:
            pressures: array of ids representing the cycle, [id, ...]
        """
        # skip req_loc == -1
        assert req_loc != -1

        # base case: there are no flights here
        if req_loc not in sectors:
            return []

        # cycle detection: you've found yourself in your own incoming chain
        if req_loc in incoming[0]:
            # print("req", request)
            # print("incoming", incoming)

            cut = incoming[0].index(req_loc)    # cut out the loop itself, ignore the other pieces - consider try/except for runtime improvement
            return incoming[1][cut:]

        # recursive: run backward until you find yourself
        pressures = []      # should track id's
        for _id in sectors[req_loc]:
            # [IMPLEMENT] chekc if this _id has been checked already
            if _id in scanned: continue

            incoming[0].append(req_loc)        # add to chain - PRIORITIZATION IS RANDOM rn
            incoming[1].append(_id)        

            next_loc = bids[_id][0]     # pulling out the next location
            pressures += self.find_cycles(next_loc, sectors, bids, scanned, incoming)

            if len(pressures) > 0: 
                for _id in pressures:
                    scanned.add(_id)
                break        # if cycle found len(pressures) > 0, remove all ids in that cycle

            incoming[0].pop()       # pop off the end that we added
            incoming[1].pop()
            scanned.add(_id)        # add to set of scanned ids

        return pressures

    
    def calc_backpressure(self, bids, requests, locations, cycle_ids):
        """
        Wrapper for recursive function - stores all the backpressures
        Input:
            bids: all active agent bids {id : (next_loc, price)}
            requests: array of {loc: [(id, price), ...]}
            locations: locations of agents {id: loc}
            cycle_ids: all _ids in cycles, [_id, ...]
        Returns:
            backpressures: dict of backpressures at requests {req (Hex): backpressure (int)}
        """

        # method 2 - smarter DP ideally
        backpressures = {}
        for req_loc, _ in requests.items():       # have to check backpressure on every single sector

            if req_loc in backpressures: continue   # DP check if we have a value already

            # feed into track_backpressure 
            pressure = self.track_backpressure(requests, locations, cycle_ids, backpressures, req_loc)
            backpressures[req_loc] = pressure

        return backpressures 

    def track_backpressure(self, requests, locations, cycle_ids, backpressures, req_loc):
        """
        Input:
            requests: array of {loc: [(id, price), ...]}
            locations: locations of agents {id: loc}
            cycle_ids: all _ids in cycles, [_id, ...]
            backpressures: dict for shortcut on sectors, {loc: int}
            req_loc: requested location, loc
        Returns:
            output: the pressure at req_loc, int
        """
        assert req_loc != -1  # check that requested location isn' ground - otherwise infinite recursion

        # base case - if you're not in requests (but not cycled, checked in layer aboe), return 0
        if req_loc not in requests:
            backpressures[req_loc] = 0
            return 0

        pressures = [0]     # default pressure 0
        for _id, price in requests[req_loc]:

            cur_loc = locations[_id]        # find location of the _id     
            if cur_loc == -1: continue      # if the next location is ground skip recursion

            if _id in cycle_ids: continue       # check if _id is in a cycle - skip if so
            if _id in backpressures:        # check if this _id's has a backpressure associated
                pressures.append(backpressures[_id])
                continue

            # if cur_loc isn't in requests, it's not being requested and backpressure is 0
            # if cur_loc not in requests:
            #     backpressures[cur_loc] = 0
            #     continue

            # jump to that location - recursion
            pressures.append(self.track_backpressure(requests, locations, cycle_ids, backpressures, cur_loc))
        
        # output, store to backpressures
        output = max(pressures) + 1
        backpressures[req_loc] = output
        return output