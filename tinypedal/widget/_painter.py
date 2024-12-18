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
Overlay base painter class.
"""

from __future__ import annotations

from PySide2.QtCore import Qt, QRectF
from PySide2.QtGui import QPainter, QPen
from PySide2.QtWidgets import QWidget

from ..formatter import select_gear


class WheelGaugeBar(QWidget):
    """Wheel gauge bar"""

    def __init__(
        self,
        padding_x: int,
        bar_width: int,
        bar_height: int,
        font_offset: int = 0,
        max_range: int = 100,
        input_color: str = "",
        fg_color: str = "",
        bg_color: str = "",
        right_side: bool = False,
    ):
        super().__init__()
        self.last = 0
        self.max_range = max_range
        self.width_scale = bar_width / self.max_range
        self.input_color = input_color
        self.bg_color = bg_color
        self.rect_bg = QRectF(0, 0, bar_width, bar_height)
        self.rect_input = self.rect_bg.adjusted(0,0,0,0)
        self.rect_text = self.rect_bg.adjusted(padding_x, font_offset, -padding_x, 0)

        if right_side:
            self.update_input = self.__update_right
            self.align = Qt.AlignRight | Qt.AlignVCenter
        else:
            self.update_input = self.__update_left
            self.align = Qt.AlignLeft | Qt.AlignVCenter

        self.pen = QPen()
        self.pen.setColor(fg_color)
        self.setFixedSize(bar_width, bar_height)

    def __update_left(self, input_value: float):
        """Update input value"""
        self.rect_input.setX((self.max_range - input_value) * self.width_scale)
        self.update()

    def __update_right(self, input_value: float):
        """Update input value"""
        self.rect_input.setWidth(input_value * self.width_scale)
        self.update()

    def paintEvent(self, event):
        """Draw normal without warning or negative highlighting"""
        painter = QPainter(self)
        painter.fillRect(self.rect_bg, self.bg_color)
        painter.fillRect(self.rect_input, self.input_color)
        painter.setPen(self.pen)
        painter.drawText(self.rect_text, self.align, f"{self.last:.0f}")


class PedalInputBar(QWidget):
    """Pedal input bar"""

    def __init__(
        self,
        pedal_length: int,
        pedal_extend: int,
        pedal_size: tuple,
        raw_size: tuple,
        filtered_size: tuple,
        max_size: tuple,
        reading_size: tuple,
        fg_color: str = "",
        bg_color: str = "",
        input_color: str = "",
        ffb_color: str = "",
        show_reading: bool = False,
        horizontal_style: bool = False,
    ):
        super().__init__()
        self.last = None
        self.is_maxed = False
        self.show_reading = show_reading
        self.input_reading = 0.0
        self.pedal_length = pedal_length
        self.pedal_extend = pedal_extend
        self.input_color = input_color
        self.bg_color = bg_color
        self.rect_pedal = QRectF(*pedal_size)
        self.rect_raw = QRectF(*raw_size)
        self.rect_filtered = QRectF(*filtered_size)
        self.rect_text = QRectF(*reading_size)

        if ffb_color:
            self.rect_max = self.rect_pedal
            self.max_color = ffb_color
        else:
            self.rect_max = QRectF(*max_size)
            self.max_color = input_color

        if horizontal_style:
            self.update_input = self.__update_horizontal
        else:
            self.update_input = self.__update_vertical

        self.pen = QPen()
        self.pen.setColor(fg_color)
        self.setFixedSize(pedal_size[2], pedal_size[3])

    def __update_horizontal(self, input_raw: float, input_filtered: float):
        """Update input value - horizontal style"""
        self.input_reading = max(input_raw, input_filtered) * 100
        scaled_raw = self.__scale_horizontal(input_raw)
        scaled_filtered = self.__scale_horizontal(input_filtered)
        self.rect_raw.setRight(scaled_raw)
        self.rect_filtered.setRight(scaled_filtered)
        self.is_maxed = scaled_raw >= self.pedal_length
        self.update()

    def __update_vertical(self, input_raw: float, input_filtered: float):
        """Update input value - vertical style"""
        self.input_reading = max(input_raw, input_filtered) * 100
        scaled_raw = self.__scale_vertical(input_raw)
        scaled_filtered = self.__scale_vertical(input_filtered)
        self.rect_raw.setTop(scaled_raw)
        self.rect_filtered.setTop(scaled_filtered)
        self.is_maxed = scaled_raw <= self.pedal_extend
        self.update()

    def __scale_horizontal(self, input_value: float) -> float:
        """Scale input - horizontal style"""
        return input_value * self.pedal_length

    def __scale_vertical(self, input_value: float) -> float:
        """Scale input - vertical style"""
        return (1 - input_value) * self.pedal_length + self.pedal_extend

    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.fillRect(self.rect_pedal, self.bg_color)
        painter.fillRect(self.rect_raw, self.input_color)
        painter.fillRect(self.rect_filtered, self.input_color)
        if self.is_maxed:
            painter.fillRect(self.rect_max, self.max_color)
        if self.show_reading:
            painter.setPen(self.pen)
            painter.drawText(self.rect_text, Qt.AlignCenter, f"{self.input_reading:.0f}")


class ProgressBar(QWidget):
    """Progress bar"""

    def __init__(
        self,
        width: int,
        height: int,
        input_color: str = "",
        bg_color: str = "",
        right_side: bool = False,
    ):
        super().__init__()
        self.last = -1
        self.bar_width = width
        self.rect_bar = QRectF(0, 0, width, height)
        self.rect_input = QRectF(0, 0, width, height)
        self.input_color = input_color
        self.bg_color = bg_color

        if right_side:
            self.update_input = self.__update_right
        else:
            self.update_input = self.__update_left

        self.setFixedSize(width, height)

    def __update_left(self, input_value: float):
        """Update input"""
        self.rect_input.setRight(input_value * self.bar_width)
        self.update()

    def __update_right(self, input_value: float):
        """Update input"""
        self.rect_input.setLeft(self.bar_width - input_value * self.bar_width)
        self.update()

    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.fillRect(self.rect_bar, self.bg_color)
        painter.fillRect(self.rect_input, self.input_color)


class FuelLevelBar(QWidget):
    """Fuel level bar"""

    def __init__(
        self,
        width: int,
        height: int,
        start_mark_width: int,
        refill_mark_width: int,
        input_color: str = "",
        bg_color: str = "",
        start_mark_color: str = "",
        refill_mark_color: str = "",
        show_start_mark: bool = True,
        show_refill_mark: bool = True,
    ):
        super().__init__()
        self.last = None
        self.bar_width = width
        self.rect_bar = QRectF(0, 0, width, height)
        self.rect_input = QRectF(0, 0, width, height)
        self.rect_start = QRectF(0, 0, start_mark_width, height)
        self.rect_refuel = QRectF(0, 0, refill_mark_width, height)
        self.input_color = input_color
        self.bg_color = bg_color
        self.start_mark_color = start_mark_color
        self.refill_mark_color = refill_mark_color
        self.show_start_mark = show_start_mark
        self.show_refill_mark = show_refill_mark
        self.setFixedSize(width, height)

    def update_input(self, input_value: float, start_value: float, refill_value: float):
        """Update input"""
        self.rect_input.setRight(input_value * self.bar_width)
        self.rect_start.moveLeft(start_value * self.bar_width)
        self.rect_refuel.moveLeft(refill_value * self.bar_width)
        self.update()

    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.fillRect(self.rect_bar, self.bg_color)
        painter.fillRect(self.rect_input, self.input_color)
        if self.show_start_mark:
            painter.fillRect(self.rect_start, self.start_mark_color)
        if self.show_refill_mark:
            painter.fillRect(self.rect_refuel, self.refill_mark_color)


class GearGaugeBar(QWidget):
    """Gear gauge bar"""

    def __init__(
        self,
        width: int,
        height: int,
        font_speed,
        gear_size: tuple,
        speed_size: tuple,
        fg_color: str,
        bg_color: str,
        show_speed: bool = True,
    ):
        super().__init__()
        self.last = -1
        self.gear = 0
        self.speed = 0
        self.color_index = 0
        self.show_speed = show_speed
        self.font_speed = font_speed
        self.bg_color = bg_color
        self.rect_gear = QRectF(*gear_size)
        self.rect_speed = QRectF(*speed_size)
        self.rect_bar = QRectF(0, 0, width, height)

        self.pen = QPen()
        self.pen.setColor(fg_color)
        self.setFixedSize(width, height)

    def update_input(self, gear: int, speed: int, color_index: int, bg_color: str):
        """Update input"""
        self.gear = gear
        self.speed = speed
        self.color_index = color_index
        self.bg_color = bg_color
        self.update()

    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.fillRect(self.rect_bar, self.bg_color)
        if self.color_index == -4:  # flicker trigger
            return
        painter.setPen(self.pen)
        painter.drawText(self.rect_gear, Qt.AlignCenter, select_gear(self.gear))
        if self.show_speed:
            painter.setFont(self.font_speed)
            painter.drawText(self.rect_speed, Qt.AlignCenter, f"{self.speed:03.0f}")


class TextBar(QWidget):
    """Text bar"""

    def __init__(
        self,
        width: int,
        height: int,
        font_offset: int,
        fg_color: str,
        bg_color: str,
        text: str = "",
    ):
        super().__init__()
        self.last = -1
        self.text = text
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.rect_bar = QRectF(0, 0, width, height)
        self.rect_text = self.rect_bar.adjusted(0, font_offset, 0, 0)
        self.setFixedSize(width, height)

    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.fillRect(self.rect_bar, self.bg_color)
        pen = QPen()
        pen.setColor(self.fg_color)
        painter.setPen(pen)
        painter.drawText(self.rect_text, Qt.AlignCenter, self.text)
