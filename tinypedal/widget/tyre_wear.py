#  TinyPedal is an open-source overlay application for racing simulation.
#  Copyright (C) 2022-2024 TinyPedal developers, see contributors.md file
#
#  This file is part of TinyPedal.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Tyre Wear Widget
"""

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QGridLayout

from .. import calculation as calc
from ..api_control import api
from ..module_info import minfo
from ._base import Overlay

WIDGET_NAME = "tyre_wear"


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config):
        # Assign base setting
        Overlay.__init__(self, config, WIDGET_NAME)

        # Config font
        font_m = self.get_font_metrics(
            self.config_font(self.wcfg["font_name"], self.wcfg["font_size"]))

        # Config variable
        text_def = "n/a"
        bar_padx = round(self.wcfg["font_size"] * self.wcfg["bar_padding"]) * 2
        bar_gap = self.wcfg["bar_gap"]
        bar_width = font_m.width * 4 + bar_padx
        self.freeze_duration = min(max(self.wcfg["freeze_duration"], 0), 30)

        # Base style
        self.setStyleSheet(
            f"font-family: {self.wcfg['font_name']};"
            f"font-size: {self.wcfg['font_size']}px;"
            f"font-weight: {self.wcfg['font_weight']};"
        )
        bar_style_desc = self.set_qss(
            fg_color=self.wcfg["font_color_caption"],
            bg_color=self.wcfg["bkg_color_caption"],
            font_size=int(self.wcfg['font_size'] * 0.8)
        )

        # Create layout
        layout = QGridLayout()
        layout.setContentsMargins(0,0,0,0)  # remove border
        layout.setSpacing(bar_gap)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setLayout(layout)

        # Remaining tyre wear
        if self.wcfg["show_remaining"]:
            layout_twear = QGridLayout()
            layout_twear.setSpacing(0)
            self.bar_style_twear = (
                self.set_qss(
                    self.wcfg["font_color_remaining"],
                    self.wcfg["bkg_color_remaining"]),
                self.set_qss(
                    self.wcfg["font_color_warning"],
                    self.wcfg["bkg_color_remaining"])
            )
            self.bar_twear = self.set_qlabel(
                text=text_def,
                style=self.bar_style_twear[0],
                width=bar_width,
                count=4,
            )
            self.set_layout_quad(layout_twear, self.bar_twear)

            if self.wcfg["show_caption"]:
                cap_twear = self.set_qlabel(
                    text="tyre wear",
                    style=bar_style_desc,
                )
                layout_twear.addWidget(cap_twear, 0, 0, 1, 0)

            self.set_layout_orient(
                layout, layout_twear, self.wcfg["column_index_remaining"])

        # Tyre wear difference
        if self.wcfg["show_wear_difference"]:
            layout_tdiff = QGridLayout()
            layout_tdiff.setSpacing(0)
            self.bar_style_tdiff = (
                self.set_qss(
                    self.wcfg["font_color_wear_difference"],
                    self.wcfg["bkg_color_wear_difference"]),
                self.set_qss(
                    self.wcfg["font_color_warning"],
                    self.wcfg["bkg_color_wear_difference"])
            )
            self.bar_tdiff = self.set_qlabel(
                text=text_def,
                style=self.bar_style_tdiff[0],
                width=bar_width,
                count=4,
            )
            self.set_layout_quad(layout_tdiff, self.bar_tdiff)

            if self.wcfg["show_caption"]:
                cap_tdiff = self.set_qlabel(
                    text="tyre diff",
                    style=bar_style_desc,
                )
                layout_tdiff.addWidget(cap_tdiff, 0, 0, 1, 0)

            self.set_layout_orient(
                layout, layout_tdiff, self.wcfg["column_index_wear_difference"])

        # Estimated tyre lifespan in laps
        if self.wcfg["show_lifespan_laps"]:
            layout_tlaps = QGridLayout()
            layout_tlaps.setSpacing(0)
            self.bar_style_tlaps = (
                self.set_qss(
                    self.wcfg["font_color_lifespan_laps"],
                    self.wcfg["bkg_color_lifespan_laps"]),
                self.set_qss(
                    self.wcfg["font_color_warning"],
                    self.wcfg["bkg_color_lifespan_laps"])
            )
            self.bar_tlaps = self.set_qlabel(
                text=text_def,
                style=self.bar_style_tlaps[0],
                width=bar_width,
                count=4,
            )
            self.set_layout_quad(layout_tlaps, self.bar_tlaps)

            if self.wcfg["show_caption"]:
                cap_tlaps = self.set_qlabel(
                    text="est. laps",
                    style=bar_style_desc,
                )
                layout_tlaps.addWidget(cap_tlaps, 0, 0, 1, 0)

            self.set_layout_orient(
                layout, layout_tlaps, self.wcfg["column_index_lifespan_laps"])

        # Estimated tyre lifespan in minutes
        if self.wcfg["show_lifespan_minutes"]:
            layout_tmins = QGridLayout()
            layout_tmins.setSpacing(0)
            self.bar_style_tmins = (
                self.set_qss(
                    self.wcfg["font_color_lifespan_minutes"],
                    self.wcfg["bkg_color_lifespan_minutes"]),
                self.set_qss(
                    self.wcfg["font_color_warning"],
                    self.wcfg["bkg_color_lifespan_minutes"])
            )
            self.bar_tmins = self.set_qlabel(
                text=text_def,
                style=self.bar_style_tmins[0],
                width=bar_width,
                count=4,
            )
            self.set_layout_quad(layout_tmins, self.bar_tmins)

            if self.wcfg["show_caption"]:
                cap_tmins = self.set_qlabel(
                    text="est. mins",
                    style=bar_style_desc,
                )
                layout_tmins.addWidget(cap_tmins, 0, 0, 1, 0)

            self.set_layout_orient(
                layout, layout_tmins, self.wcfg["column_index_lifespan_minutes"])

        # Last data
        self.checked = False
        self.last_lap_stime = 0        # last lap start time
        self.wear_prev = [0,0,0,0]     # previous moment remaining tyre wear
        self.wear_curr_lap = [0,0,0,0]  # live tyre wear update of current lap
        self.wear_last_lap = [0,0,0,0]  # total tyre wear of last lap

        self.last_wear_curr_lap = [None] * 4
        self.last_wear_last_lap = [None] * 4
        self.last_wear_laps = [None] * 4
        self.last_wear_mins = [None] * 4

    def timerEvent(self, event):
        """Update when vehicle on track"""
        if self.state.active:

            # Reset switch
            if not self.checked:
                self.checked = True

            # Read tyre wear data
            lap_stime = api.read.timing.start()
            lap_etime = api.read.timing.elapsed()
            wear_curr = tuple(map(self.round2decimal, api.read.tyre.wear()))

            if lap_stime != self.last_lap_stime:
                self.wear_last_lap = self.wear_curr_lap
                self.wear_curr_lap = [0,0,0,0]  # reset real time wear
                self.last_lap_stime = lap_stime  # reset time stamp counter

            for idx in range(4):
                # Remaining tyre wear
                if self.wcfg["show_remaining"]:
                    self.update_wear(self.bar_twear[idx], wear_curr[idx], self.wear_prev[idx])

                # Update tyre wear differences
                self.wear_prev[idx], self.wear_curr_lap[idx] = calc.tyre_wear_difference(
                    wear_curr[idx], self.wear_prev[idx], self.wear_curr_lap[idx])

                # Tyre wear differences
                if self.wcfg["show_wear_difference"]:
                    if (self.wcfg["show_live_wear_difference"] and
                        lap_etime - lap_stime > self.freeze_duration):
                        self.update_diff(
                            self.bar_tdiff[idx], self.wear_curr_lap[idx],
                            self.last_wear_curr_lap[idx])
                        self.last_wear_curr_lap[idx] = self.wear_curr_lap[idx]
                    else:  # Last lap diff
                        self.update_diff(
                            self.bar_tdiff[idx], self.wear_last_lap[idx],
                            self.last_wear_last_lap[idx])
                        self.last_wear_last_lap[idx] = self.wear_last_lap[idx]

                # Estimated tyre lifespan in laps
                if self.wcfg["show_lifespan_laps"]:
                    wear_laps = calc.tyre_lifespan_in_laps(
                        wear_curr[idx], self.wear_last_lap[idx], self.wear_curr_lap[idx])
                    self.update_laps(self.bar_tlaps[idx], wear_laps, self.last_wear_laps[idx])
                    self.last_wear_laps[idx] = wear_laps

                # Estimated tyre lifespan in minutes
                if self.wcfg["show_lifespan_minutes"]:
                    wear_mins = calc.tyre_lifespan_in_mins(
                        wear_curr[idx], self.wear_last_lap[idx], self.wear_curr_lap[idx],
                        minfo.delta.lapTimePace)
                    self.update_mins(self.bar_tmins[idx], wear_mins, self.last_wear_mins[idx])
                    self.last_wear_mins[idx] = wear_mins

        else:
            if self.checked:
                self.checked = False
                self.wear_prev = [0,0,0,0]
                self.wear_curr_lap = [0,0,0,0]
                self.wear_last_lap = [0,0,0,0]

    # GUI update methods
    def update_wear(self, target_bar, curr, last):
        """Remaining tyre wear"""
        if curr != last:
            target_bar.setText(self.format_num(curr))
            target_bar.setStyleSheet(
                self.bar_style_twear[curr <= self.wcfg["warning_threshold_remaining"]]
            )

    def update_diff(self, target_bar, curr, last):
        """Tyre wear differences"""
        if curr != last:
            target_bar.setText(self.format_num(curr))
            target_bar.setStyleSheet(
                self.bar_style_tdiff[curr > self.wcfg["warning_threshold_wear"]]
            )

    def update_laps(self, target_bar, curr, last):
        """Estimated tyre lifespan in laps"""
        if curr != last:
            target_bar.setText(self.format_num(curr))
            target_bar.setStyleSheet(
                self.bar_style_tlaps[curr <= self.wcfg["warning_threshold_laps"]]
            )

    def update_mins(self, target_bar, curr, last):
        """Estimated tyre lifespan in minutes"""
        if curr != last:
            target_bar.setText(self.format_num(curr))
            target_bar.setStyleSheet(
                self.bar_style_tmins[curr <= self.wcfg["warning_threshold_minutes"]]
            )

    # GUI generate methods
    @staticmethod
    def set_layout_quad(layout, bar_set, row_start=1, column_left=0, column_right=9):
        """Set layout - quad

        Default row index start from 1; reserve row index 0 for caption.
        """
        for idx in range(4):
            layout.addWidget(bar_set[idx], row_start + (idx > 1),
                column_left + (idx % 2) * column_right)

    # Additional methods
    @staticmethod
    def round2decimal(value):
        """Round 2 decimal"""
        return round(value * 100, 2)

    @staticmethod
    def format_num(value):
        """Format number"""
        return f"{value:.2f}"[:4].strip(".")
