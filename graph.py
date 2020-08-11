import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import numpy as np

def add_multiple(*args):
    """Does np.add() with any number of arrays.
    Arrays must be the same length.

    Returns:
        np.array: Arrays added together
    """
    out = args[0]
    for arg in args[1:]:
        out = np.add(out, arg)
    return out

def draw_graph(longterm_actions, shortterm_actions, bar_actions):

    fig, (ax0, ax1, ax2) = plt.subplots(nrows = 3)
    axes = (ax0, ax1, ax2)

    for action, stats in longterm_actions.items():
        action, colour = action
        ax0.plot(stats[0], stats[1], label = action, color = colour)

    for action, stats in shortterm_actions.items():
        action, colour = action
        ax1.plot(stats[0], stats[1], label = action, color = colour)

    action_names = list(bar_actions[1].keys())
    for k in action_names:      
        ax2.bar(
            bar_actions[0], add_multiple(*bar_actions[1].values()),
            0.5, color = bar_actions[2][k], label = k
        )
        bar_actions[1].pop(k)

    for c, ax in enumerate(axes, 0):
        ax.set_facecolor("#E9E9E9")
        ax.legend(loc = "upper left")
        if c < 2:
            ax.grid(True)
        else:
            ax.xaxis.set_tick_params(rotation = 90)

    fig.set_size_inches(13, 13)
    plt.savefig("graph.png")
    return "graph.png"

