#!/usr/bin/env python3
# -*- coding=utf-8 -*-

# hum-temp-pi: humidity and temperature datalogger using raspberry/arduino and
# DHT22 sensors
# Copyright (C) 2022  Marco Radocchia

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see
# https://www.gnu.org/licenses/gpl-3.0.html

# dependencies:
# - pip:
#   * adafruit-circuitpython-dht
# - libgpiod2

from adafruit_dht import DHT22
from argparse import ArgumentParser
from board import D4
from datetime import datetime
from os.path import expanduser, isdir, join
from os import mkdir
from sys import exit
from time import sleep

MIN_INTERVAL = 2
OUTPUT_DIRECTORY = expanduser("~/datalogger")

# you can pass DHT22 use_pulseio=False if you wouldn't like to use pulseio.
# This may be necessary on a Linux single board computer like the Raspberry Pi,
# but it will not work in CircuitPython.
# dhtDevice = DHT22(D4, use_pulseio=False)

# Initial the dht device, with data pin connected to:
dhtDevice = DHT22(D4)


def log(error: Exception) -> None:
    with open(join(OUTPUT_DIRECTORY, "datalogger.log"), "a+") as logfile:
        logfile.write(f"{error}\n")


def read_temp_hum(quiet: bool) -> str:
    try:
        # get temperature in degrees Celsius
        temperature = dhtDevice.temperature
        humidity = dhtDevice.humidity
    except RuntimeError as error:
        if not quiet:
            print(error)
        log(error)
        # TODO: try recursive call
        sleep(2)
        read_temp_hum(quiet=quiet)
    except Exception as error:
        if not quiet:
            print(error)
        # exiting program
        log(error)
        dhtDevice.exit()
        raise error
    sleep(2)
    return temperature, humidity


def measure(measures: int, quiet: bool) -> None:
    # average of humidity and temperature on "measures" number of measures
    # time is stored at the central measure
    humidity = 0
    temperature = 0
    for i in range(measures):
        temp_read, hum_read = read_temp_hum(quiet=quiet)
        if i == int(measures / 2):
            date, time = str(datetime.now()).split(".")[0].split(" ")
        temperature += temp_read
        humidity += hum_read
    temperature = round(temperature / measures, 1)
    humidity = round(humidity / measures, 1)
    string = f"{date},{time},{temperature},{humidity}\n"
    if not quiet:
        print(string)
    with open(join(OUTPUT_DIRECTORY, date), "a+") as data_file:
        data_file.write(string)


def main() -> None:
    argparser = ArgumentParser(allow_abbrev=False)
    argparser.add_argument(
        "-i",
        "--interval",
        required=True,
        type=int,
        metavar=("<sec>"),
        help=f"interval between two reads (> {MIN_INTERVAL})",
    )
    argparser.add_argument(
        "-m",
        "--measures",
        type=int,
        metavar=("<num>"),
        default=11,
        help="number of measures to average the value (default: 11)",
    )
    argparser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="suppresses terminal output (for use in scripts)",
    )
    args = argparser.parse_args()
    if args.interval is not None and args.interval <= MIN_INTERVAL:
        exit(f"ERROR: Interval must be grater than {MIN_INTERVAL}")
    if args.measures % 2 == 0:
        exit("WARNING: Please insert odd integer")
    if args.measures * MIN_INTERVAL >= args.interval:
        exit("Incompatible parameters")
    # check if ~/datalogger directory exists, if not create it
    if not isdir(OUTPUT_DIRECTORY):
        mkdir(OUTPUT_DIRECTORY)
    # main loop
    while True:
        try:
            measure(measures=args.measures, quiet=args.quiet)
            sleep(args.interval)
        except KeyboardInterrupt:
            exit()


if __name__ == "__main__":
    main()
