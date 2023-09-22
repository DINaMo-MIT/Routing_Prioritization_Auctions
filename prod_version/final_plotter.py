
from helpers import *   ## Constants
import matplotlib.pyplot as plt
import seaborn as sns

# from agents import *
# from grid import *
# from envs import *
# from simulate import *


def final_plotter2(output, axs, scenario = "NULL", title= True):

    data_avg_rev	=	output['data_avg_rev'] 
    data_avg_del	=	output['data_avg_del'] 
    data_avg_std	=	output['data_avg_std'] 
    data_avg_confl	=	output['data_avg_confl'] 

    data_avg_wait	=	output['data_avg_wait'] 
    data_avg_pay	=	output['data_avg_pay'] 

    data_avg_std_weighted	=	output['data_avg_std_weighted'] 

    data_avg_wait_norm	=	output['data_avg_wait_norm'] 
    data_avg_pay_norm	=	output['data_avg_pay_norm'] 

    data_avg_operator_diff_raw	=	output['data_avg_operator_diff_raw'] 
    data_avg_operator_diff_wait	=	output['data_avg_operator_diff_wait'] 

    data_std_operator_diff_raw	=	output['data_std_operator_diff_raw'] 
    data_std_operator_diff_wait	=	output['data_std_operator_diff_wait']

    (grid, active, schedule) = output['example'] 

    # section on example printing 

    layout = Layout(layout_pointy, Point(1, 1), Point(0, 0))
    locations = {}
    for ag in active:
        # print(ag._id, ag.loc)
        locations[ag.loc] = (ag._id, ag.finished, ag.bid[0], ag.bid[1])
    

    # fig, ax = plt.subplots(1, figsize=(radius * 2, radius * 2), dpi= 2*radius * 25,)

    # ax.set(xlim=(-7, 7), ylim=(-7,7))
    
    for h in grid.coords_l:

        x, y = hex_to_pixel(layout, h)
        hex = RegularPolygon((x,y), numVertices=6, radius= 1, 
                             orientation=np.radians(0), 
                             alpha=0.2, edgecolor='k')
        axs[0].add_patch(hex)
        

    for ag in active:
        x_s, y_s = hex_to_pixel(layout, ag._origin)
        x_d, y_d = hex_to_pixel(layout, ag._dest)


        color = 'k'
        if ag._operator and False:      ## turned off color for operators in example
            if ag._operator == 1: color = 'b'
            if ag._operator == 2: color = 'r'
            if ag._operator == 3: color = 'g'
            if ag._operator == 4: color = 'orange'
            if ag._operator == 5: color = 'yellow'
            if ag._operator == 6: color = 'purple'

        arrow = FancyArrow(x_s, y_s, x_d - x_s, y_d - y_s, 
                            color = color, 
                            head_width = 0.1, head_length = 0.1)
        axs[0].add_patch(arrow)

    axs[0].set_aspect('equal')
    axs[0].autoscale()

    # sns.set_theme()
    # sns.set(font_scale=1.5)
    icon_size = 500
    methods = ["random", "roundrobin", "backpressure", "accrueddelay", "reversals", "secondprice", "secondback"]
    # markers = ['.', 'x', 'o', '+', '*']
    # ',', '.', 'o', 'v', '^'
    # markers = {'random' : '.', 'roundrobin' : 'x','backpressure' : 'o','secondprice' : '+', 'secondback' : '*'}

    # f, axs = plt.subplots(1, 4, figsize=(28, 5), gridspec_kw=dict(width_ratios=[1, 1, 1, 1], wspace = 0.2, hspace = 0.2))
    sns.scatterplot(x=np.array(data_avg_del), y=data_avg_std, hue=methods, ax=axs[2], style=methods, s=icon_size, legend=title, alpha=1)
    # for i in range(len(methods)):
    #     sns.scatterplot(x=np.array(data_avg_del)[i], y=data_avg_std[i], hue=methods[i], ax=axs[2], marker=markers[i], s=130, legend=title) 

    # axs[1].legend(loc='center right', bbox_to_anchor=(1.25, 0.5))
    sns.scatterplot(x=np.array(data_avg_wait), y=data_avg_std_weighted, hue=methods, ax=axs[4], style=methods,  s=icon_size, legend=title, alpha=1)


    if len(data_avg_operator_diff_raw) > 0 and False:
        sns.barplot(x = methods, y = data_avg_operator_diff_raw, ax=axs[6])
        sns.barplot(x = methods, y = data_avg_operator_diff_wait, ax=axs[8])

    # axs[1].get_legend().get_texts(),



    # axs[0].set(xlabel = scenario)
    # axs[0].xaxis.get_label().set_fontsize(20)

    # axs[0].set_title(scenario, fontsize=26)
    # axs[0].title.get_label().set_fontsize(26)

    # extra = axs[0].twiny()
    # extra.set_xlabel(scenario, fontsize=26, labelpad=10)
    # extra.set_xticks([])

    # extra = axs[0].twinx()
    # extra.set_ylabel(scenario, fontsize=26, labelpad=-100, loc='left')
    # extra.set_yticks([])
    axs[0].set_ylabel(scenario, fontsize=26, labelpad=10)


    if title:

        axs[2].legend(markerscale=2, ncol=2)
        axs[4].legend(markerscale=2, ncol=2)

        plt.setp(axs[2].get_legend().get_texts(), fontsize='17')
        plt.setp(axs[2].get_legend().get_title(), fontsize='30')

        plt.setp(axs[4].get_legend().get_texts(), fontsize='17')
        plt.setp(axs[4].get_legend().get_title(), fontsize='20')

        
    #     subtitlesize = 20

    #     axs[0].set(ylabel = "Example Scenario")
    #     axs[1].set(ylabel = "Delay vs. \n Standard Deviation Delay")
    #     axs[2].set(ylabel = "Weighted Delay vs. \n Weighted Standard Deviation Delay")
    #     axs[3].set(ylabel = "Raw Summed Total Standard Deviation \n across Operators")
    #     axs[4].set(ylabel = "Weighted Summed Total Standard Deviation \n across Operators")

    #     axs[0].yaxis.get_label().set_fontsize(subtitlesize)
    #     axs[1].yaxis.get_label().set_fontsize(subtitlesize)
    #     axs[2].yaxis.get_label().set_fontsize(subtitlesize)
    #     axs[3].yaxis.get_label().set_fontsize(subtitlesize)
    #     axs[4].yaxis.get_label().set_fontsize(subtitlesize)

        # axs[0].set_title("Example Scenario", rotation=90, x=-0.3, y=0.2)
        # axs[2].set_title("Delay vs. \n Standard Deviation Delay", rotation=90, x=-0.3, y=0.2)
        # axs[4].set_title("Weighted Delay vs. \n Weighted Standard Deviation Delay", rotation=90, x=-0.3, y=0.05)
        # axs[0].set_title("Example Scenario", x=0.5, y=1.05, fontsize=30)
        # axs[2].set_title("Delay vs. \n Standard Deviation Delay", x=0.5, y=1.05, fontsize=26)
        # axs[4].set_title("Weighted Delay vs. \n Weighted Standard Deviation Delay", x=0.5, y=1.05, fontsize=26)
        # axs[6].set_title("Raw Standard Deviation \n across Operators", rotation=90, x=-0.3, y=0.15)
        # axs[8].set_title("Weighted Standard Deviation \n across Operators", rotation=90, x=-0.3, y=0.1)

        axs[0].set_title("$N_{aircraft} / N_{sectors} \, = \, 0.4$", x=0.5, y=1.05, fontsize=30)
        axs[2].set_title("$N_{aircraft} / N_{sectors} \, = \, 0.6$", x=0.5, y=1.05, fontsize=30)
        axs[4].set_title("$N_{aircraft} / N_{sectors} \, = \, 0.9$", x=0.5, y=1.05, fontsize=30)

        # extra = axs[0].twiny()
        # extra.set_xlabel(scenario, fontsize=26, labelpad=10)
        # extra.set_xticks([])



    # fig, ax = plt.subplots()
    # ax.bar(methods, data_avg_operator_diff_raw)
    # ax.set_ylabel("raw delay difference operator")

    # fig, ax = plt.subplots()
    # ax.bar(methods, data_avg_operator_diff_wait)
    # ax.set_ylabel("weighted delay difference operator")



    # f.set_axis_labels('Delay', "St. Dev. Delay")

    sidesize=18
    ticksize = 26

    # axs[1].set(xlabel= 'Delay', ylabel = "St. Dev. Delay")
    # axs[2].set(xlabel= 'Weighted Delay', ylabel = "Weighted St. Dev. Delay")
    # axs[3].set(ylabel = 'Raw Delay')
    # axs[4].set(ylabel = 'Weighted Delay') 
    # axs[0].axis('off')

    # axs[0].set_ymargin(0)
    axs[0].tick_params(
        axis='both',          # changes apply to the x-axis
        which='both',      # both major and minor ticks are affected
        bottom=False,      # ticks along the bottom edge are off
        top=False,         # ticks along the top edge are off
        left=False,
        right=False,
        labelbottom=False,
        labelleft=False) # labels along the bottom edge are off

    axs[2].set_xlabel('Delay (time steps)', fontsize=ticksize)
    axs[2].set_ylabel('St. Dev. Delay', fontsize=ticksize)
    axs[2].tick_params(labelsize=sidesize)

    axs[4].set_xlabel('Weighted Delay (cost * time steps)', fontsize=ticksize)
    axs[4].set_ylabel('Weighted St. Dev. Delay', fontsize=ticksize)
    axs[4].tick_params(labelsize=sidesize)

    # axs[6].set_ylabel('Raw Delay', fontsize=ticksize)
    # axs[8].set_ylabel('Weighted Delay', fontsize=ticksize)

    # axs[6].tick_params(labelsize=sidesize)
    # axs[8].tick_params(labelsize=sidesize)
    # axs[6].tick_params(axis='x', rotation=30, labelsize=ticksize)
    # axs[8].tick_params(axis='x', rotation=30, labelsize=ticksize)

    # axs[1].xaxis.get_label().set_fontsize(ticksize)
    # axs[2].xaxis.get_label().set_fontsize(ticksize)
    # axs[1].yaxis.get_label().set_fontsize(ticksize)
    # axs[2].yaxis.get_label().set_fontsize(ticksize)

    for ax in axs:
        ax.yaxis.labelpad = 10
        ax.xaxis.labelpad = 10

        # ax.title("test", fontdict = {'fontsize' : 100})

    # axs[0].legend(loc='center left')
    # axs[3].legend(loc='best')
    axs[1].remove()
    axs[3].remove()
    # axs[5].remove()
    # axs[7].remove()



