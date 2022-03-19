from helpers import *
from scipy.stats import norm, poisson

def simulate(grid, agents, schedule, prior = None, iters = 1e4, seed = 0, vis = False, debug = False, output=False):
    """
    Simulation function to run everything
    Not dealing with cycles
    Inputs:
        grid: Grid
        agents: list of Agents
        schedule: dictionary of {time: [Agents]}, when each agent starts up
        *****
        priority: string, type of priority method grid uses, default None -> random
        iters: int of iterations, optional
        seed: int for RNG, optional
        vis: bool for visualization, optional
        debug: bool for text debugging, optional
    Returns:
        revenue:
        delay:
        std delay:
        num_conflicts
        pay costs:
        wait costs:
        weighted std delay:
        normalized pay costs:
        normalized wait costs:
        operator counts:
        operator raw delay:
        operator weighted delay:
    """
    
    ## Initialization
    # Grid setup
    if prior is not None: grid.set_priority(prior)
    
    # Data collection setups
    delays = {}
    

    ## Running the simulation
    active = []    
    time = 0
    
    layout = Layout(layout_pointy, Point(1, 1), Point(0, 0))
    
    while time <= iters:

        if vis or debug: print("Time: ", time)
        
        # plotting and visualization

        if vis: plot_locations(layout, grid.coords_l, active, radius = grid.radius)
        
        # for debugging, print all agent locations
        if debug:
            for ag in agents: 
                print("Agent", ag._id, "location", ag.loc, "target", ag.dest, ag.finished)
        
        # update the active agents list
        for ag in active:
            if ag.finished:
                ag._arrival_t = time
        

        # check if all agents are in, which would indicate END ****
        if all([x.finished for x in agents]): break
        
            
        active = [ag for ag in active if not ag.finished]
        if time in schedule.keys(): active += schedule[time]
        
        # get bids and locations
        bids = {}
        locs = {}
        for ag in active:
            next_loc, price, _id = ag.bid
            bids[_id] = (next_loc, price)
            # bids.append(ag.bid)
            locs[_id] = ag.loc

            
        # Run the step simulation
        commands = grid.step_sim(locs, bids)
        if debug:
            print("Bids: ", bids)
            print("Commands: ", commands)
        
        # move agents around
        for i, command in enumerate(commands.values()):
            active[i].move(command)
            
        time += 1
    
    
    if output:
        print("Time: ", time)
        print("Priority: ", grid.priority)

    delays = []
    delays_weighted = []
    agent_waits = []
    agent_waits_norm = []

    # Operator questions
    operator_delay = {}
    operator_delay_waits = {}
    operator_counts = {}

    operate = False
    if agents[0].operator: operate = True
        # get costs and revenue
    for i, ag in enumerate(agents):
        if output: 
            print("Agent ", i, "operator ", ag.operator, " costed ", ag.costs, "finished", ag.finished, "departure, scheduled, arrived", ag._depart_t, ag._schedule_t, ag._arrival_t, "price", ag._var_cost)   # think of this as extra/delayed costs
            
        delays.append(ag._arrival_t - ag._schedule_t)
        delays_weighted.append((ag._arrival_t - ag._schedule_t) * ag._var_cost)
        agent_waits.append(np.array(ag.costs))
        agent_waits_norm.append(np.array(ag.costs) / ag._var_cost)

        if operate:
            if ag.operator not in operator_delay.keys():
                operator_delay[ag.operator] = 0
                operator_delay_waits[ag.operator] = np.zeros(3)
                operator_counts[ag.operator] = 0
            
            operator_delay[ag.operator] += ag._arrival_t - ag._schedule_t
            operator_delay_waits[ag.operator] += np.concatenate((ag.costs, [ag._var_cost]))
            operator_counts[ag.operator] += 1
        
    agent_waits = np.array(agent_waits)
    agent_waits_norm = np.array(agent_waits_norm)
    # print(agent_waits)
    if output:
        print("Total Revenue: ", grid.revenue)
        print("Total Conflicts: ", grid.num_conflicts)
        print("Total Delay: ", np.sum(delays))
        print("Std Dev Delay: ", np.std(delays))
        print("Total Pay Costs: ", np.sum(agent_waits[:, 0]))
        print("Total Wait Costs: ", np.sum(agent_waits[:, 1]))
        
        print("Std Dev Normalized Delay: ", np.std(delays_weighted))

        print("Total Normalized Pay Costs: ", np.sum(agent_waits_norm[:, 0]))
        print("Total Normalized Wait Costs: ", np.sum(agent_waits_norm[:, 1]))
    
        if operate:
            for op in operator_delay.keys():
                print("Operator ", op, "# agents ", operator_counts[op], "raw delay ", operator_delay[op], "weighted delay ", operator_delay_waits[op])

    return grid.revenue, np.sum(delays), np.std(delays), grid.num_conflicts, np.sum(agent_waits[:, 0]), np.sum(agent_waits[:, 1]), np.std(delays_weighted), np.sum(agent_waits_norm[:, 0]), np.sum(agent_waits_norm[:, 1]), operator_counts, operator_delay, operator_delay_waits