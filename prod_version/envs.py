from helpers import *
from agents import *
from grid import *
from grid_cap import *

def create_random(num_agents = 1, radius = 1, iters = 10, seed = None, operator_flag = False):
    """
    Creates a grid, list of agents, and the schedule in which they deploy - all uniform random
    Inputs:
        radius: size of grid
        iters: iterations planned
        seed: seed for random number generator
        operatro_flag: generate 3 opearators
    Outputs: (grid, agents, schedule)
        grid: the map we're operating on
        agents: list of all agents that will join the system during the sim
        schedule: time at which agents depart and join system
    """
    rand = np.random.default_rng(seed)
    grid = GridCapacity(radius)

    # Agents get random OD and random departure time (arrival time judged by steps to there)
    # create radius # of agents, store schedule of when agents go to active list
    agents = []
    schedule = {}
    for _ in range(num_agents):
        
        
        OD = rand.integers(0, len(grid.coords_l), size=2)
        init_time = rand.integers(0, iters - radius)
        var_cost = rand.integers(1, 10)
        
#         print(grid.coords_l[OD[0]], grid.coords_l[OD[1]], init_time)
        operator = None
        if operator_flag:
            operator = rand.integers(1, 4)


        ag = Agent(grid.coords_l[OD[0]], grid.coords_l[OD[1]], var_cost, depart_t = init_time, operator = operator)
        agents.append(ag)
        
        if init_time in schedule.keys(): schedule[init_time].append(ag)
        else: schedule[init_time] = [ag]
        
        # store and release from active_agents list
        # have grid process and understand bids - will need wait times and queuing data stored w/ agents
    
    return grid, agents, schedule


    
def create_bimodal(num_agents = 62, radius = 1, time = 50, seed = None, operator_flag=False):
    """
        Creates a grid, list of agents, and the schedule in which they deploy - bimodal distribution schedule only
    Inputs:
        radius: size of grid
        iters: iterations planned
        seed: seed for random number generator
        operatro_flag: generate 3 opearators
    Outputs: (grid, agents, schedule)
        grid: the map we're operating on
        agents: list of all agents that will join the system during the sim
        schedule: time at which agents depart and join system
    """
    rand = np.random.default_rng(seed)
    grid = GridCapacity(radius)
    
    weights_loc = rand.random(len(grid.coords_l))
    weights_loc = weights_loc / np.sum(weights_loc)
    
    x = np.linspace(0, time)
    weights_t = norm.pdf(x, 40, 5) + norm.pdf(x, 20, 8)     # Bimodal time dsitribution
    weights_t = weights_t / np.sum(weights_t)
    
    agents = []
    schedule = {}
    for i in range(num_agents):
        
        OD = rand.choice(len(grid.coords_l), size = 2, replace = False, p = weights_loc)
        init_time = rand.choice(time, p = weights_t)
        var_cost = rand.integers(1, 10)

        operator = None
        if operator_flag:
            operator = i % 3 + 1

#         print(grid.coords_l[OD[0]], grid.coords_l[OD[1]], init_time)
        ag = Agent(grid.coords_l[OD[0]], grid.coords_l[OD[1]], var_cost, init_time, operator=operator)
        agents.append(ag)
        
        if init_time in schedule.keys(): schedule[init_time].append(ag)
        else: schedule[init_time] = [ag]
        
        # store and release from active_agents list
        # have grid process and understand bids - will need wait times and queuing data stored w/ agents
    
    return grid, agents, schedule

# create_bimodal(radius=6)

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
    
    grid = GridCapacity(radius)

    # Agents get random OD and random departure time (arrival time judged by steps to there)
    # create radius # of agents, store schedule of when agents go to active list
    agents = []
    schedule = {}
    
    for i in range(1, radius-1):
        
        init_time = 0
        var_cost = i
        ag = Agent(Hex(i, -i, 0), Hex(0, 0, 0), var_cost, init_time)
        agents.append(ag)
        
        if init_time in schedule.keys(): schedule[init_time].append(ag)
        else: schedule[init_time] = [ag]
    
    for i in range(1, radius-1):
        
        init_time = 0
        var_cost = i + 1
        ag = Agent(Hex(i, -i, 0), Hex(0, 0, 0), var_cost, init_time)
        agents.append(ag)
        
        if init_time in schedule.keys(): schedule[init_time].append(ag)
        else: schedule[init_time] = [ag]
    

    # opposing line of agents
    for i in range(1, radius-1):
        
        init_time = 0
        var_cost = i + 3
        ag = Agent(Hex(i, 0, -i), Hex(0, 0, 0), var_cost, init_time)
        agents.append(ag)
        
        if init_time in schedule.keys(): schedule[init_time].append(ag)
        else: schedule[init_time] = [ag]
        
    
    return grid, agents, schedule

# create_connected(4)

def create_cycle_testing_cap(radius = 3, iters = 10, seed=None):
    
    """ASSUMES CAPACITY OF 2 TO TEST CYCLING"""

    rand = np.random.default_rng(seed)
    grid = GridCapacity(radius)

    agents = []
    schedule = {}

    agents = [
        Agent(Hex(1, 0, -1), Hex(0, 0, 0), 1, 0),     
        Agent(Hex(0, 0, 0), Hex(0, 1, -1), 1, 0), 
        Agent(Hex(0, 1, -1), Hex(1, 0, -1), 1, 0),
 

        # Agent(Hex(1, 0, -1), Hex(0, 0, 0), 1, 0),     
        # Agent(Hex(0, 0, 0), Hex(0, 1, -1), 1, 0), 
        # Agent(Hex(0, 1, -1), Hex(1, 0, -1), 1, 0),

        # comment out bottom for 1 cycle only, capacity 1
        # Agent(Hex(1, 0, -1), Hex(1, 1, -2), 1, 0), 
        # Agent(Hex(1, 1, -2), Hex(0, 1, -1), 1, 0),
        # Agent(Hex(0, 1, -1), Hex(1, 0, -1), 1, 0),

    ]
    schedule[0] = agents

    return grid, agents, schedule