def final_plotter(output, axs, scenario = "NULL", title= True):

    data_avg_rev	=	output['data_avg_rev'] 
    data_avg_del	=	output['data_avg_del'] 
    data_avg_std	=	output['data_avg_std'] 
    data_avg_confl	=	output['data_avg_confl'] 

    data_avg_wait	=	output['data_avg_wait'] 
    data_avg_pay	=	output['data_avg_pay'] 

    data_avg_std_weighted	=	output['data_avg_std_weighted'] 

    data_avg_wait_norm	=	output['data_avg_wait_norm'] 
    data_avg_pay_norm	=	output['data_avg_pay_norm'] 

    data_avg_operator_diff_raw	=	output['data_avg_operator_diff_raw'] 
    data_avg_operator_diff_wait	=	output['data_avg_operator_diff_wait'] 

    data_std_operator_diff_raw	=	output['data_std_operator_diff_raw'] 
    data_std_operator_diff_wait	=	output['data_std_operator_diff_wait']

    (grid, active, schedule) = output['example'] 

    # section on example printing 

    layout = Layout(layout_pointy, Point(1, 1), Point(0, 0))
    locations = {}
    for ag in active:
        # print(ag._id, ag.loc)
        locations[ag.loc] = (ag._id, ag.finished, ag.bid[0], ag.bid[1])
    

    # fig, ax = plt.subplots(1, figsize=(radius * 2, radius * 2), dpi= 2*radius * 25,)

    # ax.set(xlim=(-7, 7), ylim=(-7,7))
    
    for h in grid.coords_l:

        x, y = hex_to_pixel(layout, h)
        hex = RegularPolygon((x,y), numVertices=6, radius= 1, 
                             orientation=np.radians(0), 
                             alpha=0.2, edgecolor='k')
        axs[0].add_patch(hex)
        

    for ag in active:
        x_s, y_s = hex_to_pixel(layout, ag._origin)
        x_d, y_d = hex_to_pixel(layout, ag._dest)


        color = 'k'
        if ag._operator and False:      ## turned off color for operators in example
            if ag._operator == 1: color = 'b'
            if ag._operator == 2: color = 'r'
            if ag._operator == 3: color = 'g'
            if ag._operator == 4: color = 'orange'
            if ag._operator == 5: color = 'yellow'
            if ag._operator == 6: color = 'purple'

        arrow = FancyArrow(x_s, y_s, x_d - x_s, y_d - y_s, 
                            color = color, 
                            head_width = 0.1, head_length = 0.1)
        axs[0].add_patch(arrow)

    axs[0].set_aspect('equal')
    axs[0].autoscale()

    # sns.set_theme()
    # sns.set(font_scale=1.5)
    icon_size = 500
    methods = ["random", "roundrobin", "backpressure", "accrueddelay", "reversals", "secondprice", "secondback"]
    # markers = ['.', 'x', 'o', '+', '*']
    # ',', '.', 'o', 'v', '^'
    # markers = {'random' : '.', 'roundrobin' : 'x','backpressure' : 'o','secondprice' : '+', 'secondback' : '*'}

    # f, axs = plt.subplots(1, 4, figsize=(28, 5), gridspec_kw=dict(width_ratios=[1, 1, 1, 1], wspace = 0.2, hspace = 0.2))
    sns.scatterplot(x=np.array(data_avg_del), y=data_avg_std, hue=methods, ax=axs[2], style=methods, s=icon_size, legend=title, alpha=1)
    # for i in range(len(methods)):
    #     sns.scatterplot(x=np.array(data_avg_del)[i], y=data_avg_std[i], hue=methods[i], ax=axs[2], marker=markers[i], s=130, legend=title) 

    # axs[1].legend(loc='center right', bbox_to_anchor=(1.25, 0.5))
    sns.scatterplot(x=np.array(data_avg_wait), y=data_avg_std_weighted, hue=methods, ax=axs[4], style=methods,  s=icon_size, legend=title, alpha=1)


    if len(data_avg_operator_diff_raw) > 0:
        sns.barplot(x = methods, y = data_avg_operator_diff_raw, ax=axs[6])
        sns.barplot(x = methods, y = data_avg_operator_diff_wait, ax=axs[8])

    # axs[1].get_legend().get_texts(),



    # axs[0].set(xlabel = scenario)
    # axs[0].xaxis.get_label().set_fontsize(20)

    # axs[0].set_title(scenario, fontsize=26)
    # axs[0].title.get_label().set_fontsize(26)

    extra = axs[0].twiny()
    extra.set_xlabel(scenario, fontsize=26, labelpad=10)
    extra.set_xticks([])


    if title:

        plt.setp(axs[2].get_legend().get_texts(), fontsize='17')
        plt.setp(axs[2].get_legend().get_title(), fontsize='30')

        plt.setp(axs[4].get_legend().get_texts(), fontsize='17')
        plt.setp(axs[4].get_legend().get_title(), fontsize='20')

        
    #     subtitlesize = 20

    #     axs[0].set(ylabel = "Example Scenario")
    #     axs[1].set(ylabel = "Delay vs. \n Standard Deviation Delay")
    #     axs[2].set(ylabel = "Weighted Delay vs. \n Weighted Standard Deviation Delay")
    #     axs[3].set(ylabel = "Raw Summed Total Standard Deviation \n across Operators")
    #     axs[4].set(ylabel = "Weighted Summed Total Standard Deviation \n across Operators")

    #     axs[0].yaxis.get_label().set_fontsize(subtitlesize)
    #     axs[1].yaxis.get_label().set_fontsize(subtitlesize)
    #     axs[2].yaxis.get_label().set_fontsize(subtitlesize)
    #     axs[3].yaxis.get_label().set_fontsize(subtitlesize)
    #     axs[4].yaxis.get_label().set_fontsize(subtitlesize)

        axs[0].set_title("Example Scenario", rotation=90, x=-0.3, y=0.2)
        axs[2].set_title("Delay vs. \n Standard Deviation Delay", rotation=90, x=-0.3, y=0.2)
        axs[4].set_title("Weighted Delay vs. \n Weighted Standard Deviation Delay", rotation=90, x=-0.3, y=0.05)
        axs[6].set_title("Raw Standard Deviation \n across Operators", rotation=90, x=-0.3, y=0.15)
        axs[8].set_title("Weighted Standard Deviation \n across Operators", rotation=90, x=-0.3, y=0.1)

        # extra = axs[0].twiny()
        # extra.set_xlabel(scenario, fontsize=26, labelpad=10)
        # extra.set_xticks([])

    # fig, ax = plt.subplots()
    # ax.bar(methods, data_avg_operator_diff_raw)
    # ax.set_ylabel("raw delay difference operator")

    # fig, ax = plt.subplots()
    # ax.bar(methods, data_avg_operator_diff_wait)
    # ax.set_ylabel("weighted delay difference operator")



    # f.set_axis_labels('Delay', "St. Dev. Delay")

    sidesize=18
    ticksize = 20

    # axs[1].set(xlabel= 'Delay', ylabel = "St. Dev. Delay")
    # axs[2].set(xlabel= 'Weighted Delay', ylabel = "Weighted St. Dev. Delay")
    # axs[3].set(ylabel = 'Raw Delay')
    # axs[4].set(ylabel = 'Weighted Delay') 
    axs[0].axis('off')

    # axs[0].set_ymargin(0)
    # axs[0].tick_params(
    #     axis='both',          # changes apply to the x-axis
    #     which='both',      # both major and minor ticks are affected
    #     bottom=False,      # ticks along the bottom edge are off
    #     top=False,         # ticks along the top edge are off
    #     labelbottom=False) # labels along the bottom edge are off

    axs[2].set_xlabel('Delay (time units)', fontsize=ticksize)
    axs[2].set_ylabel('St. Dev. Delay', fontsize=ticksize)
    axs[2].tick_params(labelsize=sidesize)

    axs[4].set_xlabel('Weighted Delay (time units)', fontsize=ticksize)
    axs[4].set_ylabel('Weighted St. Dev. Delay', fontsize=ticksize)
    axs[4].tick_params(labelsize=sidesize)

    axs[6].set_ylabel('Raw Delay', fontsize=ticksize)
    axs[8].set_ylabel('Weighted Delay', fontsize=ticksize)

    axs[6].tick_params(labelsize=sidesize)
    axs[8].tick_params(labelsize=sidesize)
    axs[6].tick_params(axis='x', rotation=30, labelsize=ticksize)
    axs[8].tick_params(axis='x', rotation=30, labelsize=ticksize)

    # axs[1].xaxis.get_label().set_fontsize(ticksize)
    # axs[2].xaxis.get_label().set_fontsize(ticksize)
    # axs[1].yaxis.get_label().set_fontsize(ticksize)
    # axs[2].yaxis.get_label().set_fontsize(ticksize)

    for ax in axs:
        ax.yaxis.labelpad = 10
        ax.xaxis.labelpad = 10

        # ax.title("test", fontdict = {'fontsize' : 100})

    # axs[0].legend(loc='center left')
    # axs[3].legend(loc='best')
    axs[1].remove()
    axs[3].remove()
    axs[5].remove()
    axs[7].remove()