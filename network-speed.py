#!/usr/bin/env python3
# network-speed - Show overall network interface traffic
# Copyright 2025  Simon Arlott
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import math
import os
import time

class NetDevs(dict):
	def __init__(self):
		with open("/proc/net/dev", "rt") as f:
			(rxn, txn) = [x.strip() for x in f.readline().strip().split("|")[1:]]
			(rxh, txh) = [x.split() for x in f.readline().strip().split("|")[1:]]
			rxh = [(rxn, x) for x in rxh]
			txh = [(txn, x) for x in txh]
			header = rxh + txh
			for line in f:
				(ifname, stats) = line.strip().split(":")
				stats = dict(zip(header, [int(x) for x in stats.split()]))
				self[ifname] = stats

def format_bytes(value):
	units = ["B", "K", "M", "G", "T", "P", "E", "Z", "Y", "R", "Q"]

	while value >= 1000 and len(units) > 1:
		value /= 1024
		units = units[1:]

	return f"{value:7.3f}{units[0]}"

def format_packets(value):
	units = ["", "K", "M", "G", "T", "P", "E", "Z", "Y", "R", "Q"]

	if value < 100000:
		return f"{value:5.0f}"

	while value >= 10000 and len(units) > 1:
		value /= 1000
		units = units[1:]

	return f"{value:4.0f}{units[0]}"

def format_graph(value, width, limit, left):
	blocks = (min(value, limit) / limit) * width
	blocks = math.ceil(blocks * 2) / 2

	output = "█" * int(blocks)

	if blocks % 1 != 0:
		if left:
			output = "▐" + output
		else:
			output = output + "▌"

	if left:
		output = " " * (width - len(output)) + output
	else:
		output = output + " " * (width - len(output))

	return output

class NetworkSpeed:
	def __init__(self, interface, rx_speed, tx_speed):
		self.interface = interface
		self.rx_speed = rx_speed / 8
		self.tx_speed = tx_speed / 8
		self.width = 79

	def run(self, interval):
		last_ts = None
		last_stats = None
		while True:
			now = time.time()
			stats = NetDevs()[self.interface]

			if last_ts is not None:
				adjust = 1 / (now - last_ts)

				self.print(
					max(0, (stats[("Receive", "bytes")] - last_stats[("Receive", "bytes")])) * adjust,
					max(0, (stats[("Receive", "packets")] - last_stats[("Receive", "packets")])) * adjust,
					max(0, (stats[("Transmit", "bytes")] - last_stats[("Transmit", "bytes")])) * adjust,
					max(0, (stats[("Transmit", "packets")] - last_stats[("Transmit", "packets")])) * adjust,
				)
			else:
				self.print(
					max(0, stats[("Receive", "bytes")]),
					max(0, stats[("Receive", "packets")]),
					max(0, stats[("Transmit", "bytes")]),
					max(0, stats[("Transmit", "packets")]),
					True,
				)

			last_ts = now
			last_stats = stats
			wait_s = (now + 1) - time.time()
			if wait_s > 0:
				time.sleep(wait_s)

	def print(self, rx_bytes, rx_packets, tx_bytes, tx_packets, first=False):
		left = f"{format_packets(rx_packets):5} {format_bytes(rx_bytes):8} |"
		right = f"| {format_bytes(tx_bytes):8} {format_packets(tx_packets):5}"
		available = max(10, self.width - len(left) - len(right)) // 2
		left = left + "\x1B[32m" + format_graph(rx_bytes, available, self.rx_speed, True) + "\x1B[39m"
		right = "\x1B[31m" + format_graph(tx_bytes, available, self.tx_speed, False) + "\x1B[39m" + right
		if first:
			print(f"\x1B[4m{left}{right}\x1B[24m")
		else:
			print(f"{left}{right}")


if __name__ == "__main__":
	parser = argparse.ArgumentParser(prog="network-speed",
		description="Show overall network interface traffic")
	parser.add_argument("interface", type=str)
	parser.add_argument("rx_speed", type=float, metavar="RX_MEGABITS")
	parser.add_argument("tx_speed", type=float, metavar="TX_MEGABITS")
	args = parser.parse_args()

	NetworkSpeed(args.interface, args.rx_speed * 10**6, args.tx_speed * 10**6).run(1)

