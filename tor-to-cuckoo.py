#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Downloads a file via Tor, through a privoxy chain, and sends it to Cuckoo"""
from builtins import input
from argparse import ArgumentParser
from distutils.util import strtobool
from io import BytesIO
from time import sleep

from requests import get

from cuckooutils import Cuckoo, get_file_hash

__version__ = "1.0.0"
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

cuckoo = Cuckoo("https://cuckoo.example.net", "username", "password")
default_user_agent = "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/4.0; InfoPath.2; " \
                     ".NET CLR 2.0.50727; WOW64)"

parser = ArgumentParser(description=__doc__, version=__version__)
parser.add_argument("URL", help="URL of the sample")
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
parser.add_argument("--user-agent", help="The user agent to spoof. Default: {0}".format(default_user_agent),
                    default=default_user_agent)

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

proxies = {"http": "http://localhost:8118",
           "https": "http://localhost:8118"}

headers = {"user-agent": args.user_agent}

options = ""
if args.tor:
    options += "tor=yes"
if not args.URL.lower().startswith("http"):
    args.URL = "http://{0}".format(args.URL)
filename = args.URL.split("/")[-1]
response = get(args.URL, headers=headers, proxies=proxies)
response.raise_for_status()
temp_file = BytesIO(response.content)
file_hash = get_file_hash(temp_file)
existing_tasks = cuckoo.find_tasks(file_hash)
if len(existing_tasks) > 0:
    print("The following analysis reports already exist for this sample:")
    for task_id in existing_tasks:
        print("{0}/analysis/{1}".format(cuckoo.root, task_id))
    try:
        resubmit = strtobool(input("Would you like to resubmit it? (y/N)").lower())
    except ValueError:
        exit()
    if not resubmit:
        exit()

results = cuckoo.submit_file(filename, temp_file.getvalue(), tags=args.tags, options=options)

tasks = {}

task_ids = results['task_ids']

for task_id in task_ids:
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