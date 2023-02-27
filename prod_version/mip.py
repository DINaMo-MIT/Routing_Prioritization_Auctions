# %%
"""
Packages
"""
try:
    from pyomo.environ import *
except:
    print('Need to install pyomo')
from pyomo.environ import *
from pyomo.dae import *

import random
import pickle

# %%
from helpers import *   
from agents import *
from grid import *
from envs import *
from simulate import *

# %%


# # agents = []
# # for i in range(2):
# #     agents.append(Agent(Hex(0, 0, 0), Hex(0, -1, 1), 1, 0))
# # grid, agents, schedule = create_custom(agents, radius = 2)

# for i, ag in enumerate(agents):
#     ag._id = i

def optimal_solver(agents, Tf = 20, weights=False):
    Tf = Tf

    # Create variables w for all flights, times, sectors 
    # variables have Agent, Sector (only on path), Time (only after takeoff), Layer (0, 1, 2)
    # for each flight iterate
    vars = []
    departures = {}     # hex : _id  where hex is the takeoff and _id is agent
    travel = {}         # hex: [(_id, next, time, layer)] where next is next hex and time is the first time it's active and layer is the next step layer we care about

    # Variable definition
    # define only for sectors agent will travel in, including start and end
    # define for all times after agent departure
    for ag in agents:
        if ag._id == 3:
            pass
        indices = []

        for i, h in enumerate(ag._steps):

            # create entries in travel
            if h not in travel:
                travel[h] = []
            if i + 1 >= len(ag._steps):
                travel[h].append((ag._id, ag._steps[-1], ag._depart_t, 2))     ## CHANGE ag._depart_t to have logic when # var defs are shrunk
            else:
                travel[h].append((ag._id, ag._steps[i+1], ag._depart_t, 1))


            # create the variables  
            # ## NOTE when # var defs shrunk, must define variable one time-step before it actually can be filled, so that capacity constraints make sense
            for t in range(ag._depart_t, Tf+1):
                indices.append((ag._id, h, t, 1))

        for t in range(ag._depart_t, Tf+1): 
            # start and end layers
            indices.append((ag._id, ag._steps[0], t, 0))
            indices.append((ag._id, ag._steps[-1], t, 2))

        vars += indices   

    ### Create model
    m = ConcreteModel()
    m.vars = Set(initialize = vars)
    m.w = Var(m.vars, domain=Binary)    # indexing is (_id, q, r, s, time, layer)

    # debugging w
    # [var for var in list(m.w._data.keys()) if var[0] == 3]

    ## set boundary conditions - initialization, ending, and everything layer 1 and 2 at time 0 is 0
    m.boundary = ConstraintList()
    for ag in agents:
        # initialization - enters layer 0
        m.boundary.add(m.w[ag._id, ag._steps[0], ag._depart_t, 0] == 1)

        # ending - has to be in layer 2 by the end
        m.boundary.add(m.w[ag._id, ag._steps[-1], Tf, 2] == 1)

        # initial empty - all the 1's are not filled when the agent departs
        # the first 1 that exist basically
        for s in ag._steps:
            m.boundary.add(m.w[ag._id, s, ag._depart_t, 1] == 0)
        
        # initial empty - 2's are not filled when the agent departs
        m.boundary.add(m.w[ag._id, ag._steps[-1], ag._depart_t, 2] == 0)
        


    # capacity (4)  ## SKIPPING FOR ONE AGENT 
    m.capacity = ConstraintList()
    # movement constraints - for a hex, go through all times - at each time go through all agents, figure out who maters, and put them into constraint
    for cur, data in travel.items():
        for t in range(Tf+1):
            sum = None
            for agid, next, time, layer in data:
                if t < time: continue       # the variable doesn't exist yet and isn't defined for current t

                sum += m.w[agid, cur, t, 1] - m.w[agid, next, t, layer]

            if sum is not None:     # if something has been added to the sum
                m.capacity.add(sum <= 1)

    # takeoff constraints - a form of capacity essentially

    # continuity (5) - for every step in agent, step after must be taken after step is taken and time has passed
    m.cont = ConstraintList()
    for ag in agents:
        for i in range(len(ag._steps) - 1):
            cur_step = ag._steps[i]
            next_step = ag._steps[i+1]

            # iterate through all times except time 0 - set time 0 to == 0 b/c physically impossible but can't tie to a previous step
            for t in range(ag._depart_t, Tf):     # not Tf+1 b/c of t+1 below
                m.cont.add(m.w[ag._id, next_step, t+1, 1] - m.w[ag._id, cur_step, t, 1] <= 0)

        # do the 0 and 2 layers, for all times
        for t in range(ag._depart_t, Tf):
            # can't be in 1 until you're in origin 0
            m.cont.add(m.w[ag._id, ag._steps[0], t+1, 1] - m.w[ag._id, ag._steps[0], t, 0] <= 0)

            # can't be in 2 until you're in destination 1
            m.cont.add(m.w[ag._id, ag._steps[-1], t+1, 2] - m.w[ag._id, ag._steps[-1], t, 1] <= 0)


    # time constraints (7) - for every time of every sector of every flight
    # if t is 1, then t' >= t must be 1
    m.time = ConstraintList()
    for ag in agents:
        for s in ag._steps:
            for t in range(ag._depart_t, Tf):  # not Tf+1 b/c of t+1 below
                    m.time.add(m.w[ag._id, s, t+1, 1] - m.w[ag._id, s, t, 1] >= 0)

        # handle 0 and 2 layer
        for t in range(ag._depart_t, Tf):
            m.time.add(m.w[ag._id, ag._steps[0], t+1, 0] - m.w[ag._id, ag._steps[0], t, 0] >= 0)
            m.time.add(m.w[ag._id, ag._steps[-1], t+1, 2] - m.w[ag._id, ag._steps[-1], t, 2] >= 0)

    # objective
    def objective(m):
        sum = 0
        for ag in agents:
            end = ag._steps[-1]

            for t in range(ag._depart_t, Tf):
                if weights:
                    sum += t * ag._var_cost * (m.w[ag._id, end, t+1, 2] - m.w[ag._id,end, t, 2])
                else:
                    sum += t * (m.w[ag._id, end, t+1, 2] - m.w[ag._id,end, t, 2])
            
            if weights:
                sum -= ag._schedule_t  * ag._var_cost
            else:
                sum -= ag._schedule_t 
        
        return sum

    m.obj = Objective(rule=objective, sense=minimize)

    #solve
    SolverFactory('gurobi').solve(m, tee=True)
    # m.w.pprint()


    return value(m.obj), m.w, m

