""" Stript to visualize the results about the straining in TMDs
author: Bert Jorissen
date: 4 nov 2022
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider, CheckButtons, Button, RadioButtons, RangeSlider
import cloudpickle
import pickle
from urllib.request import urlopen, Request


class TmdPresentation:
    def __init__(self, data_file: str, cloud=True):
        self.data_loaded = False
        self.data_file = data_file
        self.cloud = cloud

        # figure
        self.fig_main = []
        self.fig_bands = []

        # label
        self.fig_label_main = "TMD picker"
        self.fig_label_bands = "TMD bands"

        # lines
        self.line_bands = []
        self.line_bands_zero = []

        # axes
        self.ax_bands = []

        # data
        self.data = {}
        self.u_xx = 0.
        self.u_yy = 0.
        self.u_xy = 0.
        self.name = "MoS2"
        self.zero = False
        self.biaxial = False

        # widget layout
        self.bl_margin = 0.05
        self.bl_h_dist = 0.05
        self.bl_h_heig = (1 - 2 * self.bl_margin + self.bl_h_dist) / 11
        self.bl_h_hdis = self.bl_h_heig - self.bl_h_dist

        # widgets
        self.b_xslider = []
        self.b_yslider = []
        self.b_slider_uxx = []
        self.b_slider_uyy = []
        self.b_slider_uxy = []
        self.b_reset = []
        self.b_zero = []
        self.b_name = []

        # call gui
        self.gui()

    def show_bands_figure(self):
        if not self.fig_bands:
            if plt.fignum_exists(self.fig_label_bands):
                plt.close(self.fig_label_bands)
            self.fig_bands = plt.figure(self.fig_label_bands)
            self.ax_bands = self.fig_bands.add_subplot()
            self.fig_bands.canvas.mpl_connect('close_event', self.call_close_bands)
            self.ax_bands.text(0, 0, "Click a button to start.")

    def gui(self):
        if plt.fignum_exists(self.fig_label_main):
            plt.close(self.fig_label_main)
        self.fig_main = plt.figure(self.fig_label_main, figsize=(2, 5))
        self.fig_main.canvas.mpl_connect('close_event', self.call_close_main)

        # widgets - draw
        self.b_xslider = RangeSlider(
            ax=self.fig_main.add_axes([.28, self.bl_margin + 10 * self.bl_h_heig, .4, self.bl_h_hdis]),
            label=r"$x_{scale}$",
            valmin=0,
            valmax=1,
            valinit=(0, 1),
            valfmt="%d",
            orientation="horizontal"
        )
        self.b_yslider = RangeSlider(
            ax=self.fig_main.add_axes([.28, self.bl_margin + 9 * self.bl_h_heig, .4, self.bl_h_hdis]),
            label=r"$y_{scale}$",
            valmin=-14.,
            valmax=2.,
            valinit=(-12., 0.),
            valfmt="%+.1f",
            orientation="horizontal"
        )
        self.b_slider_uxx = Slider(
            ax=self.fig_main.add_axes([.28, self.bl_margin + 8 * self.bl_h_heig, .45, self.bl_h_hdis]),
            label=r"$u_{xx}$ (%)",
            valmin=0,
            valmax=0.0001,
            valinit=self.u_xx,
            valfmt="%+.3f",
            orientation="horizontal"
        )
        self.b_slider_uyy = Slider(
            ax=self.fig_main.add_axes([.28, self.bl_margin + 7 * self.bl_h_heig, .45, self.bl_h_hdis]),
            label=r"$u_{yy}$ (%)",
            valmin=0,
            valmax=0.0001,
            valinit=self.u_yy,
            valfmt="%+.3f",
            orientation="horizontal"
        )
        self.b_slider_uxy = Slider(
            ax=self.fig_main.add_axes([.28, self.bl_margin + 6 * self.bl_h_heig, .45, self.bl_h_hdis]),
            label=r"$u_{xy}$ (%)",
            valmin=0,
            valmax=0.0001,
            valinit=self.u_xy,
            valfmt="%+.3f",
            orientation="horizontal"
        )
        self.b_reset = Button(
            ax=self.fig_main.add_axes([.15, self.bl_margin + 5 * self.bl_h_heig, .70, self.bl_h_hdis]),
            label="Reset"
        )
        self.b_zero = CheckButtons(
            ax=self.fig_main.add_axes([.15, self.bl_margin + 3 * self.bl_h_heig, .70,
                                       self.bl_h_hdis + self.bl_h_heig]),
            labels=["show 0%", "biaxial"],
            actives=[self.zero, self.biaxial]
        )
        self.b_name = RadioButtons(
            ax=self.fig_main.add_axes([.15, self.bl_margin + 0 * self.bl_h_heig, .70,
                                       self.bl_h_heig * 2 + self.bl_h_hdis]),
            labels=["MoS2", "MoSe2", "WS2", "WSe2"]
        )

        # widgets - connect
        self.b_xslider.on_changed(self.call_xslider)
        self.b_yslider.on_changed(self.call_yslider)
        self.b_slider_uxx.on_changed(self.call_u_xx_change)
        self.b_slider_uyy.on_changed(self.call_u_yy_change)
        self.b_slider_uxy.on_changed(self.call_u_xy_change)
        self.b_reset.on_clicked(self.call_reset)
        self.b_zero.on_clicked(self.call_radio)
        self.b_name.on_clicked(self.call_name)

        # call the bands figure
        self.show_bands_figure()

    def call_close_main(self, event):
        self.fig_main = []

    def call_close_bands(self, event):
        self.fig_bands = []
        self.ax_bands = []
        self.line_bands = []

    def call_xslider(self, val):
        if not self.fig_main:
            self.show_bands_figure()
        self.x_range = self.b_xslider.val
        self.plot_bands()

    def call_yslider(self, val):
        if not self.fig_main:
            self.show_bands_figure()
        self.y_range = self.b_yslider.val
        self.plot_bands()

    def call_u_xx_change(self, val):
        if not self.fig_main:
            self.show_bands_figure()
        if not self.b_slider_uxx.val == self.u_xx:
            self.u_xx = self.b_slider_uxx.val
            if self.biaxial:
                self.u_yy = self.u_xx
                self.b_slider_uyy.set_val(self.u_yy)
            self.plot_bands()

    def call_u_yy_change(self, val):
        if not self.fig_main:
            self.show_bands_figure()
        if not self.b_slider_uyy.val == self.u_yy:
            self.u_yy = self.b_slider_uyy.val
            if self.biaxial:
                self.u_xx = self.u_yy
                self.b_slider_uxx.set_val(self.u_xx)
            self.plot_bands()

    def call_u_xy_change(self, val):
        if not self.fig_main:
            self.show_bands_figure()
        self.u_xy = self.b_slider_uxy.val
        self.plot_bands()

    def call_reset(self, event):
        if not self.fig_main:
            self.show_bands_figure()
        self.b_slider_uxx.reset()
        self.b_slider_uyy.reset()
        self.b_slider_uxy.reset()
        self.u_xx = 0.
        self.u_yy = 0.
        self.u_xy = 0.
        self.plot_bands()

    def call_name(self, name):
        if not self.fig_main:
            self.show_bands_figure()
        self.name = name
        self.k_path = self.k_path_as_1d(self.data[self.name]["k_path"])
        self.k_path_points = self.k_path[self.data[self.name]["k_path_point_indices"]]
        self.plot_bands()

    def call_radio(self, label):
        if not self.fig_main:
            self.show_bands_figure()
        self.zero = self.b_zero.get_status()[0]
        self.biaxial = self.b_zero.get_status()[1]
        if self.biaxial:
            self.u_yy = self.u_xx
            self.b_slider_uyy.set_val(self.u_yy)
        self.plot_bands()

    def plot_bands(self):
        self.show_bands_figure()
        if not self.data_loaded:
            self.ax_bands.cla()
            self.ax_bands.text(0, .2, "Data is being loaded..... (this can take a minute)", color="C2")
            plt.draw()
            plt.pause(0.5)
            if self.cloud:
                self.data = cloudpickle.load(urlopen(Request(self.data_file)))
            else:
                self.data = pickle.load(open(self.data_file, 'rb'))

            self.u_xx_lims = (np.min([np.min(self.data[name]["u"][:, 0]) for name in [*self.data]]),
                              np.max([np.max(self.data[name]["u"][:, 0]) for name in [*self.data]]))

            self.u_yy_lims = (np.min([np.min(self.data[name]["u"][:, 1]) for name in [*self.data]]),
                              np.max([np.max(self.data[name]["u"][:, 1]) for name in [*self.data]]))

            self.u_xy_lims = (np.min([np.min(self.data[name]["u"][:, 2]) for name in [*self.data]]),
                              np.max([np.max(self.data[name]["u"][:, 2]) for name in [*self.data]]))
            self.k_path = self.k_path_as_1d(self.data[self.name]["k_path"])
            self.k_path_points = self.k_path[self.data[self.name]["k_path_point_indices"]]

            self.max_k = np.max([self.data[name]["k_path_point_indices"][-1] for name in [*self.data]]) - 1
            self.x_range = [0, self.max_k]
            self.y_range = [-12., 0.]

            self.b_slider_uxx.valmin, self.b_slider_uxx.valmax = self.u_xx_lims
            self.b_slider_uyy.valmin, self.b_slider_uyy.valmax = self.u_yy_lims
            self.b_slider_uxy.valmin, self.b_slider_uxy.valmax = self.u_xy_lims
            self.b_slider_uxx.ax.set_xlim(self.b_slider_uxx.valmin, self.b_slider_uxx.valmax)
            self.b_slider_uyy.ax.set_xlim(self.b_slider_uyy.valmin, self.b_slider_uyy.valmax)
            self.b_slider_uxy.ax.set_xlim(self.b_slider_uxy.valmin, self.b_slider_uxy.valmax)

            self.b_xslider.valmin, self.b_xslider.valmax = self.x_range
            self.b_yslider.valmin, self.b_yslider.valmax = self.y_range
            self.b_xslider.ax.set_xlim(self.x_range)
            self.b_yslider.ax.set_xlim(self.y_range)
            self.b_xslider.val = (self.x_range[0], self.x_range[1])
            self.b_yslider.val = (self.y_range[0], self.y_range[1])
            self.data_loaded = True

        self.ax_bands.cla()
        idx = self.find_nearest(self.u_xx, self.u_yy, self.u_xy)
        u_loc = self.data[self.name]["u"][idx]
        self.ax_bands.set_title(
            r"{0}: $u_{{xx}}$={1:.3f}, $u_{{yy}}$={2:.3f}, $u_{{xy}}$={3:.3f}".format(self.name, *u_loc))

        if self.zero:
            self.line_bands_zero = self.ax_bands.plot(
                self.k_path,
                self.data[self.name]["energy"][self.find_nearest(0, 0, 0)],
                color="C1", ls=":"
            )

        self.line_bands = self.ax_bands.plot(
            self.k_path,
            self.data[self.name]["energy"][idx],
            color="C0"
        )
        if self.zero:
            self.ax_bands.legend([self.line_bands[0], self.line_bands_zero[0]], ["strain", "no strain"])
        else:
            self.ax_bands.legend([self.line_bands[0]], ["strain"])
        for k_index in self.k_path_points:
            self.ax_bands.axvline(k_index, color="black", ls=":")
        self.ax_bands.set_xticks(self.k_path_points,
                                 [r"$\Gamma$", r"$M_1$", r"$K_1$", r"$\Gamma$", r"$K_2$", r"$M_2$", r"$\Gamma$"])
        self.ax_bands.set_ylabel("E (eV)")
        self.ax_bands.set_xlim(self.k_path[int(np.min((self.x_range[0], len(self.k_path) - 1)))],
                               self.k_path[int(np.min((self.x_range[1], len(self.k_path) - 1)))])
        self.ax_bands.set_ylim(*self.y_range)
        plt.show()

    def find_nearest(self, u_xx, u_yy, u_xy):
        return np.sum((self.data[self.name]["u"] - np.array([u_xx, u_yy, u_xy])) ** 2, axis=1).argmin()

    def k_path_as_1d(self, k_path):
        """ Return a 1D respresentation of the Path"""
        return np.append([0], np.sqrt((np.diff(k_path, axis=0) ** 2).dot([[1]] * len(k_path[0]))).cumsum())


def run_script():
    return TmdPresentation(data_file="http://nc.tfm.uantwerpen.be/s/HJRpRTTssAKM67P/download/bands.pickle", cloud=True)


if __name__ == "__main__":
    run_script()
