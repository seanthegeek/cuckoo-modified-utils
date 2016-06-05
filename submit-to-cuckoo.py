#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Submits files or a URL to Cuckoo

Copyright 2016 Sean Whalen

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from builtins import input
from argparse import ArgumentParser
from distutils.util import strtobool
from io import BytesIO
from time import sleep
from glob import glob
from zipfile import ZipFile
from os.path import basename

from cuckoo import Cuckoo, get_file_hash

__version__ = "1.0.0"

cuckoo = Cuckoo("https://cuckoo.example.net", "username", "password")

parser = ArgumentParser(description=__doc__)
parser.add_argument("sample", nargs="+", help="One or more filenames or globs, or a single URL")
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

url = len(args.sample) == 1 and args.sample[0].lower().startswith("http")
if url:
    url = args.sample[0]
    results = cuckoo.submit_url(url, tags=args.tags, options=options)
else:
    filenames = []

    for filename in args.sample:
        filenames += glob(filename)

    if len(filenames) == 0:
        raise ValueError("No matching files found")
    elif len(filenames) > 1:
        multi_file = True
    else:
        multi_file = False

    if multi_file:
        temp_file = BytesIO()
        temp_filename = "bulk.zip"
        with ZipFile(temp_file, 'a') as temp_zip:
            temp_zip.setpassword("infected")
            for filename in filenames:
                temp_zip.write(filename)
    else:
        temp_filename = basename(filenames[0])
        with open(temp_filename, 'rb') as sample_file:
            temp_file = BytesIO(sample_file.read())
        file_hash = get_file_hash(temp_file)
        existing_tasks = cuckoo.find_tasks(file_hash)
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

    results = cuckoo.submit_file(temp_filename, temp_file.getvalue(), tags=args.tags, options=options)

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