# %%

# %%
"""
Testing
"""

delay_dict = {}
stdev_delay_dict = {}

# parameters
priority = 'backpressure'
samples = 100
Tf = 70

for run in [1,2,3,4]:
    print('starting run:', run)

    # Initialize dicts
    delay_dict[run] = {'protocol': {'unweighted': [], 'weighted': []}, 
                'optimize': {'unweighted': [], 'weighted': []}}
    stdev_delay_dict[run] = {'protocol': {'unweighted': [], 'weighted': []}, 
                        'optimize': {'unweighted': [], 'weighted': []}}

    # loop through samples
    for s in range(samples):

        # Create agents
        if run == 1: grid, agents, schedule = create_random(num_agents=124, radius=7, iters=50, operator_flag=True, seed = s+100)
        elif run == 2: grid, agents, schedule = create_bimodal(num_agents=126, radius=7, time=50, operator_flag = True, seed = s+1000)
        # grid, agents, schedule = create_crossing(num_agents = [40,60], radius = 7, time = 50, points = 4, seed=i+1000)
        elif run == 3: grid, agents, schedule = create_crossing(num_agents = [15, 20, 15], radius = 7, time = 50, points = 4, seed= s+1000)
        elif run == 4: grid, agents, schedule = create_hubspoke(num_agents = [15, 15, 15, 15, 15, 15], radius = 7, seed = s+100)


        # protocol
        rev, delay, std_delay, conflicts, pay_costs, wait_costs, std_delay_weighted, \
                        pay_costs_norm, wait_costs_norm, operator_count, operator_delay, operator_delay_waits = simulate(grid, agents, schedule, vis=False, prior=priority, output=False, debug=False)
        print(delay)

        # save to dicts
        delay_dict[run]['protocol']['unweighted'].append(delay)
        delay_dict[run]['protocol']['weighted'].append(wait_costs)
        stdev_delay_dict[run]['protocol']['unweighted'].append(std_delay)
        stdev_delay_dict[run]['protocol']['weighted'].append(std_delay_weighted)

        # optimization
        for j, ag in enumerate(agents):
            ag._id = j
        optimal_delay, w, model = optimal_solver(agents, Tf=Tf)
        w_dict = w.extract_values()
        # print('Optimal Delay:', optimal_delay)

        # calculate metrics
        delays = []
        weighted_delays = []
        for i, ag in enumerate(agents):
            id = ag._id
            dest = ag._steps[-1]
            sch_arr = ag._schedule_t
            for t in range(sch_arr, Tf+1):
                # find arrival times
                if w_dict[id,dest.q,dest.r,dest.s,t,1] > 0.99:
                    flt_delay = t - sch_arr
                    delays.append(flt_delay)
                    flt_weighted_delay = flt_delay * ag._var_cost
                    weighted_delays.append(flt_weighted_delay)
                    break

        # save to dicts
        delay_dict[run]['optimize']['unweighted'].append(np.sum(delays))
        delay_dict[run]['optimize']['weighted'].append(np.sum(weighted_delays))
        stdev_delay_dict[run]['optimize']['unweighted'].append(np.std(delays))
        stdev_delay_dict[run]['optimize']['weighted'].append(np.std(weighted_delays))        


