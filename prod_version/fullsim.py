from helpers import *   ## Constants
from agents import *
from grid import *
from envs import *
from simulate import *

## Try multiple runs of different tests
def full_sim(run = 1):
    methods = ["random", "roundrobin", "backpressure", "secondprice", "secondback"]

    data_avg_rev = []
    data_avg_del = []
    data_avg_std = []
    data_avg_confl = []

    data_avg_wait = []  # weighted delay
    data_avg_pay = []   # how much paid

    data_avg_std_weighted = []

    data_avg_wait_norm = []
    data_avg_pay_norm = []

    data_avg_operator_diff_raw = []
    data_avg_operator_diff_wait = []

    data_std_operator_diff_raw = []
    data_std_operator_diff_wait = []

    # generate test cases
    samples = 100 
    cases = []
    operator_flag = True
    for i in range(samples):
        if run == 1: grid, agents, schedule = create_random(num_agents=124*2, radius=4, iters=50, operator_flag=True, seed = i + 100)
        elif run == 2: grid, agents, schedule = create_bimodal(num_agents=126, radius=7, time=50, operator_flag = operator_flag, seed = i + 1000)
        # grid, agents, schedule = create_crossing(num_agents = [40,60], radius = 7, time = 50, points = 4, seed=i+1000)
        elif run == 3: grid, agents, schedule = create_crossing(num_agents = [30, 40, 30], radius = 7, time = 50, points = 4, seed=i + 1000)
        elif run == 4: grid, agents, schedule = create_hubspoke(num_agents = [25, 25, 25, 25, 25, 25], radius = 7, seed = i + 100)
        cases.append((grid, agents, schedule))


    # run through priority
    for priority in methods:
        avg_rev = 0
        avg_del = 0
        avg_std_del = 0
        avg_num_conflicts = 0

        avg_pay_costs = 0
        avg_wait_costs = 0

        avg_std_del_weighted = 0

        avg_pay_costs_norm = 0
        avg_wait_costs_norm = 0

        avg_operator_diff_raw = 0
        avg_operator_diff_wait = 0

        std_operator_diff_raw = []
        std_operator_diff_wait = []

        # if priority == "secondprice" or priority == "secondback":
        #     avg__pay_costs = 0


        for i in range(len(cases)):
            # seed = np.random.randint(1000)
            # print(seed)
            # print(i)
            # print(grid, agents, schedule)
            
            grid, agents, schedule = deepcopy(cases[i])

            rev, delay, std_delay, conflicts, pay_costs, wait_costs, std_delay_weighted, pay_costs_norm, wait_costs_norm, operator_count, operator_delay, operator_delay_waits = simulate(grid, agents, schedule, vis= False, prior=priority)
            avg_rev += rev
            avg_del += delay
            avg_std_del += std_delay
            avg_num_conflicts += conflicts

            avg_pay_costs += pay_costs
            avg_wait_costs += wait_costs

            avg_std_del_weighted += std_delay_weighted

            avg_pay_costs_norm += pay_costs_norm
            avg_wait_costs_norm += wait_costs_norm


            if operator_flag:

                temp_delay = [delay / number for (delay, number) in zip(list(operator_delay.values()), list(operator_count.values()))]
                avg_operator_diff_raw += np.sum(np.std(temp_delay))
                # std_operator_diff_raw.append(np.sum(np.std(list(operator_delay.values()))))
                
                temp_wait = [pay / number for ([_, pay, total], number) in zip(list(operator_delay_waits.values()), list(operator_count.values()))]

                # print(np.std(temp_wait))
                # print('vs', np.sum(np.std(temp_wait)))
                avg_operator_diff_wait += np.sum(np.std(temp_wait))
                # std_operator_diff_wait.append(np.sum(np.std(temp_wait)))

                # avg_operator_diff_raw += abs(operator_delay[1] / operator_count[1] - operator_delay[2] / operator_count[2])
                # avg_operator_diff_wait += abs(operator_delay_waits[1][1] / operator_delay_waits[1][2] - operator_delay_waits[2][1] / operator_delay_waits[2][2])

        
        print("Priority: ", priority)
        print("Avg Revenue: ", avg_rev / samples)
        print("Avg Delay: ", avg_del / samples)
        print("Avg Std Dev Delay (among agents): ", avg_std_del / samples)
        print("Avg Num Conflicts: ", avg_num_conflicts / samples)

        print("Avg payment costs: ", avg_pay_costs / samples)
        print("Avg waiting costs: ", avg_wait_costs / samples)

        print("Avg Weighted Std Dev Delay (among agents): ", avg_std_del_weighted / samples)
        
        print("Avg Normalized payment costs: ", avg_pay_costs_norm / samples)
        print("Avg Normalized waiting costs: ", avg_wait_costs_norm / samples)

        data_avg_rev.append(avg_rev / samples)
        data_avg_del.append(avg_del / samples)
        data_avg_std.append(avg_std_del / samples)
        data_avg_confl.append(avg_num_conflicts / samples)

        data_avg_pay.append(avg_pay_costs / samples)
        data_avg_wait.append(avg_wait_costs / samples)

        data_avg_std_weighted.append(avg_std_del_weighted  / samples)

        data_avg_pay_norm.append(avg_pay_costs_norm / samples)
        data_avg_wait_norm.append(avg_wait_costs_norm / samples)


        if operator_flag:
            print("Avg difference in operator delays: ", avg_operator_diff_raw / samples)
            print("Avg difference in operator waits: ", avg_operator_diff_wait / samples)
            data_avg_operator_diff_raw.append(avg_operator_diff_raw / samples)
            data_avg_operator_diff_wait.append(avg_operator_diff_wait / samples)

            data_std_operator_diff_raw.append(np.std(std_operator_diff_raw))
            data_std_operator_diff_wait.append(np.std(std_operator_diff_wait))

    output = {}

    output['data_avg_rev'] = data_avg_rev
    output['data_avg_del'] = data_avg_del
    output['data_avg_std'] = data_avg_std
    output['data_avg_confl'] = data_avg_confl

    output['data_avg_wait'] = data_avg_wait
    output['data_avg_pay'] = data_avg_pay

    output['data_avg_std_weighted'] = data_avg_std_weighted

    output['data_avg_wait_norm'] = data_avg_wait_norm
    output['data_avg_pay_norm'] = data_avg_pay_norm

    output['data_avg_operator_diff_raw'] = data_avg_operator_diff_raw
    output['data_avg_operator_diff_wait'] = data_avg_operator_diff_wait

    output['data_std_operator_diff_raw'] = data_std_operator_diff_raw
    output['data_std_operator_diff_wait'] = data_std_operator_diff_wait
    
    grid, agents, schedule = deepcopy(cases[23])
    output['example'] = (grid, agents, schedule)

    return output

    
if __name__ == "__main__":
    for i in range(1, 5):
        output = full_sim(run = i)