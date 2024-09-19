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
Overlay Control
"""

import logging
import time
import threading

from PySide2.QtCore import QObject, Signal

from .setting import cfg
from .api_control import api

logger = logging.getLogger(__name__)


class StateTimer:
    """State timer"""

    def __init__(self, interval: float, last: float = 0) -> None:
        self._interval = interval
        self._last = last

    def timeout(self, now: float) -> bool:
        """Check time out"""
        if self._last > now:  # last time stamp correction
            self._last = now
        if now - self._last < self._interval:
            return False
        self._last = now
        return True

    def reset(self, now: float = 0) -> None:
        """Reset timer"""
        self._last = now

    def set_interval(self, interval: float) -> None:
        """Set timer interval"""
        self._interval = interval

    @property
    def interval(self) -> float:
        """Timer interval"""
        return self._interval

    @property
    def last(self) -> float:
        """Timer last time stamp"""
        return self._last


class OverlayState(QObject):
    """Set and update overlay global state

    Signals:
        * hidden: auto hide
        * locked: overlay lock
        * reload: reload preset, should only be emitted after app fully loaded

    States:
        * Active: True if vehicle is on track
        * Lock position
        * Auto hide
        * Grid move
    """
    hidden = Signal(bool)
    locked = Signal(bool)
    reload = Signal(bool)

    def __init__(self):
        super().__init__()
        self.stopped = True
        self.active = False
        self.event = threading.Event()

        self._auto_hide_timer = StateTimer(interval=0.4)
        self._auto_load_preset_timer = StateTimer(interval=1.0)

    def start(self):
        """Start state update thread"""
        if self.stopped:
            self.stopped = False
            self.event.clear()
            threading.Thread(target=self.__updating, daemon=True).start()
            logger.info("ACTIVE: overlay control")

    def stop(self):
        """Stop thread"""
        self.event.set()

    def __updating(self):
        """Update global state"""
        while not self.event.wait(0.01):
            self.active = api.state
            self.__auto_hide_state()
            if cfg.application["enable_auto_load_preset"]:
                self.__auto_load_preset()

        self.stopped = True
        logger.info("CLOSED: overlay control")

    def __auto_hide_state(self):
        """Auto hide state"""
        if self._auto_hide_timer.timeout(time.perf_counter()):
            self.hidden.emit(cfg.overlay["auto_hide"] and not self.active)

    def __auto_load_preset(self):
        """Auto load primary preset"""
        if self._auto_load_preset_timer.timeout(time.perf_counter()):
            # Make sure app is fully loaded before check state
            if not cfg.app_loaded:
                return
            # Get sim_name, returns "" if no game running
            sim_name = api.read.check.sim_name()
            # Abort if game not found
            if not sim_name:
                # Clear detected name if no game found
                if cfg.last_detected_sim is not None:
                    cfg.last_detected_sim = None
                return
            # Abort if same as last found game
            if sim_name == cfg.last_detected_sim:
                return
            # Assign sim name to last detected, set preset name
            cfg.last_detected_sim = sim_name
            preset_name = cfg.get_primary_preset_name(sim_name)
            logger.info("SETTING: game detected: %s", sim_name)
            # Abort if preset file does not exist
            if preset_name == "":
                logger.info("SETTING: not found, abort auto loading")
                return
            # Check if already loaded
            if preset_name == cfg.filename.last_setting:
                logger.info("SETTING: %s already loaded", preset_name)
                return
            # Update preset name
            cfg.filename.setting = preset_name
            # Do not call cfg.load here as it's handled by loader.reload
            self.reload.emit(True)


class OverlayControl:
    """Overlay control"""

    def __init__(self):
        self.state = OverlayState()

    def enable(self):
        """Enable overlay control"""
        self.state.start()

    def disable(self):
        """Disable overlay control"""
        self.state.stop()
        while not self.state.stopped:
            time.sleep(0.01)

    def toggle_lock(self):
        """Toggle lock state"""
        self.__toggle_option("fixed_position")
        self.state.locked.emit(cfg.overlay["fixed_position"])

    def toggle_hide(self):
        """Toggle hide state"""
        self.__toggle_option("auto_hide")

    def toggle_grid(self):
        """Toggle grid move state"""
        self.__toggle_option("enable_grid_move")

    @staticmethod
    def __toggle_option(option_name: str):
        """Toggle option"""
        cfg.overlay[option_name] = not cfg.overlay[option_name]
        cfg.save()

octrl = OverlayControl()
