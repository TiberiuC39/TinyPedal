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
Track map Widget
"""

from PySide2.QtCore import Qt, QRectF
from PySide2.QtGui import QPainterPath, QPainter, QPixmap, QPen, QBrush

from .. import calculation as calc
from ..module_info import minfo
from ._base import Overlay

WIDGET_NAME = "track_map"


class Realtime(Overlay):
    """Draw widget"""

    def __init__(self, config):
        # Assign base setting
        Overlay.__init__(self, config, WIDGET_NAME)

        # Config font
        self.font = self.config_font(
            self.wcfg["font_name"],
            self.wcfg["font_size"],
            self.wcfg["font_weight"]
        )
        font_m = self.get_font_metrics(self.font)
        font_offset = self.calc_font_offset(font_m)

        # Config variable
        self.display_detail_level = max(self.wcfg["display_detail_level"], 0)
        self.veh_size = self.wcfg["font_size"] + round(font_m.width * self.wcfg["bar_padding"])
        self.veh_shape = QRectF(
            self.veh_size * 0.5,
            self.veh_size * 0.5,
            self.veh_size,
            self.veh_size
        )
        self.veh_text_shape = QRectF(
            -self.veh_size * 0.5,
            -self.veh_size * 0.5 + font_offset,
            self.veh_size,
            self.veh_size
        )

        # Config canvas
        self.area_size = max(self.wcfg["area_size"], 100)
        self.area_margin = min(max(self.wcfg["area_margin"], 0), int(self.area_size/4))
        self.temp_map_size = self.area_size - self.area_margin * 2

        self.resize(self.area_size, self.area_size)
        self.pixmap_map = QPixmap(self.area_size, self.area_size)

        self.pen = QPen()
        self.pen.setColor(self.wcfg["font_color"])

        self.pixmap_veh_player = self.draw_vehicle_pixmap("player")
        self.pixmap_veh_leader = self.draw_vehicle_pixmap("leader")
        self.pixmap_veh_in_pit = self.draw_vehicle_pixmap("in_pit")
        self.pixmap_veh_yellow = self.draw_vehicle_pixmap("yellow")
        self.pixmap_veh_laps_ahead = self.draw_vehicle_pixmap("laps_ahead")
        self.pixmap_veh_laps_behind = self.draw_vehicle_pixmap("laps_behind")
        self.pixmap_veh_same_lap = self.draw_vehicle_pixmap("same_lap")

        # Last data
        self.map_scaled = None
        self.map_range = (0,10,0,10)
        self.map_scale = 1
        self.map_offset = (0,0)

        self.last_coords_hash = -1
        self.last_veh_data_version = None
        self.circular_map = True

        self.update_map(0, 1)

    def timerEvent(self, event):
        """Update when vehicle on track"""
        if self.state.active:

            # Map
            coords_hash = minfo.mapping.coordinatesHash
            self.update_map(coords_hash, self.last_coords_hash)
            self.last_coords_hash = coords_hash

            # Vehicles
            veh_data_version = minfo.vehicles.dataSetVersion
            self.update_vehicle(veh_data_version, self.last_veh_data_version)
            self.last_veh_data_version = veh_data_version

    # GUI update methods
    def update_map(self, curr, last):
        """Map update"""
        if curr != last:
            map_path = self.create_map_path(minfo.mapping.coordinates)
            self.draw_map_image(map_path, self.circular_map)

    def update_vehicle(self, curr, last):
        """Vehicle & update"""
        if curr != last:
            self.update()

    def paintEvent(self, event):
        """Draw"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        # Draw map
        painter.drawPixmap(0, 0, self.pixmap_map)
        # Draw vehicles
        self.draw_vehicle(painter, minfo.vehicles.dataSet, minfo.vehicles.drawOrder)

    def create_map_path(self, raw_coords=None):
        """Create map path"""
        map_path = QPainterPath()
        if raw_coords:
            dist = calc.distance(raw_coords[0], raw_coords[-1])
            (self.map_scaled, self.map_range, self.map_scale, self.map_offset
             ) = calc.scale_map(raw_coords, self.area_size, self.area_margin)

            total_nodes = len(self.map_scaled)
            skip_node = total_nodes // (self.temp_map_size * 3) * self.display_detail_level
            skipped_last_node = (total_nodes - 1) % skip_node if skip_node else 0
            last_skip = 0
            for index, coords in enumerate(self.map_scaled):
                if index == 0:
                    map_path.moveTo(*coords)
                elif last_skip >= skip_node:
                    map_path.lineTo(*coords)
                    last_skip = 0
                last_skip += 1

            if skipped_last_node:  # set last node if skipped
                map_path.lineTo(*self.map_scaled[-1])

            # Close map loop if start & end distance less than 500 meters
            if dist < 500:
                map_path.closeSubpath()
                self.circular_map = True
            else:
                self.circular_map = False

        # Temp(circular) map
        else:
            temp_coords = (
                (self.area_margin, self.area_margin),
                (self.temp_map_size, self.area_margin),
                (self.temp_map_size, self.temp_map_size),
                (self.area_margin, self.temp_map_size)
            )
            (_, self.map_range, self.map_scale, self.map_offset
             ) = calc.scale_map(temp_coords, self.area_size, self.area_margin)

            self.map_scaled = None

            map_path.addEllipse(
                self.area_margin,
                self.area_margin,
                self.temp_map_size,
                self.temp_map_size,
            )
            self.circular_map = True
        return map_path

    def draw_map_image(self, map_path, circular_map=True):
        """Draw map image separately"""
        if self.wcfg["show_background"]:
            self.pixmap_map.fill(self.wcfg["bkg_color"])
        else:
            self.pixmap_map.fill(Qt.transparent)
        painter = QPainter(self.pixmap_map)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)

        # Draw map inner background
        if self.wcfg["show_map_background"] and circular_map:
            brush = QBrush(Qt.SolidPattern)
            brush.setColor(self.wcfg["bkg_color_map"])
            painter.setBrush(brush)
            painter.drawPath(map_path)
            painter.setBrush(Qt.NoBrush)

        # Set pen style
        pen = QPen()
        pen.setJoinStyle(Qt.RoundJoin)

        # Draw map outline
        if self.wcfg["map_outline_width"] > 0:
            pen.setWidth(self.wcfg["map_width"] + self.wcfg["map_outline_width"])
            pen.setColor(self.wcfg["map_outline_color"])
            painter.setPen(pen)
            painter.drawPath(map_path)

        # Draw map
        pen.setWidth(self.wcfg["map_width"])
        pen.setColor(self.wcfg["map_color"])
        painter.setPen(pen)
        painter.drawPath(map_path)

        # Draw sector
        if self.map_scaled:
            # SF line
            if self.wcfg["show_start_line"]:
                pen.setWidth(self.wcfg["start_line_width"])
                pen.setColor(self.wcfg["start_line_color"])
                painter.setPen(pen)
                pos_x1, pos_y1, pos_x2, pos_y2 = calc.line_intersect_coords(
                    self.map_scaled[0],  # point a
                    self.map_scaled[1],  # point b
                    1.57079633,  # 90 degree rotation
                    self.wcfg["start_line_length"]
                )
                painter.drawLine(pos_x1, pos_y1, pos_x2, pos_y2)

            # Sector lines
            sectors_index = minfo.mapping.sectors
            if self.wcfg["show_sector_line"] and sectors_index and all(sectors_index):
                pen.setWidth(self.wcfg["sector_line_width"])
                pen.setColor(self.wcfg["sector_line_color"])
                painter.setPen(pen)

                for idx in range(2):
                    pos_x1, pos_y1, pos_x2, pos_y2 = calc.line_intersect_coords(
                        self.map_scaled[sectors_index[idx]],  # point a
                        self.map_scaled[sectors_index[idx] + 1],  # point b
                        1.57079633,  # 90 degree rotation
                        self.wcfg["sector_line_length"]
                    )
                    painter.drawLine(pos_x1, pos_y1, pos_x2, pos_y2)
        else:
            # SF line
            if self.wcfg["show_start_line"]:
                pen.setWidth(self.wcfg["start_line_width"])
                pen.setColor(self.wcfg["start_line_color"])
                painter.setPen(pen)
                painter.drawLine(
                    self.area_margin - self.wcfg["start_line_length"],
                    self.area_size * 0.5,
                    self.area_margin + self.wcfg["start_line_length"],
                    self.area_size * 0.5
                )

    def draw_vehicle(self, painter, veh_info, veh_draw_order):
        """Draw vehicles"""
        if self.wcfg["show_vehicle_standings"]:
            painter.setFont(self.font)
            painter.setPen(self.pen)

        for index in veh_draw_order:
            if self.last_coords_hash:
                pos_x, pos_y = (  # position = (coords - min_range) * scale + offset
                    round((veh_info[index].posXY[0] - self.map_range[0])
                        * self.map_scale + self.map_offset[0]),  # min range x, offset x
                    round((veh_info[index].posXY[1] - self.map_range[2])
                        * self.map_scale + self.map_offset[1])  # min range y, offset y
                )  # round to prevent bouncing
                offset = 0
            else:  # vehicles on temp map
                inpit_offset = self.wcfg["font_size"] if veh_info[index].inPit else 0
                pos_x, pos_y = calc.rotate_coordinate(
                    6.2831853 * veh_info[index].lapProgress,
                    self.temp_map_size / -2 + inpit_offset,  # x pos
                    0)  # y pos
                offset = self.area_size * 0.5

            painter.translate(offset + pos_x, offset + pos_y)
            painter.drawPixmap(
                -self.veh_size, -self.veh_size,
                self.color_veh_pixmap(veh_info[index]))

            # Draw text standings
            if self.wcfg["show_vehicle_standings"]:
                painter.drawText(
                    self.veh_text_shape, Qt.AlignCenter,
                    f"{veh_info[index].positionOverall}")
            painter.resetTransform()

    def draw_vehicle_pixmap(self, suffix):
        """Draw vehicles pixmap"""
        pixmap_veh = QPixmap(self.veh_size * 2, self.veh_size * 2)
        pixmap_veh.fill(Qt.transparent)
        painter = QPainter(pixmap_veh)
        painter.setRenderHint(QPainter.Antialiasing, True)
        if self.wcfg["vehicle_outline_width"] > 0:
            pen = QPen()
            pen.setWidth(self.wcfg["vehicle_outline_width"])
            pen.setColor(self.wcfg["vehicle_outline_color"])
            painter.setPen(pen)
        else:
            painter.setPen(Qt.NoPen)
        brush = QBrush(Qt.SolidPattern)
        brush.setColor(self.wcfg[f"vehicle_color_{suffix}"])
        painter.setBrush(brush)
        painter.drawEllipse(self.veh_shape)
        return pixmap_veh

    # Additional methods
    def color_veh_pixmap(self, veh_info):
        """Compare lap differences & set color"""
        if veh_info.isPlayer:
            return self.pixmap_veh_player
        if veh_info.positionOverall == 1:
            return self.pixmap_veh_leader
        if veh_info.inPit:
            return self.pixmap_veh_in_pit
        if veh_info.isYellow and not veh_info.inPit:
            return self.pixmap_veh_yellow
        if veh_info.isLapped > 0:
            return self.pixmap_veh_laps_ahead
        if veh_info.isLapped < 0:
            return self.pixmap_veh_laps_behind
        return self.pixmap_veh_same_lap
