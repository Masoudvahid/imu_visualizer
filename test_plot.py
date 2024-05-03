import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style

matplotlib.use('TkAgg')  # Set the backend to TkAgg

style.use('fivethirtyeight')

fig = plt.figure()
ax1 = fig.add_subplot(1, 1, 1)


def animate(i):
    graph_data = open(r"C:\Users\Admin\Desktop\graphics.txt", 'r').read()
    lines = graph_data.split('\n')

    acc = []
    time = []

    for line in lines:
        if len(line) > 1:
            x, y, z, t = line.split(',')
            acc.append([float(x), float(y), float(z)])
            time.append(float(t))

    ax1.clear()
    ax1.set_xlim(time[-1] - 7, time[-1] + 7)
    ax1.set_ylim(-2, 2)
    plt.plot(time, acc)


ani = animation.FuncAnimation(fig, animate, interval=10)
plt.show()
