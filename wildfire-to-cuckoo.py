#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Downloads a sample from Palo Alto Network's Wildfire service and sends it to
Cuckoo. Requires pyldfire - https://github.com/seanthegeek/pyldfire"""

from builtins import input
from argparse import ArgumentParser
from io import BytesIO
from distutils.util import strtobool
from time import sleep

from pyldfire import WildFire
from cuckoo import Cuckoo

__version__ = "1.0.1"
__license__ = """Copyright 2016 Sean Whalen

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License."""

wildfire = WildFire("api-key-goes-here")
cuckoo = Cuckoo("https://cuckoo.example.net/", "username", "password")

parser = ArgumentParser(description=__doc__, version=__version__)
parser.add_argument("hash", help="A MD5, SHA1, or SHA256 hash of a sample")
parser.add_argument("filename", nargs="?", help="The filename of the sample")
parser.add_argument("--tags",
                    help="Comma separated tags for selecting an analysis VM",
                    default=None)
parser.add_argument("--options",
                    help="Comma separated option=value pairs",
                    default=None)
parser.add_argument("--tor", action="store_true",
                     help="Enable Tor during analysis")
parser.add_argument("--procmemdump", action="store_true",
                    help="Dump and analyze process memory")
args = parser.parse_args()

options = {}

if args.tor:
    options['tor'] = 'yes'
if args.procmemdump:
    options['procmemdump'] = 'yes'

options = ",".join(list(map(lambda option: "{0}={1}".format(option, options[option]), options.keys())))

if args.options:
    if len(options) > 0:
        options += ","
    options += args.options

existing_tasks = cuckoo.find_tasks(args.hash)
if len(existing_tasks) > 0:
    print("The following analysis reports already exist for this sample:")
    for task_id in existing_tasks:
        print("{0}/analysis/{1}".format(cuckoo.root, task_id))
    try:
        resubmit = strtobool(input("Would you like to resubmit it? (/y/N)").lower())
    except ValueError:
        exit()
    if not resubmit:
        exit()

temp_file = BytesIO(wildfire.get_sample(args.hash))
results = cuckoo.submit_file((args.filename or args.hash),
                             temp_file.getvalue(),
                             tags=args.tags,
                             options=",".join(options))
tasks = {}

for task_id in results:
    tasks[task_id] = dict(previous_state=None, current_state=None)

while (len(tasks)) > 0:
    for task_id in tasks.keys():
        tasks[task_id]['previous_state'] = tasks[task_id]['current_state']
        tasks[task_id]['current_state'] = cuckoo.get_task_status(task_id)
        if tasks[task_id]['current_state'] != tasks[task_id]['previous_state']:
            print("Task {0} is {1}".format(task_id,  tasks[task_id]['current_state']))
        if tasks[task_id]['current_state'] == "reported":
            print("{0}/analysis/{1}".format(cuckoo.root, task_id))
        if tasks[task_id]['current_state'] == "reported" or tasks[task_id]['current_state'].startswith("failed"):
            del tasks[task_id]
        sleep(1)
