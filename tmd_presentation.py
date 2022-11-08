""" Stript to visualize the results about the straining in TMDs
author: Bert Jorissen
date: 4 nov 2022
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider, CheckButtons, Button, RadioButtons, RangeSlider
import cloudpickle
from urllib.request import urlopen, Request
from matplotlib.pyplot import Figure, Line2D, Axes
from typing import List, Optional


class TmdPresentation:
    def __init__(self, data: dict):
        # figure
        self._fig: Optional[Figure] = None

        # label
        self._fig_label = "TMD picker"

        # lines
        self._line_bands: Optional[List[Line2D, ...]] = None
        self._line_bands_zero: Optional[List[Line2D, ...]] = None

        # axes
        self._ax_bands: Optional[Axes] = None

        # data
        self._data = data
        self._u = np.array([0., 0., 0.])
        self._name = [*self._data][0]
        self._zero = False
        self._biaxial = False

        self._u_lims = [(np.min([np.min(self._data[name]["u"][:, i]) for name in [*self._data]]),
                        np.max([np.max(self._data[name]["u"][:, i]) for name in [*self._data]]))
                        for i in range(3)]
        self._k_path = self._k_path_as_1d(self._data[self._name]["k_path"])
        self._k_path_points = self._k_path[self._data[self._name]["k_path_point_indices"]]

        self._max_k = np.max([self._data[name]["k_path_point_indices"][-1] for name in [*self._data]]) - 1
        self._x_range = [0, self._max_k]
        self._y_range = [np.floor(np.min([np.min(self._data[name]["energy"]) for name in [*self._data]])),
                         np.ceil(np.max([np.max(self._data[name]["energy"]) for name in [*self._data]]))]

        # widget layout
        self._n_cols = 4
        self._bl_margin = 0.05
        self._bl_h_dist = 0.05
        self._bl_h_heig = (1 - 2 * self._bl_margin + self._bl_h_dist) / 11
        self._bl_h_hdis = self._bl_h_heig - self._bl_h_dist

        # widgets
        self._b_xslider: Optional[RangeSlider] = None
        self._b_yslider: Optional[RangeSlider] = None
        self._b_slider_uxx: Optional[Slider] = None
        self._b_slider_uyy: Optional[Slider] = None
        self._b_slider_uxy: Optional[Slider] = None
        self._b_reset: Optional[Button] = None
        self._b_zero: Optional[CheckButtons] = None
        self._b_name: Optional[RadioButtons] = None

        # call gui
        self.gui()

    def gui(self):
        if plt.fignum_exists(self._fig_label):
            plt.close(self._fig_label)
        self._fig = plt.figure(self._fig_label, figsize=(10, 5))
        self._fig.canvas.mpl_connect('close_event', self._call_close_bands)
        self._ax_bands = self._fig.add_axes([
            .70 / self._n_cols + .15 / self._n_cols * 4,
            self._bl_margin + 0 * self._bl_h_heig,
            1 - (.70 / self._n_cols + .15 / self._n_cols * 4) - .15 / self._n_cols,
            10 * self._bl_h_heig + self._bl_h_hdis
        ])

        # widgets - draw
        self._b_xslider = RangeSlider(
            ax=self._fig.add_axes([
                .28 / self._n_cols,
                self._bl_margin + 10 * self._bl_h_heig,
                .4 / self._n_cols,
                self._bl_h_hdis]),
            label=r"$x_{scale}$",
            valmin=0,
            valmax=self._max_k,
            valinit=(0, self._max_k),
            valfmt="%d",
            orientation="horizontal"
        )
        self._b_yslider = RangeSlider(
            ax=self._fig.add_axes([
                .28 / self._n_cols,
                self._bl_margin + 9 * self._bl_h_heig,
                .4 / self._n_cols,
                self._bl_h_hdis
            ]),
            label=r"$y_{scale}$",
            valmin=self._y_range[0],
            valmax=self._y_range[1],
            valinit=self._y_range,
            valfmt="%+.1f",
            orientation="horizontal"
        )
        self._b_slider_uxx = Slider(
            ax=self._fig.add_axes([
                .28 / self._n_cols,
                self._bl_margin + 8 * self._bl_h_heig,
                .45 / self._n_cols,
                self._bl_h_hdis
            ]),
            label=r"$u_{xx}$ (%)",
            valmin=self._u_lims[0][0],
            valmax=self._u_lims[0][1],
            valinit=self._u[0],
            valfmt="%+.3f",
            orientation="horizontal"
        )
        self._b_slider_uyy = Slider(
            ax=self._fig.add_axes([
                .28 / self._n_cols,
                self._bl_margin + 7 * self._bl_h_heig,
                .45 / self._n_cols,
                self._bl_h_hdis
            ]),
            label=r"$u_{yy}$ (%)",
            valmin=self._u_lims[1][0],
            valmax=self._u_lims[1][1],
            valinit=self._u[1],
            valfmt="%+.3f",
            orientation="horizontal"
        )
        self._b_slider_uxy = Slider(
            ax=self._fig.add_axes([
                .28 / self._n_cols,
                self._bl_margin + 6 * self._bl_h_heig,
                .45 / self._n_cols,
                self._bl_h_hdis
            ]),
            label=r"$u_{xy}$ (%)",
            valmin=self._u_lims[2][0],
            valmax=self._u_lims[2][1],
            valinit=self._u[2],
            valfmt="%+.3f",
            orientation="horizontal"
        )
        self._b_reset = Button(
            ax=self._fig.add_axes([
                .15 / self._n_cols,
                self._bl_margin + 5 * self._bl_h_heig,
                .70 / self._n_cols,
                self._bl_h_hdis
            ]),
            label="Reset"
        )
        self._b_zero = CheckButtons(
            ax=self._fig.add_axes([
                .15 / self._n_cols,
                self._bl_margin + 3 * self._bl_h_heig,
                .70 / self._n_cols,
                self._bl_h_hdis + self._bl_h_heig
            ]),
            labels=["show 0%", "biaxial"],
            actives=[self._zero, self._biaxial]
        )
        self._b_name = RadioButtons(
            ax=self._fig.add_axes([
                .15 / self._n_cols,
                self._bl_margin + 0 * self._bl_h_heig,
                .70 / self._n_cols,
                self._bl_h_heig * 2 + self._bl_h_hdis
            ]),
            labels=[*self._data]
        )

        # widgets - connect
        self._b_xslider.on_changed(self._call_xslider)
        self._b_yslider.on_changed(self._call_yslider)
        self._b_slider_uxx.on_changed(self._call_u_xx_change)
        self._b_slider_uyy.on_changed(self._call_u_yy_change)
        self._b_slider_uxy.on_changed(self._call_u_xy_change)
        self._b_reset.on_clicked(self._call_reset)
        self._b_zero.on_clicked(self._call_radio)
        self._b_name.on_clicked(self._call_name)
        self._plot_bands()

    def _call_close_main(self, event):
        self._fig = None

    def _call_close_bands(self, event):
        self._fig = None
        self._ax_bands = None
        self._line_bands = None

    def _call_xslider(self, val):
        self._x_range = self._b_xslider.val
        self._plot_bands()

    def _call_yslider(self, val):
        self._y_range = self._b_yslider.val
        self._plot_bands()

    def _call_u_xx_change(self, val):
        if not self._b_slider_uxx.val == self._u[0]:
            self._u[0] = self._b_slider_uxx.val
            if self._biaxial:
                self._u[1] = self._u[0]
                self._b_slider_uyy.set_val(self._u[1])
            self._plot_bands()

    def _call_u_yy_change(self, val):
        if not self._b_slider_uyy.val == self._u[1]:
            self._u[1] = self._b_slider_uyy.val
            if self._biaxial:
                self._u[0] = self._u[1]
                self._b_slider_uxx.set_val(self._u[0])
            self._plot_bands()

    def _call_u_xy_change(self, val):
        self._u[2] = self._b_slider_uxy.val
        self._plot_bands()

    def _call_reset(self, event):
        self._b_slider_uxx.reset()
        self._b_slider_uyy.reset()
        self._b_slider_uxy.reset()
        self._u = np.array([0., 0., 0.])
        self._b_xslider.reset()
        self._b_yslider.reset()
        self._plot_bands()

    def _call_name(self, name):
        self._name = name
        self._k_path = self._k_path_as_1d(self._data[self._name]["k_path"])
        self._k_path_points = self._k_path[self._data[self._name]["k_path_point_indices"]]
        self._plot_bands()

    def _call_radio(self, label):
        self._zero = self._b_zero.get_status()[0]
        self._biaxial = self._b_zero.get_status()[1]
        if self._biaxial:
            self._u[1] = self._u[0]
            self._b_slider_uyy.set_val(self._u[1])
        self._plot_bands()

    def _plot_bands(self):
        self._ax_bands.cla()
        idx = self._find_nearest(self._u)
        u_loc = self._data[self._name]["u"][idx]
        self._ax_bands.set_title(
            r"{0}: $u_{{xx}}$={1:.3f}, $u_{{yy}}$={2:.3f}, $u_{{xy}}$={3:.3f}".format(self._name, *u_loc))

        if self._zero:
            self._line_bands_zero = self._ax_bands.plot(
                self._k_path,
                self._data[self._name]["energy"][self._find_nearest(np.array([0., 0., 0.]))],
                color="C1", ls=":"
            )

        self._line_bands = self._ax_bands.plot(
            self._k_path,
            self._data[self._name]["energy"][idx],
            color="C0"
        )
        if self._zero:
            self._ax_bands.legend([self._line_bands[0], self._line_bands_zero[0]], ["strain", "no strain"])
        else:
            self._ax_bands.legend([self._line_bands[0]], ["strain"])
        for k_index in self._k_path_points:
            self._ax_bands.axvline(k_index, color="black", ls=":")
        self._ax_bands.set_xticks(self._k_path_points,
                                  [r"$\Gamma$", r"$M_1$", r"$K_1$", r"$\Gamma$", r"$K_2$", r"$M_2$", r"$\Gamma$"])
        self._ax_bands.set_ylabel("E (eV)")
        self._ax_bands.set_xlim(self._k_path[int(np.min((self._x_range[0], len(self._k_path) - 1)))],
                                self._k_path[int(np.min((self._x_range[1], len(self._k_path) - 1)))])
        self._ax_bands.set_ylim(*self._y_range)
        plt.show()

    def _find_nearest(self, u):
        return np.sum((self._data[self._name]["u"] - np.array(u)) ** 2, axis=1).argmin()

    @staticmethod
    def _k_path_as_1d(k_path):
        """ Return a 1D respresentation of the Path"""
        return np.append([0], np.sqrt((np.diff(k_path, axis=0) ** 2).dot([[1]] * len(k_path[0]))).cumsum())


def run_script():
    data = cloudpickle.load(urlopen(Request("http://nc.tfm.uantwerpen.be/s/HJRpRTTssAKM67P/download/bands.pickle")))
    return TmdPresentation(data)


if __name__ == "__main__":
    a = run_script()
