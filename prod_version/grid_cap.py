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


        (-1, 1, 0)   (0, 1, -1)
    (-1, 0, 1)  (0,0,0)  (1, 0, -1)
        (0, -1, 1)   (1, -1, 0)
    """
    
        
    def step_sim(self, locations, bids, active):
        """
        Step through one step of Chris's protocol - this handles cycles on until hold/motion (lines 4 to 24 in Alg 1)
        Inputs:
            locations: {id : loc} all active agent locations (if you're trying to depart also active)
            bids: {id : (next_loc, price)} all active agent bids
            active: list of active agents (added to calculate accrued delay)
        Returns:
            commands: dictionary of tuples {id : (next loc, winning price)} of size (# agents) (None, 0) means hold
        """
        # price = -1 means it's still undecided 
        # price = 0 means it's on hold
        # init commands
        commands = {_id: (None, -1) for (_id, (_, _)) in bids.items()}
        
        # build node graph - all departing flights are treated as coming from one massive ground node -1
        # invloc = {}   # inverse graph - points from inbound to outbound, {loc: [id, ...]}
        requests = {}   # dictionary of all locations requested and who's requesting - {loc: [(id, price), ...]}
        for loc, (_id, (next_loc, price)) in zip(locations.values(), bids.items()):

            if price == -1: continue
            assert loc == -1 or loc in self.coords, "Coordinate does not exist in the grid"
            
            # buidl the request list - essentially all the bid info the agents gave
            # right now its {location: (id, stated value)}            
            if next_loc not in requests: requests[next_loc] = []
            requests[next_loc].append((_id, price))
            
            # add to round robin priority list
            if _id not in self._roundrobin: self._roundrobin[_id] = 0

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
            # asks = requests[loc]
            asks = sorted(requests[loc], key=lambda x: x[0], reverse=False)
            if len(asks) >= 2:
                assert 1 == 1
            reversed = []       # list of agents that experienced reversal
            
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
                    
                    # insert backpressure precalculation - helper
                    # feed this into the actual prioritization later
                    if self._priority == "secondback": 
                        chains = self.secondback_helper(requests, locations, commands, cycle_ids, loc)
                        chains_sort = sorted(chains, key=lambda c: (c["total"], self._roundrobin[c["chain"][-1]]), reverse=True)

                    self.num_conflicts += 1
                    while len(decided) < CAPACITY:
                        
                        #PRIORITIZATION METHODS - win returns id of winning agent
                        if self._priority == "roundrobin": 
                            win, win_id, price = self.roundrobin_prioritization(undecided)
                            undecided.pop(win)
                        elif self._priority == "backpressure": 
                            win, win_id, price = self.backpressure_prioritization(undecided, locations, pressures)
                            undecided.pop(win)
                        elif self._priority == 'accrueddelay':
                            tiebreak, win, win_id, price, undecided_with_max = self.accrueddelay_prioritization(undecided, active)
                            if tiebreak:
                                win, win_id, price = self.backpressure_prioritization(undecided, locations, pressures, undecided_with_max=undecided_with_max)
                            undecided.pop(win)
                        elif self._priority == 'reversals':
                            tiebreak, win, win_id, price, undecided_with_max = self.reversals_prioritization(undecided, active)
                            if tiebreak:
                                win, win_id, price = self.backpressure_prioritization(undecided, locations, pressures, undecided_with_max=undecided_with_max)
                            undecided.pop(win)
                        elif self._priority == "secondprice" :
                            tiebreak, ties, win, win_id, price = self.secondprice_prioritization(undecided)
                            if tiebreak:
                                win, win_id, price = self.backpressure_prioritization(ties, locations, pressures)
                            assert win != None and win_id != None and price != None
                            undecided.pop(win)
                        elif self._priority == "secondback":
                            win, win_id, price, moves = self.secondback_prioritization(undecided, chains_sort)
                            undecided.pop(win)
                            
                            # remove the win_id from chains_sort - win_id already passed in, don't deal w/ it
                            chains_sort = [c for c in chains_sort if c["chain"][-1] != win_id]
                            
                            # update each chain by taking out moved flights
                            moves_id = [m[0] for m in moves]
                            for chain in chains_sort:
                                for k in range(len(chain['chain'])-1, -1, -1):
                                    if chain['chain'][k] in moves_id:
                                        chain['total'] -= chain['price'][k]
                                        chain['chain'].pop(k)
                                        chain['price'].pop(k)
                            chains_sort = sorted(chains_sort, key=lambda c: (c["total"], self._roundrobin[c["chain"][-1]]), reverse=True)
                        else: 
                            win, win_id, price = self.random_prioritization(undecided)   # PRIORITIZATION using random prioritization
                            undecided.pop(win)

                        if price == -1:
                            pass
        
                        if loc == Hex(1,-1,0):
                            pass
                        reversed = self.update_reversed(active, win_id, undecided, loc, reversed)

                        # put out the commands
                        if self._priority == "secondback":
                            for _id, price in moves:
                                commands[_id] = (bids[_id][0], price)       
                        else:
                            commands[win_id] = (bids[win_id][0], price)
                        self._revenue += price
                        decided.append((win_id, price))

            # end dealing with the sector - mark undecided as hold
            for (_id, price) in undecided:
                commands[_id] = (None, 0)
                # self._roundrobin[_id] += 1
                if locations[_id] in requests: requests[locations[_id]].append((_id, price))
                
                # increment accrued delay of held agents by 1
                # if self._priority == 'accrueddelay' and len(undecided) > 0:
                #     for (ag_id, _) in undecided:
                ag_index = [x._id for x in active].index(_id)
                active[ag_index].accrued_delay += 1

                # increment reversals of agents in reversed *and* undecided by 1
                if _id in reversed:     # vehicle in reversed (list of agents that might've experienced reversal)
                    ag_index = [x._id for x in active].index(_id)
                    active[ag_index].reversals += 1

        # round robin updates - reset if they move
        records = {}
        for _id, (loc, price) in commands.items():
            assert price >= 0   # assert everyone has been assigned an action, go or hold
            if loc == None: self._roundrobin[_id] += 1
            else: self._roundrobin[_id] = 0

            # records for capacity check later
            temp = loc
            if temp == None: temp = locations[_id]
            if temp not in records: records[temp] = 0
            records[temp] += 1
        
        # Check that the capacity is not exceeded
        for loc, val in records.items():
            if loc != -1:
                assert val <= CAPACITY, print(val, locations, "\n", bids, "\n", commands, "\n", loc)

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
        # self._roundrobin[undecided[high_index][0]] = 0
        (win_id, price) = undecided[high_index]
                                                                             
        return high_index, win_id, price
        
    def backpressure_prioritization(self, undecided, locations, pressures, undecided_with_max = []):
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
        # filter based on undecided_with_max
        if len(undecided_with_max) > 0:
            filterMax = True
        else:
            filterMax = False

        high_press = 0
        high_index = 0

        # find the highest backpressure
        for i, (_id, price) in enumerate(undecided):
            
            # skip ids not in undecided_with_max
            if filterMax:
                if _id not in undecided_with_max:
                    continue

            update = False

            # if hex isn't in pressures, call it 0, it's ground -1
            if locations[_id] not in pressures: back_press = 0
            else: back_press = pressures[locations[_id]]
            
            # check backpressure, tiebreak roundrobin
            if back_press > high_press:
                update = True

            elif back_press == high_press and i > 0:
                print('roundrobin tiebreak')
                temp = [undecided[high_index], (_id, price)]
                index, _, _ = self.roundrobin_prioritization(temp)
                if index == 1:      # default is first instance goes
                    update = True

            # update step
            if update:
                high_press = back_press 
                high_index = i

        (win_id, price) = undecided[high_index]

        # tiebreaker checker w/ backpressure and roundrobin
        if False:
            for i, (_id, price) in enumerate(undecided):
                if _id == win_id: pass
                elif locations[_id] == -1 and locations[win_id] == -1:      # if _id and win_id are both -1, then check roundrobin then _id 
                    assert (
                        win_id < _id or
                        self._roundrobin[win_id] > self._roundrobin[_id] 
                    )
                elif locations[_id] == -1 and locations[win_id] != -1:      # if _id is -1 and win_id is not, then win_id should win anyways
                    pass
                elif locations[_id] != -1 and locations[win_id] != -1:      # if _id and win_id are not -1, check pressures then roundrobin then  _id
                    assert (
                        pressures[locations[win_id]] > pressures[locations[_id]] or 
                        self._roundrobin[win_id] > self._roundrobin[_id] or 
                        win_id < _id
                    )
                                                                            
        return high_index, win_id, price

    def accrueddelay_prioritization(self, undecided, active):
        """
        Using accrued delay to resolve conflicts
        Inputs:
            undecided: list of tuples (_id, price) of undecided flights
            active: list of active agents
        Returns:
            tiebreak: Bool of tie between agents in accrued delay 
            high_index: integer of an index in undecided
            win_id: id of winning agent
            price: price the agent pays
            undecided_with_max: subset of undecided that have max accrued delay value (only nonempty when there's a tie)
        """

        # Create ad_list: list of tuples (_id, accrued_delay) of undecided flights
        ad_list = []
        for (id, price) in undecided:
            ag = [x for x in active if x._id == id][0]
            ad_list.append((id, ag.accrued_delay))

        # Collect list of ids that have max accrued delay value
        max_ad = max([x[1] for x in ad_list])
        ad_list_max = [tup for tup in ad_list if tup[1] == max_ad]
        ad_list_ids = [x[0] for x in ad_list_max]
        if len(ad_list_max) == 0:
            raise ValueError
        elif len(ad_list_max) == 1:
            tiebreak = False
        else:
            tiebreak = True

        # if not a tie, return high_index, win_id 
        if tiebreak == False:
            high_index = [x[0] for x in undecided].index(ad_list_max[0][0])
            (win_id, price) = undecided[high_index]

            # dummy value for undecided_with_max_ad
            undecided_with_max = []
        # if tie, return undecided_with_max_ad
        else:
            # dummy values if tied
            high_index = -1
            win_id = -1
            price = -1

            # filter undecided list to those that have max accrued delay
            undecided_with_max = [x[0] for x in undecided if x[0] in ad_list_ids]
                                                                            
        return tiebreak, high_index, win_id, price, undecided_with_max


    def reversals_prioritization(self, undecided, active):
        """
        Using reversals to resolve conflicts
        Inputs:
            undecided: list of tuples (_id, price) of undecided flights
            active: list of active agents
            reversed: list of agents that might have experienced schedule reversal
        Returns:
            tiebreak: Bool of tie between agents in reversals
            high_index: integer of an index in undecided
            win_id: id of winning agent
            price: price the agent pays
            undecided_with_max: subset of undecided that have max reversals value (only nonempty when there's a tie)
        """
        # Create rev_list: list of tuples (_id, reversals) of undecided flights
        rev_list = []
        for (id, price) in undecided:
            ag = [x for x in active if x._id == id][0]
            rev_list.append((id, ag.reversals))

        # Collect list of ids that have max reversals value
        max_rev = max([x[1] for x in rev_list])
        rev_list_max = [tup for tup in rev_list if tup[1] == max_rev]
        rev_list_ids = [x[0] for x in rev_list_max]
        if len(rev_list_max) == 0:
            raise ValueError
        elif len(rev_list_max) == 1:
            tiebreak = False
        else:
            tiebreak = True

        # if not a tie, return high_index, win_id 
        if tiebreak == False:
            high_index = [x[0] for x in undecided].index(rev_list_max[0][0])
            (win_id, price) = undecided[high_index]

            # dummy value for undecided_with_max_ad
            undecided_with_max = []
        # if tie, return undecided_with_max_ad
        else:
            # dummy values if tied
            high_index = -1
            win_id = -1
            price = -1

            # filter undecided list to those that have max accrued delay
            undecided_with_max = [x[0] for x in undecided if x[0] in rev_list_ids]
                                                                            
        return tiebreak, high_index, win_id, price, undecided_with_max

    def update_reversed(self, active, win_id, undecided, loc, reversed):
        # find scheduled arrival time at this sector for win_id
        win_ag = [x for x in active if x._id == win_id][0]
        win_schedule_t_step = win_ag._schedule_t_steps[win_ag._steps.index(loc)]

        # update reversed list
        for (this_id, _) in undecided:
            if this_id == win_id:        # skip win_id
                continue

            # find scheduled arrival time at this sector for this_id
            this_ag = [x for x in active if x._id == this_id][0]
            this_schedule_t_step = this_ag._schedule_t_steps[this_ag._steps.index(loc)]

            # record schedule reversal if this_id supposed to arrive before win_id
            if this_schedule_t_step < win_schedule_t_step:
                reversed.append(this_id)

        return reversed

    
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
        
        print(undecided)

        # check for ties, bounce out to backpressure if so
        temp = deepcopy(sorted(undecided, key=lambda x: x[1], reverse=True))
        temp = [x for x in temp if x[1] == temp[0][1]]
        if len(temp) > 1:
            return True, temp, None, None, None

        print(undecided)

        # get high bid
        high_index, winner = max(enumerate(undecided), key=lambda x:x[1][1])
        # print(undecided)
        
        # get price of second bid
        new = set(undecided)
        new.remove(winner)
    
        # if no one else no price
        if not new: price = 0
        else: price = max(new, key=lambda x: x[1])[1]
    
        assert price >= 0
        if winner[0] == 103:
            assert True

        return False, undecided, high_index, winner[0], price

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
        price = chains_sorted[1]["total"]

        # build commands for flights in the winner
        commands = []
        for _id, bid in zip(winner["chain"], winner["price"]):
            if winner["total"] == 0:
                cost = 0
            else:
                cost = float(bid / winner["total"]) * price     # proportional payment
            commands.append((_id, cost))

        return win_index, win_id, price, commands

    
    def secondback_helper(self, requests, locations, commands, cycle_ids, req_loc, temp_chain=[]):
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

        # if you loop on yourself, return 0 at this level
        if req_loc in temp_chain:
            chains.append({'chain': [], 'price': [], 'total': 0})
            return chains


        # recursion call - add every _id requesting to you to the list of chains given by location[_id]
        temp_tracking = {}      # temporary chain tracking of {loc: chains}, so that we don't redo recursion if a loc shows up again
        temp_chain.append(req_loc)
        for _id, price in requests[req_loc]:

            # check not in cycles and already moved
            # check if _id is already at this location - then it's a delayed flight
            # check if _id has a command - then it's been decided previously
            if _id in cycle_ids or locations[_id] == req_loc or commands[_id][1] > -1: 
                continue
            

            # get the next location
            prev_loc = locations[_id]

            # if we have no record of the location being recursed
            if prev_loc not in temp_tracking:
                if prev_loc == -1:
                    temp_tracking[prev_loc] = [{'chain': [], 'price': [], 'total': 0}]
                else:
                    temp_tracking[prev_loc] = self.secondback_helper(requests, locations, commands, cycle_ids, prev_loc, temp_chain)
            
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

        temp_chain.pop()
        # base case - if there's no chain, everyone requesting is cycled
        if len(chains) == 0:
            chains.append({'chain': [], 'price': [], 'total': 0})

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

        # base case - if you're not in requests (but not cycled, checked in layer above), return 0
        if req_loc not in requests:
            backpressures[req_loc] = 0
            return 0

        # if you loop on yourself, return 0 at this level
        if req_loc in backpressures:
            return 0

        pressures = [0]     # default pressure 0
        for _id, price in requests[req_loc]:        

            cur_loc = locations[_id]        # find location of the _id     
            if cur_loc == -1: continue      # if the next location is ground skip recursion

            if _id in cycle_ids: continue       # check if _id is in a cycle - skip if so
            if cur_loc in backpressures and backpressures[cur_loc] != None:        # check if this _id's has a backpressure associated
                pressures.append(backpressures[cur_loc])
                continue
            
            backpressures[req_loc] = None
            # jump to that location - recursion
            pressures.append(self.track_backpressure(requests, locations, cycle_ids, backpressures, cur_loc))
        
        # output, store to backpressures
        output = max(pressures) + 1
        backpressures[req_loc] = output
        return output