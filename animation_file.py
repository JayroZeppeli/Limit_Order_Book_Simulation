"""import matplotlib; matplotlib.use("TkAgg")
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation


fig, ax = plt.subplots()

x = np.arange(0, 2*np.pi, 0.01)
line, = ax.plot(x, np.sin(x))


def animate(i):
    line.set_ydata(np.sin(x + i/10.0))  # update the data
    return line,


# Init only required for blitting to give a clean slate.
def init_universe():
    line.set_ydata(np.ma.array(x, mask=True))
    return line,

ani = animation.FuncAnimation(fig, animate, np.arange(1, 20000), init_func=init_universe,
                              interval=25, blit=True)
plt.show()"""
import matplotlib; matplotlib.use("TkAgg")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation



# Préparer les données
x = np.linspace(0, 100, 1000)
y = np.sin(x)

fig, ax = plt.subplots()

ax.set_xlim([0, 10])
ax.set_ylim([-2, 2])

line, = ax.plot([], [], 'ro')


# Fonction de mise à jour à chaque frame
def update(frame):
    print(frame)
    ax.set_xlim([frame/12-5, 5 + frame/12])
    line.set_data(x[:frame], y[:frame])
    return line,


# Création de l'animation
ani = FuncAnimation(fig, update, frames=800, interval=25)

plt.show()

