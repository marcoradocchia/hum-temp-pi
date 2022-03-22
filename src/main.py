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

from Adafruit_DHT import DHT22, read_retry
from argparse import ArgumentParser
from datetime import datetime
from os.path import expanduser, isdir, join
from os import mkdir
from sys import exit
from time import sleep, time

MIN_INTERVAL = 2
OUTPUT_DIRECTORY = expanduser("~/datalogger")


def read_temp_hum(pin: int) -> str:
    humidity, temperature = read_retry(DHT22, pin)
    if humidity is not None and temperature is not None:
        return humidity, temperature
    # wait 2 seconds and try a recursive call
    sleep(1)
    read_temp_hum()


def measure(measures: int, quiet: bool, pin: int, id: str) -> None:
    # average of humidity and temperature on "measures" number of measures
    # time is stored at the central measure
    humidity = 0
    temperature = 0
    for i in range(measures):
        hum_read, temp_read = read_temp_hum(pin=pin)
        if i == int(measures / 2):
            date, time = str(datetime.now()).split(".")[0].split(" ")
        temperature += temp_read
        humidity += hum_read
    temperature = round(temperature / measures, 1)
    humidity = round(humidity / measures, 1)
    if not quiet:
        print(
            f"date: {date}; "
            f"time:{time}; "
            f"temperature(celsius): {temperature}; "
            f"humidity(%): {humidity}"
        )
    with open(join(OUTPUT_DIRECTORY, f"{date}-{id}"), "a+") as data_file:
        data_file.write(f"{date},{time},{temperature},{humidity}\n")


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
    argparser.add_argument(
        "-p",
        "--pin",
        required=True,
        type=int,
        metavar=("<pin>"),
        help="GPIO pin",
    )
    argparser.add_argument(
        "-id",
        "--identifier",
        required=True,
        type=str,
        metavar=("<id>"),
        help="filename identifier",
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
            time_start = time()
            measure(
                measures=args.measures,
                quiet=args.quiet,
                pin=args.pin,
                id=args.identifier,
            )
            elapsed_time = time() - time_start
            sleep(args.interval - elapsed_time)
        except KeyboardInterrupt:
            exit()


if __name__ == "__main__":
    main()