def create_backpressure_test(radius = 3, iters = 10, seed=None):
    
    """ASSUMES CAPACITY OF 2 TO TEST CYCLING"""

    rand = np.random.default_rng(seed)
    grid = GridCapacity(radius)

    agents = []
    schedule = {}

    agents = [
        Agent(Hex(1, 0, -1), Hex(0, 0, 0), 1, 0),     
        Agent(Hex(0, 0, 0), Hex(1, 0, -1), 1, 0), 
        Agent(Hex(0, 1, -1), Hex(1, 0, -1), 1, 0),

        Agent(Hex(-1, 0, 1), Hex(0, 0, 0), 1, 0),    
        Agent(Hex(-2, 0, 2), Hex(-1, 0, 1),  1, 0),
        Agent(Hex(-2, 0, 2), Hex(-1, 0, 1),  1, 0),
        Agent(Hex(-3, 0, 3), Hex(-1, 0, 1),  1, 0),


        # Agent(Hex(0, 2, -2), Hex(0, 1, -1),  1, 0),

        # Agent(Hex(1, 0, -1), Hex(0, 0, 0), 1, 0),     
        # Agent(Hex(0, 0, 0), Hex(0, 1, -1), 1, 0), 
        # Agent(Hex(0, 1, -1), Hex(1, 0, -1), 1, 0),

        # comment out bottom for 1 cycle only, capacity 1
        # Agent(Hex(1, 0, -1), Hex(1, 1, -2), 1, 0), 
        # Agent(Hex(1, 1, -2), Hex(0, 1, -1), 1, 0),
        # Agent(Hex(0, 1, -1), Hex(1, 0, -1), 1, 0),

    ]
    schedule[0] = agents

    return grid, agents, schedule


def create_hubspoke(num_agents = [50, 50, 50], radius = 7, seed = None):
    """
    Create a hub and spoke scenario, with 6 operators each owning two positions
    Poisson distribution of launch? - mean 2
    """
    # set up grid
    rand = np.random.default_rng(seed)
    grid = GridCapacity(radius)

    # hubs1 = [Hex(radius, -radius, 0), Hex(radius, 0, -radius)]
    # hubs2 = [Hex(0, radius, -radius), Hex(-radius, radius, 0)]
    # hubs3 = [Hex(-radius, 0, radius), Hex(0, -radius, radius)]

    # hubs = [hubs1, hubs2, hubs3]
    
    hubs = [Hex(radius, -radius, 0), Hex(radius, 0, -radius), Hex(0, radius, -radius), Hex(-radius, radius, 0), Hex(-radius, 0, radius), Hex(0, -radius, radius)]

    agents = []
    schedule = {}
    for i, num in enumerate(num_agents):

        t = 0
        origins = hubs[i]
        for _ in range(num):

            # org = rand.choice(len(origins))
            org = 0
            dest = rand.choice(len(grid.coords_l))

            t += poisson.rvs(mu=2)

            init_time = t
            var_cost = rand.integers(1, 10)
            operator = i+1

            # assert locs[0][origin] in grid.coords and locs[1][departure] in grid.coords
    #         print(grid.coords_l[OD[0]], grid.coords_l[OD[1]], init_time)
            ag = Agent(origins, grid.coords_l[dest], var_cost, init_time, operator=operator)
            agents.append(ag)
            
            if init_time in schedule.keys(): schedule[init_time].append(ag)
            else: schedule[init_time] = [ag]

    return grid, agents, schedule


def create_crossing(num_agents = [50, 50, 50], radius = 7, time = 50, points = 3, seed = None):
    """
    Create a crossing setup, where three operators are crossing over. Encode number of agents in size
    """
    # set up grid
    rand = np.random.default_rng(seed)
    grid = GridCapacity(radius)
    
    assert points <= radius

    # set up time of departure
    x = np.linspace(0, time)
    weights_t = norm.pdf(x, 40, 5) + norm.pdf(x, 20, 8)
    weights_t = weights_t / np.sum(weights_t)

    # set up all origin and destination points
    op1 = [[], []]
    op2 = [[], []]
    op3 = [[], []]
    for i in range(points):
        op1[0].append(Hex(-radius, radius - i, i))
        op1[1].append(Hex(radius, -radius + i, -i))

        # op2[0].append(Hex(i, radius-i, -radius))
        # op2[1].append(Hex(-i, -radius+i, radius))
        
        op2[0].append(Hex(-i, radius, -radius+i))
        op2[1].append(Hex(i, -radius, radius-i))

        op3[0].append(Hex(radius-i, i, -radius))
        op3[1].append(Hex(-radius+i, -i, radius))

    ops = [op1, op2, op3]

    # iterate for the two operators
    agents = []
    schedule = {}
    for i, num in enumerate(num_agents):

        locs = ops[i]
        for _ in range(num):

            origin = rand.choice(len(locs[0]))
            departure = rand.choice(len(locs[1]))

            init_time = rand.choice(time, p = weights_t)
            var_cost = rand.integers(1, 10)


            operator = i+1

            assert locs[0][origin] in grid.coords and locs[1][departure] in grid.coords
    #         print(grid.coords_l[OD[0]], grid.coords_l[OD[1]], init_time)
            ag = Agent(locs[0][origin], locs[1][departure], var_cost, init_time, operator=operator)
            agents.append(ag)
            
            if init_time in schedule.keys(): schedule[init_time].append(ag)
            else: schedule[init_time] = [ag]

    return grid, agents, schedule

