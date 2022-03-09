import numpy as np
import pandas as pd
import matplotlib.pyplot as pl

try:
    coocc = np.load("cooccurrences.npy")
except:
    print("Error: couldn't find `cooccurrences.npy`")

try:
    whitelist = list(pd.read_csv("whitelist.csv")['whitelist'])
except:
    print("Error: couldn't find `whitelist.csv`")

fig, ax = pl.subplots(1, 1)
ax.imshow(coocc)
ax.set_xticks(list(range(len(whitelist))), labels=whitelist)
ax.set_yticks(list(range(len(whitelist))), labels=whitelist)
pl.setp(ax.get_xticklabels(), rotation=90, horizontalalignment='right')
pl.show()
