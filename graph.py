import matplotlib
# matplotlib.use('agg')
import matplotlib.pyplot as plt

def draw_graph(actions):

    fig, (ax0, ax1, ax2) = plt.subplots(nrows = 3)

    for action, stats in actions.items():
        action, colour = action
        ax0.plot(stats[0], stats[1], label = action, color = colour)
    # ax0.plot(actions["all_actions"][0], actions["all_actions"][1], label = "All actions", color = "blue")

    ax0.grid(True)
    ax0.set_facecolor("#E9E9E9")
    ax0.legend(loc = "upper left")

    fig.set_size_inches(13, 13)
    plt.show()
