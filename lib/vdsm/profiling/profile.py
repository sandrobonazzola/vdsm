#
# Copyright 2014 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#
# Refer to the README and COPYING files for full details of the license
#

from __future__ import absolute_import
"""
profiling facade.
"""

from . import cpu
from . import memory


def start():
    cpu.start()
    memory.start()


def stop():
    cpu.stop()
    memory.stop()


def status():
    res = {}
    for profiler in (cpu, memory):
        res[profiler.__name__] = {
            "enabled": profiler.is_enabled(),
            "running": profiler.is_running()
        }
    return res
