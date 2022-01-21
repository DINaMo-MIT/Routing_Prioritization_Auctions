from helpers import *

class Agent():
    
    def __init__(self, origin, dest, var_cost, depart_t = 0):
        
        """
        Initialize an Agent navigating the environment
        
        Input:
            origin: Hex, initial location
            dest: Hex, destination location
            var_cost: double, variable cost of operation
            depart_t: integer, time of departure
        Returns:
        
        """

        self._loc = -1   # -1 means grounded trying to enter air, 0 means arrived and down
        self._var_cost = var_cost

        # requested locations, payment costs and waiting costs
        self._steps = hex_linedraw(origin, dest)
        self._index = 0
        self._pay_costs = 0
        self._wait_costs = 0
        
        self._origin = origin
        self._dest = dest
        
        # departure and arrival times
        self._depart_t = depart_t
        self._schedule_t = depart_t + len(self._steps)
        self._arrival_t = None
        
        self._id = uuid.uuid4()
        
    @property
    def bid(self):
        """
        Send out bid of (loc, price, id)
        Returns:
            out: tuple of (loc, price, id)
        """
        if self._index >= len(self._steps): # if you're done
            # self._loc = 0  # return no bid, and set arrival flag
            return (None, -1, self._id)  
        
        # check that requested location is right next to current
        assert self._loc == -1 or hex_distance(self._steps[self._index], self._loc) == 1
        
        return (self._steps[self._index], self._var_cost, self._id)
    
    @property
    def loc(self):
        """
        Return current location
        Returns:
            out: Hex of location
        """
        return self._loc
    
    @property
    def dest(self):
        """
        Return destination
        Returns:
            out: Hex of location
        """
        return self._dest
    
    @property
    def finished(self):
        """
        Returns if agent has reached the destination
        Returns:
            out: bool
        """
        return self._loc == self._dest
    
    @property
    def costs(self):
        """
        Return costs incurred by agent so far
        This is essentially the extra costs incurred on top of costs from operatin w/o anyone else
        Returns:
            out: tuple of (pay_costs, wait_costs)
        """
        return (self._pay_costs, self._wait_costs)
    
    def move(self, command):
        """
        Move the bot
        Inputs:
            command: tuple of (next_loc, bid)
        Outputs:
            out: boolean to indicate at goal already
        """
        if self._index >= len(self._steps): return True  # if you're at the goal already
        
        next_loc, bid = command
        # if command is None, not cleared to move and you eat the variable cost
        if next_loc == None:
            self._wait_costs += self._var_cost
            return False
        
        # else move
        assert next_loc == self._steps[self._index]
        self._index += 1
        # del self._steps[0]
        self._loc = next_loc
        
        # pay the bid price
        self._pay_costs += bid
        return False