from itertools import cycle
from helpers import *
from grid import *

class GridCapacity(Grid):
    """
    Contains the environment, the auctioneer
    
    Grid is small grid of 6 hexagons surrounding 7th center (q, r, s)
    
    
        (0, -1, 1)   (1, -1, 0)
    (-1, 0, 1)  (0,0,0)  (1, 0, -1)
        (-1, 1, 0)   (0, 1, -1)


        (1, -1, 0)   (0, -1, 1)
    (1, 0, -1)  (0,0,0)  (-1, 0, 1)
        (0, 1, -1)   (-1, 1, 0)
    """
    
        
    def step_sim(self, locations, bids, time=None):
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
        invloc = {}   # inverse graph - points from inbound to outbound, {loc: [id, ...]}
        requests = {}   # dictionary of all locations requested and who's requesting - {loc: [(id, price), ...]}
        for loc, (_id, (next_loc, price)) in zip(locations.values(), bids.items()):

            if price == -1: continue
            assert loc == -1 or loc in self.coords, "Coordinate does not exist in the grid"
            
            # buidl the request list - essentially all the bid info the agents gave
            # right now its {location: (id, stated value)}            
            if next_loc not in requests: requests[next_loc] = []
            requests[next_loc].append((_id, price))

            # build the inverse graph
            if loc not in invloc: invloc[loc] = []
            invloc[loc].append(_id)
            
            # add to round robin priority list
            if _id not in self._roundrobin: self._roundrobin[_id] = 0

        # find cycles
        cycle_ids = self.move_cycles(bids, requests, locations)
        
        # print("cycling _id", cycle_ids)
        # clear cycles to move
        for _id in cycle_ids:
            commands[_id] = bids[_id]
        
        
            # self.track_backpressure_experimental(requests, locations, [], {}, Hex(-1,0,1), 0, Hex(-1,0,1))

        # calculate backpressure and sort - order is which sectors to deconflict first
            # NOTE: both backpressure and cycles requires building a graph at each step
        # pressures = {req: self.calc_backpressure(in_graph, req) for req in requests.keys()}     # replace pressures with the find_backpressure new function
        pressures = self.calc_backpressure(bids, requests, locations, cycle_ids, invloc)
        print(pressures)
        order = sorted(requests, key=lambda req: pressures[req][0], reverse=True)

        steps_unresolved = 0

        # handling every sector now
        # for loc in order:
        while len(order) > 0:

            loc = order[0]
            asks = requests[loc]
            # # check that all flights currently in this sector have been determined
            # if steps_unresolved < len(order):
            #     if loc in invloc and any([commands[_id][1] == -1 for _id in invloc[loc]]):
            #         order.pop(0)
            #         order.append(loc)
            #         steps_unresolved += 1
            #         continue
            if loc == Hex(-1,1,0):
                print("here")  

            # create a list of (index, price of bid)
            undecided = []
            decided = []
            for (_id, price) in asks:
                if commands[_id][1] == -1: undecided.append((_id, price))
                else: decided.append((_id, price))

            # # if the steps_unresolved is length, and you've looped to begining
            # # add the current flights to decided (assume they're on hold)
            # if steps_unresolved >= len(order):
            #     order.append(loc)
            #     for _id in invloc[loc]:
            #         decided.append((_id, 0))

            # resolve capacities
            # check if you still have capacity
            assert len(decided) <= CAPACITY, print(decided, "\n", locations, "\n", bids, "\n", commands, "\n", loc)
            if len(decided) < CAPACITY and len(undecided) > 0:
                
                # current = len(invloc[loc]) if loc in invloc and  else 0
                current = len([_id for _id in invloc[loc] if commands[_id][1] == -1]) if loc in invloc else 0
                # if you still have capacity 
                if False:
                # if len(undecided) <= CAPACITY - len(decided) - current:
                # if len(undecided) <= CAPACITY - len(decided):

                    # function for moving undin cecided into G (aka all go)
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
                    
                    # insert backpressure precalculation - helper
                    # feed this into the actual prioritization later
                    if self._priority == "secondback" or self._priority == "backpressure": 
                        # chains = self.secondback_helper(requests, locations, commands, cycle_ids, loc)
                        at_capacity = False
                        if CAPACITY - len(decided) - current == 0: at_capacity = True
                        chains = self.secondback_helper_experimental(requests, locations, commands, cycle_ids, loc, CAPACITY-len(decided)-current, 0, loc, at_capacity=at_capacity)
                        if self._priority == "secondback": 
                            chains_sort = sorted(chains, key=lambda c: (c["total"], self._roundrobin[c["chain"][-1]]), reverse=True)
                        else:
                            chains_sort = sorted(chains, key=lambda c: (len(c["chain"]), self._roundrobin[c["chain"][-1]]), reverse=True)

                    self.num_conflicts += 1
                    # while len(decided) + current < CAPACITY and len(undecided) > 0:
                    while len(decided) < CAPACITY and len(undecided) > 0 and len(chains_sort) > 0:
                        
                        #PRIORITIZATION METHODS - win returns id of winning agent
                        if self._priority == "roundrobin": 
                            win, win_id, price = self.roundrobin_prioritization(undecided)
                            undecided.pop(win)
                        elif self._priority == "backpressure": 
                            win, win_id, price, moves = self.backpressure_prioritization(undecided, chains_sort)
                            undecided.pop(win)
                        elif self._priority == "secondprice" :
                            win, win_id, price = self.secondprice_prioritization(undecided)
                            undecided.pop(win)
                        elif self._priority == "secondback":
                            win, win_id, price, moves = self.secondback_prioritization(undecided, chains_sort)
                            undecided.pop(win)
                        else: 
                            win, win_id, price = self.random_prioritization(undecided)   # PRIORITIZATION using random prioritization
                            undecided.pop(win)
        
                        # put out the commands
                        if self._priority == "secondback" or self._priority == "backpressure":
                                                        # remove the win_id from chains_sort - win_id already passied in, don't deal w/ it
                            chains_sort = [c for c in chains_sort if c["chain"][-1] != win_id]
                            
                            # update each chain by taking out moved flights
                            moves_id = [m[0] for m in moves]
                            for chain in chains_sort:
                                for k in range(len(chain['chain'])-1, -1, -1):
                                    if chain['chain'][k] in moves_id:
                                        chain['total'] -= chain['price'][k]
                                        chain['chain'].pop(k)
                                        chain['price'].pop(k)
                            
                            chains_sort = [c for c in chains_sort if len(c["chain"]) > 0]
                            if self._priority == "secondback":
                                chains_sort = sorted(chains_sort, key=lambda c: (c["total"], self._roundrobin[c["chain"][-1]]), reverse=True)
                            else:
                                chains_sort = sorted(chains_sort, key=lambda c: (len(c["chain"]), self._roundrobin[c["chain"][-1]]), reverse=True)

                            for _id, price in moves:
                                if (_id, price) in undecided:
                                    undecided.remove((_id, price))
                                    decided.append((_id, price))
                                if locations[_id] == loc:
                                    current -= 1
                                commands[_id] = (bids[_id][0], price)       
                        else:
                            commands[win_id] = (bids[win_id][0], price)
                        self._revenue += price
                        decided.append((win_id, price))
                        
            # end dealing with the sector - mark undecided as hold
            current = len([_id for _id in invloc[loc] if commands[_id][1] == -1]) if loc in invloc else 0
            if current > 0:
                for (_id, price) in undecided:
                    commands[_id] = (None, 0)
                    # self._roundrobin[_id] += 1
                    if locations[_id] in requests: requests[locations[_id]].append((_id, price))

            # remove the sector from the list
            # if it's a forced solve, add it back
            order.pop(0)
            steps_unresolved = 0


        # round robin updates + capacity check
        records = {}
        for _id, (loc, price) in commands.items():
            if price < 0:
                print('warning: flight not processed')
            if loc == None: self._roundrobin[_id] += 1
            else: self._roundrobin[_id] = 0

            temp = loc
            if temp == None: temp = locations[_id]
            if temp not in records: records[temp] = 0
            records[temp] += 1
        
        for loc, val in records.items():
            if loc != -1:
                assert val <= CAPACITY, print(val, "\n", locations, "\n", bids, "\n", commands, "\n", loc)

        # print("locs", locations)
        # print("bids", bids)
        # print("comms", commands)
        check = len([_id for _id, (loc, price) in commands.items() if loc != None])
        if check == 0:
            print("no commands")

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
        
    def backpressure_prioritization(self, undecided, chains_sorted):
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

        # take the top chain from the sorted list, pull id and price
        winner = chains_sorted[0]
        win_id = winner["chain"][-1]
        win_price = winner["price"][-1]
        
        # find the index
        win_index = undecided.index((win_id, win_price))

        # find second price
        price = chains_sorted[1]["total"] if len(chains_sorted) > 1 else 0

        # build commands for flights in the winner
        commands = []
        for _id, bid in zip(winner["chain"], winner["price"]):
            commands.append((_id, bid))

        return win_index, win_id, price, commands

        # high_press = 0
        # high_index = 0

        # # find the highest backpressure
        # for i, (_id, price) in enumerate(undecided):
        #     update = False

        #     # if hex isn't in pressures, call it 0, it's ground -1
        #     if locations[_id] not in pressures: back_press = 0
        #     else: back_press = pressures[locations[_id]]
            
        #     # check backpressure, tiebreak roundrobin
        #     if back_press > high_press:
        #         update = True
        #     elif back_press == high_press:
        #         temp = [undecided[high_index], (_id, price)]        # [current high, new high]
        #         index, _, _ = self.roundrobin_prioritization(temp)
        #         if index == 1:      # default is first instance goes
        #             update = True

        #     # update step
        #     if update:
        #         high_press = back_press
        #         high_index = i

        # (win_id, price) = undecided[high_index]
                                                                            
        # return high_index, win_id, price


    def secondprice_prioritization(self, undecided):
        """
        Sealed second price auction for locations - single square bid
    
        Inputs:
            undecided: list of tuples (_id, price) of undecided flights
        Returns:
            high_index: integer of an index in undecided
            win_id: id of winning agent
            price: price the agent pays
        """
        
        # get high bid
        high_index, winner = max(enumerate(undecided), key=lambda x:x[1][1])
        # print(undecided)
        
        # get price of second bid
        new = set(undecided)
        new.remove(winner)
    
        # if no one else no price
        if not new: price = 0
        else: price = max(new, key=lambda x: x[1])[1]
    
        return high_index, winner[0], price

    def secondback_prioritization(self, undecided, chains_sorted):
        """
        Wrapper for recursive function - stores all the backpressures
        Input:
            undecided: list of tuples (_id, price) of undecided flights
            chains_sorted: list of chains sorted by total largest at top, [{chain: [_id, ...], prices: [int, ...], total: int}, ...]
        Returns:
            high_index: integer of an index in undecided
            win_id: id of winning agent
            price: price the chain pays
            commands: commands of backpressured flights to move, [(id, cost), ...]
        """

        # take the top chain from the sorted list, pull id and price
        winner = chains_sorted[0]
        win_id = winner["chain"][-1]
        win_price = winner["price"][-1]
        
        # find the index
        win_index = undecided.index((win_id, win_price))

        # find second price
        price = chains_sorted[1]["total"] if len(chains_sorted) > 1 else 0

        # build commands for flights in the winner
        commands = []
        for _id, bid in zip(winner["chain"], winner["price"]):
            if winner["total"] == 0:
                cost = 0
            else:
                cost = float(bid / winner["total"]) * price     # proportional payment
            commands.append((_id, cost))

        return win_index, win_id, price, commands

    
    def secondback_helper(self, requests, locations, commands, cycle_ids, origin, origin_spares, origin_count, req_loc, temp_chain=[]):
        """
        Recursion that actually calculates backpressure
        Works by iterating through id requesting in req_loc and tracing all chains leading to that id
        Input:
            requests: array of {loc: [(id, price), ...]}
            locations: locations of agents {id: loc}
            cycle_ids: all _ids in cycles, [_id, ...] 
            req_loc: requested location, loc
        Returns:
            output: list of chains, [{chain: [_id, ...], prices: [int, ...], total: int}, ...]
        """
        chains = []

        # base case - if no one's interested in req_loc (aka not in requests, includes -1) (cycling covered at bottom)
        if req_loc not in requests:
            chains.append({'chain': [], 'price': [], 'total': 0})
            return chains

        # # if you loop on yourself, return 0 at this level
        # if req_loc in temp_chain:
        #     chains.append({'chain': [], 'price': [], 'total': 0})
        #     return chains
                # if you're the head of the search

        # recursion call - add every _id requesting to you to the list of chains given by location[_id]
        temp_tracking = {}      # temporary chain tracking of {loc: chains}, so that we don't redo recursion if a loc shows up again
        current = 0
        for _id, price in requests[req_loc]:

            # check not in cycles and already moved
            # check if _id is in chain - then it's already been chained in
            # check if _id is already at this location - then it's a delayed flight
            # check if _id has a command - then it's been decided previously
            if _id in cycle_ids or _id in temp_chain or locations[_id] == req_loc or commands[_id][1] > -1: 
                continue
            
            # keep a counter - check if this locaiton has already been dragged enough times
        
            # get the next location
            prev_loc = locations[_id]

        
            if prev_loc == -1:  # if next location is ground base case
                temp_tracking[prev_loc] = [{'chain': [], 'price': [], 'total': 0}]
            else:
                temp_chain.append(_id)
                temp_tracking[prev_loc] = self.secondback_helper(requests, locations, commands, cycle_ids, prev_loc, temp_chain)
                temp_chain.pop(-1)

            # pull out chains on that location and check
            for chain in temp_tracking[prev_loc]:
                # deepcopy the chain
                temp = deepcopy(chain)
    
                # alter the chains with current _id
                temp['chain'].append(_id)
                temp['price'].append(price)
                temp['total'] += price

                # add the altered chain to chains
                chains.append(temp)

        # base case - if there's no chain, everyone requesting is cycled
        if len(chains) == 0:
            chains.append({'chain': [], 'price': [], 'total': 0})

        return chains

    def secondback_helper_experimental(self, requests, locations, commands, cycle_ids, origin, origin_spares, origin_count, req_loc, temp_chain=[], at_capacity=False):
        """
        Recursion that actually calculates backpressure
        Works by iterating through id requesting in req_loc and tracing all chains leading to that id
        Input:
            requests: array of {loc: [(id, price), ...]}
            locations: locations of agents {id: loc}
            cycle_ids: all _ids in cycles, [_id, ...] 
            req_loc: requested location, loc
        Returns:
            output: list of chains, [{chain: [_id, ...], prices: [int, ...], total: int}, ...]
        """
        chains = []

        # base case - if no one's interested in req_loc (aka not in requests, includes -1) (cycling covered at bottom)
        if req_loc not in requests:
            chains.append({'chain': [], 'price': [], 'total': 0})
            return chains

        # # if you loop on yourself, return 0 at this level
        # if req_loc in temp_chain:
        #     chains.append({'chain': [], 'price': [], 'total': 0})
        #     return chains
                # if you're the head of the search
        new_origin_count = origin_count
        if req_loc == origin:
            # if origin_count >= CAPACITY + origin_spares:
            if origin_count >= CAPACITY:
                chains.append({'chain': [], 'price': [], 'total': 0})
                return chains
            new_origin_count += 1

        # recursion call - add every _id requesting to you to the list of chains given by location[_id]
        temp_tracking = {}      # temporary chain tracking of {loc: chains}, so that we don't redo recursion if a loc shows up again
        current = 0
        for _id, price in requests[req_loc]:

            # check not in cycles and already moved
            # check if _id is in chain - then it's already been chained in
            # check if _id is already at this location - then it's a delayed flight
            # check if _id has a command - then it's been decided previously
            if _id in cycle_ids or _id in temp_chain or locations[_id] == req_loc or commands[_id][1] > -1: 
                continue
            
            # keep a counter - check if this locaiton has already been dragged enough times
        
            # get the next location
            prev_loc = locations[_id]

            if prev_loc == -1:  # if next location is ground base case
                temp_tracking[prev_loc] = [{'chain': [], 'price': [], 'total': 0}]
            else:
                temp_chain.append(_id)
                temp_tracking[prev_loc] = self.secondback_helper_experimental(requests, locations, commands, cycle_ids, origin, origin_spares, new_origin_count, prev_loc, temp_chain)
                temp_chain.pop(-1)

            # pull out chains on that location and check
            for chain in temp_tracking[prev_loc]:
                # deepcopy the chain
                temp = deepcopy(chain)
    
                # alter the chains with current _id
                temp['chain'].append(_id)
                temp['price'].append(price)
                temp['total'] += price

                # add the altered chain to chains
                chains.append(temp)

        # base case - if there's no chain, everyone requesting is cycled
        if len(chains) == 0:
            chains.append({'chain': [], 'price': [], 'total': 0})
        
        # postprocessing at top of recursion, only care if we're at capacity
        if req_loc == origin and origin_count == 0 and at_capacity:
            for i in range(len(chains)-1, -1, -1):
                if len(chains[i]['chain']) > 0:
                    # this is tracking exits - if at capacity need as many exits as entries
                    origin_exits = [j for j in range(len(chains[i]['chain'])) if locations[chains[i]['chain'][j]] == req_loc]
                    if len(origin_exits) == 0:      # if there are no exits, remove this pressure
                        chains.pop(i)
                    elif origin_exits[0] > 0:     # if there are exits but excess flights after, remove the excess
                        chains[i]['chain'] = chains[i]['chain'][origin_exits[0]:]
                        # chains['chain'][i] = (origin_exits[-1]+1, pressures[i][1][:origin_exits[-1]+1])

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

        # cycles must 1. have req_loc filled to capacity, 2. all agents point to same place
        if len(sectors[req_loc]) != CAPACITY:
            return []
        
        important_loc = None
        for _id in sectors[req_loc]:
            next_loc = bids[_id][0]     # pulling out the next location
            if important_loc is None:
                important_loc = next_loc
            elif important_loc != next_loc:
                return []

        # recursive: run backward until you find yourself
        pressures = [] 
        for _id in sectors[req_loc]:        # CONSIDER - sort this by price, move highest value first in cycle
            if _id in scanned: continue

            incoming[0].append(req_loc)        # add to chain - PRIORITIZATION IS RANDOM rn
            incoming[1].append(_id)        

            pressures += self.find_cycles(important_loc, sectors, bids, scanned, incoming)

            if len(pressures) > 0:      # if cycle found len(pressures) > 0, all ids record as scanned
                for _id in pressures:
                    scanned.add(_id)
                break        

            incoming[0].pop()       # pop off the end that we added
            incoming[1].pop()
            scanned.add(_id)        # add to set of scanned ids

        return pressures

    
    def calc_backpressure(self, bids, requests, locations, cycle_ids, invloc):
        """
        Wrapper for recursive function - stores all the backpressures
        Input:
            bids: all active agent bids {id : (next_loc, price)}
            requests: array of {loc: [(id, price), ...]}
            locations: locations of agents {id: loc}
            cycle_ids: all _ids in cycles, [_id, ...]
            invloc: inverse loactions of agents {loc: [id, ...]}
        Returns:
            backpressures: dict of backpressures at requests {req (Hex): backpressure (int)}
        """

        # method 2 - smarter DP ideally
        backpressures = {}
        for req_loc, _ in requests.items():       # have to check backpressure on every single sector
            
                #[Hex(1,-2,1), Hex(0,-1,1), Hex(0,0,0), Hex(0,0,0), Hex(2,-2,0), Hex(-1,0,1)]
            # if req_loc in [locations[299], locations[409], locations[255],locations[403],locations[372],locations[367]]:

            # if req_loc in backpressures: 
            #     continue   # DP check if we have a value already

            # if there's no spare capacity at the location skip
            at_capacity = False
            if req_loc in invloc and len(invloc[req_loc]) >= CAPACITY:
                at_capacity = True

            # if req_loc == locations[41]:
            #     print("here")

            # feed into track_backpressure 
            # pressure = self.track_backpressure(requests, locations, cycle_ids, backpressures, req_loc)
            # backpressures[req_loc] = pressure
            pressures = self.track_backpressure_experimental(requests, locations, cycle_ids, backpressures, req_loc, 0, req_loc, at_capacity=at_capacity)
            backpressures[req_loc] = max(pressures, key=lambda tup: tup[0])

        # check that all sectors have some backpressure recorded
        # for req_loc, _ in requests.items():
            # if req_loc == Hex(0,0,0):
            #     print('test')
            # if req_loc in invloc and len(set(invloc[req_loc]).intersection(cycle_ids)) == CAPACITY:
            #     backpressures[req_loc] = (0, [])
            # elif req_loc not in backpressures:
            #     backpressures[req_loc] = (0, [])
        return backpressures 


    def track_backpressure(self, requests, locations, cycle_ids, backpressures, req_loc, temp_chain=[]):
        """
        Go backwards - req_loc is location we are asking for, prev_loc is the locations we're at
        Go backwards on the arrows
        Input:
            requests: array of {loc: [(id, price), ...]}
            locations: locations of agents {id: loc}
            cycle_ids: all _ids in cycles, [_id, ...]
            backpressures: dict for shortcut on sectors, {loc: int}
            req_loc: requested location, loc
            temp_chain: chain of id's on this backpressure track, [id, ...]
        Returns:
            output: the pressure at req_loc, int
        """
        assert req_loc != -1  # check that requested location isn' ground - otherwise infinite recursion

        # base case - if you're not in requests (but not cycled, checked in layer above), return 0
        if req_loc not in requests:
            backpressures[req_loc] = (0,[])
            return (0, [])

        # # if you loop on yourself, return 0 at this level
        # if req_loc in temp_chain:
        #     return 0

        # temp_chain.append(req_loc)
        pressures = [(0, [])]     # default pressure 0
        for _id, price in requests[req_loc]:        

            prev_loc = locations[_id]        # find location of the _id     
            if prev_loc == -1: continue      # if the next location is ground skip recursion

            if _id in cycle_ids or _id in temp_chain: continue       # check if _id is in a cycle - skip if so
            # if prev_loc in backpressures and backpressures[prev_loc] != None:        # check if this _id's has a backpressure associated
            #     pressures.append(backpressures[prev_loc])
            #     continue
            
            temp_chain.append(_id)
            # temp = deepcopy(temp_chain)
            # backpressures[req_loc] = None
            # jump to that location - recursion
            temp = self.track_backpressure(requests, locations, cycle_ids, backpressures, prev_loc, temp_chain=temp_chain)
            pressures.append((temp[0]+1, temp[1] + [_id]))
            temp_chain.pop(-1)
        
        # temp_chain.pop(-1)
        # output, store to backpressures
        output = max(pressures, key=lambda tup: tup[0])
        if req_loc not in backpressures or output[0] > backpressures[req_loc][0]:
            backpressures[req_loc] = output

        return output

    def track_backpressure_experimental(self, requests, locations, cycle_ids, backpressures, origin, origin_count, req_loc, temp_chain=[], at_capacity=False):
        """
        Go backwards - req_loc is location we are asking for, prev_loc is the locations we're at
        Go backwards on the arrows
        Input:
            requests: array of {loc: [(id, price), ...]}
            locations: locations of agents {id: loc}
            cycle_ids: all _ids in cycles, [_id, ...]
            backpressures: dict for shortcut on sectors, {loc: int}
            req_loc: requested location, loc
            temp_chain: chain of id's on this backpressure track, [id, ...]
        Returns:
            output: the pressure at req_loc, int
        """
        assert req_loc != -1  # check that requested location isn' ground - otherwise infinite recursion

        # base case - if you're not in requests (but not cycled, checked in layer above), return 0
        if req_loc not in requests:
            # backpressures[req_loc] = (0,[])
            return [(0, [])]

        # if you're the head of the search, no extra entries
        new_origin_count = origin_count
        if req_loc == origin:
            if origin_count >= CAPACITY:
                # backpressures[req_loc] = (0,[])
                return [(0, [])]
            new_origin_count += 1

        # # if you loop on yourself, return 0 at this level
        # if req_loc in temp_chain:
        #     return 0

        # temp_chain.append(req_loc)
        pressures = [(0, [])]     # default pressure 0
        for _id, price in requests[req_loc]:        

            prev_loc = locations[_id]        # find location of the _id     
            if prev_loc == -1: continue      # if the next location is ground skip recursion

            if _id in cycle_ids or _id in temp_chain: continue       # check if _id is in a cycle - skip if so
            # if prev_loc in backpressures and backpressures[prev_loc] != None:        # check if this _id's has a backpressure associated
            #     pressures.append(backpressures[prev_loc])
            #     continue
            
            temp_chain.append(_id)
            # temp = deepcopy(temp_chain)
            # backpressures[req_loc] = None
            # jump to that location - recursion
            temp = self.track_backpressure_experimental(requests, locations, cycle_ids, backpressures, origin, new_origin_count, prev_loc, temp_chain=temp_chain)
            for i in range(len(temp)):
                pressures.append((temp[i][0]+1, deepcopy(temp[i][1]) + [_id]))
            temp_chain.pop(-1)
        
        # # postprocessing at top of recursion, only care if we're at capacity
        # if req_loc == origin and origin_count == 0 and at_capacity:
        #     for i in range(len(pressures)-1, -1, -1):
        #         if pressures[i][0] > 0:
        #             # this is tracking exits - if at capacity need as many exits as entries
        #             origin_exits = [j for j in range(len(pressures[i][1])) if locations[pressures[i][1][j]] == req_loc]
        #             if len(origin_exits) == 0:      # if there are no exits, remove this pressure
        #                 pressures.pop(i)
        #             elif origin_exits[0] > 0:     # if there are exits but excess flights after, remove the excess
        #                 cut = pressures[i][1][origin_exits[0]:]
        #                 pressures[i] = (len(cut), cut)

                    

        # temp_chain.pop(-1)
        # output, store to backpressures
        # output = max(pressures, key=lambda tup: tup[0])
        # if req_loc not in backpressures or output[0] > backpressures[req_loc][0]:
        #     backpressures[req_loc] = output

        return pressures