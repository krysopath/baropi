#!/usr/bin/env python3
# coding=utf-8
import baropi as b

b.init_db()

plt, fig = b.create_graph(
    b.get_last_samples({'hours': 6})
)
plt.show()
plt.savefig("out.png", dpi=1000, format='png')