# %%
# save to pickle
with open('delay.pickle', 'wb') as handle:
    pickle.dump(delay_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

with open('stdev_delay.pickle', 'wb') as handle2:
    pickle.dump(stdev_delay_dict, handle2, protocol=pickle.HIGHEST_PROTOCOL)


# %%
"""
Record delay and weighted delay for each agent
inputs: 
- agents: list of agent objects
- w_dict: w decision variables
"""
delay_dict
# stdev_delay_dict
# delays

        

    
# %%
# %%
# load pickle
with open('delay.pickle', 'rb') as handle:
    delay_dict = pickle.load(handle)

# %%
with open('stdev_delay.pickle', 'rb') as handle:
    std_delay_dict = pickle.load(handle)


# %%
delay_dict
# %%
for run in [1,2,3,4]:
    
    print('run', run)

    # delay
    delay = (np.mean(delay_dict[run]['optimize']['unweighted']) - 
             np.mean(delay_dict[run]['protocol']['unweighted'])) / np.mean(delay_dict[run]['optimize']['unweighted'])
    print('delay:', np.round(delay*100,1),'%')

    # std delay
    std_delay = (np.mean(std_delay_dict[run]['optimize']['unweighted']) - 
             np.mean(std_delay_dict[run]['protocol']['unweighted'])) / np.mean(std_delay_dict[run]['optimize']['unweighted'])
    print('stdev delay:', np.round(std_delay*100,1),'%')


    # weighted delay
    weighted_delay = (np.mean(delay_dict[run]['optimize']['weighted']) - 
             np.mean(delay_dict[run]['protocol']['weighted'])) / np.mean(delay_dict[run]['optimize']['weighted'])
    print('weighted delay:', np.round(weighted_delay*100,1),'%')


    # stdev weighted delay
    std_weighted_delay = (np.mean(std_delay_dict[run]['optimize']['weighted']) - 
             np.mean(std_delay_dict[run]['protocol']['weighted'])) / np.mean(std_delay_dict[run]['optimize']['weighted'])
    print('stdev weighted delay:', np.round(std_weighted_delay*100,1),'%')
# %%
