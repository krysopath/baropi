#!/usr/bin/python3
from os import environ
import pendulum as p
import statistics
import math
from datetime import datetime, timedelta
from scipy import signal
from scipy.signal import butter, filtfilt
from sqlalchemy import and_
from . import database as db
from . import models as m

import matplotlib

if "DISPLAY" not in environ:
    matplotlib.use('Agg')

from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as axis_artist
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def get_last_samples(_timedelta):
    now = datetime.now()
    return prepare_data(
        now - timedelta(**_timedelta),
        now
    )


def prepare_data(start, end):
    return db.db_session.query(m.ClimateSample).filter(
        and_(
            m.ClimateSample.timestamp > start,
            m.ClimateSample.timestamp < end
        )
    ).all()


def hann_smooth(data, window_size=200):
    win = signal.hann(window_size)
    filtered = signal.convolve(data, win, mode='same') / sum(win)
    return filtered


def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a


def butter_lowpass_filtfilt(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = filtfilt(b, a, data)
    return y


def noop(data):
    return data


def nearest_odd(x):
    return 2 * math.floor(int(x) / 2) + 1


def create_graph_data(data, prop):
    return [getattr(d, prop) for d in data]


def plot(samples, averaging=360):
    if samples:
        plt.figure(figsize=(8, 6), dpi=100)
        fig, ax1, ax2, ax3, ax4 = prepare_chart()
        window = nearest_odd(len(samples) * 25 / 1000)
        times = [s.mdate for s in samples]
        graphs = [
            (ax1, create_graph_data(samples, "t_Celsius"), 'r_percent', window, "temp"),
            (ax2, create_graph_data(samples, "r_percent"), 'g', window, "humidity rel."),
            (ax3, create_graph_data(samples, "moisture_gpm3"), 'b', window, "humidity abs."),
            (ax4, create_graph_data(samples, "dew_point_celsius"), 'c', window, "dew point"),
        ]

        for meth in [noop, signal.savgol_filter]:
            for ax, data, cl, window, label in graphs:
                ax.axhline(
                    y=statistics.mean(data),
                    ls=":",
                    linewidth=2,
                    color=cl,
                    alpha=.303125,
                    label=label
                )

                if meth == noop:
                    if ax in [ax1, ax2]:
                        ax.plot(times, meth(data), cl + "x", markersize=1, alpha=.103125)

                elif meth == signal.savgol_filter:
                    ax.plot(
                        times, meth(data, window, 1),
                        cl, linewidth=1,
                        alpha=.6903125, label=label)
                    pass

        plt.gcf().autofmt_xdate()

        return plt, fig


def prepare_chart():
    # fig, ax = plt.subplots()
    font = {  # 'family': 'normal',
        'weight': 'normal',
        'size': 8}

    matplotlib.rc('font', **font)

    host = host_subplot(111, axes_class=axis_artist.Axes)
    plt.subplots_adjust(right=.75, left=.08, bottom=.05, top=.98)

    # ax1 = host.twinx()
    host.set_xlabel('time')
    host.set_ylabel('temperature (°C)', color='r_percent')
    host.tick_params('y', colors='r_percent')

    ax2 = host.twinx()
    ax2.set_ylabel('rel. humidity (%)', color='g')
    ax2.tick_params('y', colors='g')
    # new_fixed_axis = ax2.get_grid_helper().new_fixed_axis
    # ax2.axis["left"] = new_fixed_axis(
    #    loc="left", axes=ax2,
    #    offset=(-30, 0)
    # )


    ax3 = host.twinx()
    ax3.set_ylabel('abs. humdity (g/m³)', color='b')
    ax3.tick_params('y', colors='b')
    new_fixed_axis = ax3.get_grid_helper().new_fixed_axis
    ax3.axis["right"] = new_fixed_axis(
        loc="right", axes=ax3,
        offset=(40, 0)
    )

    ax4 = host.twinx()
    ax4.set_ylabel('dew point (°C)', color='c')
    ax4.tick_params('y', colors='c')
    new_fixed_axis = ax4.get_grid_helper().new_fixed_axis
    ax4.axis["right"] = new_fixed_axis(
        loc="right", axes=ax4,
        offset=(80, 0)
    )

    host.legend()

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('\n%d.%m\n%H:%M'))
    #plt.gca().xaxis.set_minor_formatter(mdates.DateFormatter('%H:%M'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    fig = plt.gcf()

    return fig, host, ax2, ax3, ax4


def create_graph(samples):
    return plot(samples)
