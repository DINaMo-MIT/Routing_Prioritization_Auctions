from helpers import *
from agents import *
from grid import *

def create_random(num_agents = 1, radius = 1, iters = 10, seed = None):
    """
    Creates a grid, list of agents, and the schedule in which they deploy
    Inputs:
        radius: size of grid
        iters: iterations planned
        seed: seed for random number generator
    Outputs: (grid, agents, schedule)
        grid: the map we're operating on
        agents: list of all agents that will join the system during the sim
        schedule: time at which agents depart and join system
    """
    rand = np.random.default_rng(seed)
    grid = Grid(radius)

    # Agents get random OD and random departure time (arrival time judged by steps to there)
    # create radius # of agents, store schedule of when agents go to active list
    agents = []
    schedule = {}
    for _ in range(num_agents):
        
        
        OD = rand.integers(0, len(grid.coords_l), size=2)
        init_time = rand.integers(0, iters - radius)
        var_cost = rand.integers(1, 10)
        
#         print(grid.coords_l[OD[0]], grid.coords_l[OD[1]], init_time)
        ag = Agent(grid.coords_l[OD[0]], grid.coords_l[OD[1]], var_cost, init_time)
        agents.append(ag)
        
        if init_time in schedule.keys(): schedule[init_time].append(ag)
        else: schedule[init_time] = [ag]
        
        # store and release from active_agents list
        # have grid process and understand bids - will need wait times and queuing data stored w/ agents
    
    return grid, agents, schedule

    

def create_binomial(num_agents = 62, radius = 1, time = 50, seed = None):
    """
    
    """
    rand = np.random.default_rng(seed)
    grid = Grid(radius)
    var_cost = 2
    
    weights_loc = rand.random(len(grid.coords_l))
    weights_loc = weights_loc / np.sum(weights_loc)
    
    x = np.linspace(0, time)
    weights_t = norm.pdf(x, 40, 5) + norm.pdf(x, 20, 8)
    weights_t = weights_t / np.sum(weights_t)
    
    agents = []
    schedule = {}
    for _ in range(num_agents):
        
        OD = rand.choice(len(grid.coords_l), size = 2, replace = False, p = weights_loc)
        init_time = rand.choice(time, p = weights_t)
        var_cost = rand.integers(1, 10)
        
#         print(grid.coords_l[OD[0]], grid.coords_l[OD[1]], init_time)
        ag = Agent(grid.coords_l[OD[0]], grid.coords_l[OD[1]], var_cost, init_time)
        agents.append(ag)
        
        if init_time in schedule.keys(): schedule[init_time].append(ag)
        else: schedule[init_time] = [ag]
        
        # store and release from active_agents list
        # have grid process and understand bids - will need wait times and queuing data stored w/ agents
    
    return grid, agents, schedule

# create_binomial(radius = 6)

def create_connected(radius = 1, iters = 10, seed = None):
    """
    Creates a grid, list of agents, and the schedule in which they deploy
    This setup is two lines of agents all trying to go to (0,0,0)
    Inputs:
        radius: int, size of grid
        iters: int, iterations planned
        seed: int, seed for random number generator
    Outputs: (grid, agents, schedule)
        grid: Grid, the map we're operating on
        agents: list of Agents, all agents that will join the system during the sim
        schedule: dictionary of {time: [Agents]} times at which agents depart and join system
    """
    assert radius >= 3
    
    rand = np.random.default_rng(seed)
    
    grid = Grid(radius)

    # Agents get random OD and random departure time (arrival time judged by steps to there)
    # create radius # of agents, store schedule of when agents go to active list
    agents = []
    schedule = {}
    for i in range(1, radius):
        
        init_time = 0
        var_cost = 2
        ag = Agent(Hex(i, -i, 0), Hex(0, 0, 0), var_cost, init_time)
        agents.append(ag)
        
        if init_time in schedule.keys(): schedule[init_time].append(ag)
        else: schedule[init_time] = [ag]
    
    # opposing line of agents
    for i in range(1, radius-1):
        
        init_time = 0
        var_cost = 2
        ag = Agent(Hex(i, 0, -i), Hex(0, 0, 0), var_cost, init_time)
        agents.append(ag)
        
        if init_time in schedule.keys(): schedule[init_time].append(ag)
        else: schedule[init_time] = [ag]
        
#         # store and release from active_agents list
#         # have grid process and understand bids - will need wait times and queuing data stored w/ agents
    
    return grid, agents, schedule

# create_connected(4)