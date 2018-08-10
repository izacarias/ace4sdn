import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import random
import math
import argparse
from pprint import pprint

FIELD_X = 500
FIELD_Y = 500
CONN_R = 250
STA_BASE_NAME = '10.0.0.%s'

def main(num_nodes):
    coord_x = []
    coord_y = []
    names = []
    for i in range(0, num_nodes):
        coord_x.append(random.randint(1, FIELD_X))
        coord_y.append(random.randint(1, FIELD_Y))
        names.append(STA_BASE_NAME % str(i + 1))

    fig, ax = plt.subplots()
    ax.plot(coord_x, coord_y, 'o')
    for i in range(0, num_nodes):
        ax.annotate(names[i],
                    xy=(1, 5),
                    xycoords='data',
                    xytext=(coord_x[i]-3, coord_y[i]-4))
    ax.set_title('Teste de plot')

    neighbors = dict()    
    for i in range(0, num_nodes):
        nh = []
        for j in range(0, num_nodes):
            if i == j:
                continue
            x1, y1 = (coord_x[i], coord_y[i])
            x2, y2 = (coord_x[j], coord_y[j])
            d = math.sqrt(math.pow(x2-x1, 2) + math.pow(y2 - y1, 2))
            if d < CONN_R:
                plt.plot([x1, x2], [y1, y2], 'k-')
                nh.append(names[j])
        neighbors[names[i]] = nh       

    pprint(neighbors)
    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-nodes", "-n",
        help="generate a scenario with the given number of nodes.",
        type=int)
    parser.add_argument("-size", "-s",
        help="generate a field with the given size",
        default=500,
        type=int)
    args = parser.parse_args()
    FIELD_X = FIELD_Y = args.size
    main(args.nodes)
