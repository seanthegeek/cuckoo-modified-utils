# -*- coding: utf-8 -*-

"""A simple module for the API of the Brad Spengler fork of Cuckoo.

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

from hashlib import md5, sha1, sha256
from re import match
from requests import session
from io import BytesIO

__version__ = "1.0.1"

hash_types = {"md5": md5, "sha1": sha1, "sha256": sha256}
hash_regex = {r'[a-fA-F\d]{32}': "md5", r"[a-fA-F\d]{40}": "sha1", r"[a-fA-F\d]{64}": "sha256"}


def get_hash_type(file_hash):
    for regex in hash_regex:
        if match(regex, file_hash):
            return hash_regex[regex]
    raise ValueError("{0} is not a valid md5, sha1, or sha256 hash".format(file_hash))


def get_file_hash(file_obj, hash_type="sha256", block_size=65536):
    try:
        hasher = hash_types[hash_type.lower()]()
    except KeyError:
        raise ValueError("Invalid hash type")
    file_obj.seek(0)
    buffer = file_obj.read(block_size)
    while len(buffer) > 0:
        hasher.update(buffer)
        buffer = file_obj.read(block_size)
    file_obj.seek(0)
    return hasher.hexdigest()


class Cuckoo(object):
    @staticmethod
    def raise_errors(response, *args, **kwargs):
        response.raise_for_status()
        if response.headers.get("content-type").lower().startswith("application/json"):
            results = response.json()
            if results["error"]:
                raise RuntimeError(results["error_value"])

    def __init__(self, cuckoo_root, username=None, password=None, verify=True, proxies=None):
        self.root = cuckoo_root
        self.api_root = "{0}/api".format(self.root)
        self.username = username
        self.password = password
        self.session = session()
        self.session.verify = verify
        self.session.proxies = proxies
        self.session.hooks = dict(response=self.raise_errors)
        if username or password:
            self.session.auth = (self.username, self.password)

    def submit_file(self, file_name, file_to_upload, tags=None, options=None):
        if tags is None:
            tags = ""
        if options is None:
            options = ""

        url = "{0}{1}".format(self.api_root, "/tasks/create/file/")
        data = dict(tags=tags, options=options)
        files = dict(file=(file_name, file_to_upload))
        response = self.session.post(url, files=files,
                                     data=data)
        return response.json()["data"]["task_ids"]

    def submit_url(self, url, tags=None, options=None):
        if tags is None:
            tags = ""
        if options is None:
            options = "procmemdump=yes"
        else:
            options = "process_memory=yes,{0}".format(options)

        api_url = "{0}{1}".format(self.api_root, "/tasks/create/url/")
        data = dict(url=url, tags=tags, options=options)
        response = self.session.post(api_url, data=data)
        return response.json()["data"]["task_ids"]

    def submit_vtdl(self, file_hash, tags=None, options=None):
        if tags is None:
            tags = ""
        if options is None:
            options = "procmemdump=yes"
        else:
            options = "process_memory=yes,{0}".format(options)

        api_url = "{0}{1}".format(self.api_root, "/tasks/create/vtdl/")
        data = dict(vtdl=file_hash, tags=tags, options=options)
        response = self.session.post(api_url, data=data)
        return response.json()["data"]['task_ids']

    def find_tasks(self, sample_hash):
        hash_type = get_hash_type(sample_hash)
        results = self.session.get("{0}/tasks/search/{1}/{2}".format(self.api_root, hash_type, sample_hash)).json()
        results = results['data']
        if len(results) > 0:
            results = list(map(lambda x: x['id'], results))

        return results

    def extended_search(self, options):
        return self.session.post("{0}/tasks/extendedsearch/".format(self.api_root), data=options).json()['data']

    def list_tasks(self, limit=None, offset=None, window=None):
        url = "{0}/tasks/list/".format(self.api_root)
        if limit:
            url += limit
            if offset:
                url += "/{0}/".format(offset)
                if window:
                    url += "/{0}/".format(window)

        return self.session.get(url).json()

    def view_task(self, task_id):
        return self.session.get("{0}/tasks/view/{1}".format(self.api_root, task_id)).json()['data']

    def reschedule_task(self, task_id):
        return self.session.get("{0}/tasks/view/{1}".format(self.api_root, task_id)).json()['data']

    def delete_task(self, task_id):
        return self.session.get("{0}/tasks/delete/{1}".format(self.api_root, task_id)).json()['data']

    def get_task_status(self, task_id):
        status = self.session.get("{0}/tasks/status/{1}".format(self.api_root, task_id)).json()['data']
        # Workaround the difference in status names in web API and UI
        if status == "completed":
            status = "processing"

        return status

    def get_task_report(self, task_id, report_format="json"):
        response = self.session.get("{0}/tasks/get/report/{1}/{2}".format(self.api_root, task_id, report_format))
        if report_format == "json":
            results = response.json()['data']
        elif report_format == "pdf":
            results = BytesIO(response.content)
        else:
            results = response.content

        return results

    def get_task_iocs(self, task_id, detailed=False):
        url = "{0}/tasks/get/iocs/{1}".format(self.api_root, task_id)
        if detailed:
            url += "/detailed/"
        return self.session.get(url).json()['data']

    def get_task_axcreenshots(self, task_id, screenshot_id=None):
        url = "{0}/tasks/get/screenshot/{1}/".format(self.api_root, task_id)
        if screenshot_id:
            url += "{0}/".format(screenshot_id)
        return BytesIO(self.session.get(url).content)

    def get_task_procmemory(self, task_id, pid=None):
        url = "{0}/tasks/get/procmemory/{1}/".format(self.api_root, task_id)
        if pid:
            url += "{0}/".format(pid)
        return BytesIO(self.session.get(url).content)

    def get_task_fullmemory(self, task_id):
        url = "{0}/tasks/get/fullmemory/{1}/".format(self.api_root, task_id)
        return BytesIO(self.session.get(url).content)

    def get_task_pcap(self, task_id):
        url = "{0}/tasks/get/pcap/{1}/".format(self.api_root, task_id)
        return BytesIO(self.session.get(url).content)

    def get_task_dropped_files(self, task_id):
        url = "{0}/tasks/get/sropped/{1}/".format(self.api_root, task_id)
        return BytesIO(self.session.get(url).content)

    def get_task_suri_files(self, task_id):
        url = "{0}/tasks/get/surifile/{1}/".format(self.api_root, task_id)
        return BytesIO(self.session.get(url).content)

    def view_file(self, file_hash):
        hash_type = get_hash_type(file_hash)
        return self.session.get("{0}/files/view/{1/{2}}".format(self.api_root, hash_type, file_hash).json())

    def get_file(self, file_hash):
        hash_type = get_hash_type(file_hash)
        results = BytesIO(self.session.get("{0}/files/get/{1/{2}}".format(self.api_root, hash_type, file_hash)).json())
        results = results["data"]
        return results

    def list_machines(self):
        return self.session.get("{0}/machines/list/".format(self.api_root).json())['data']

    def view_machine(self, machine_name):
        return self.session.get("{0}/machines/view/{1}/".format(self.api_root, machine_name).json())['data']

    def get_cuckoo_status(self):
        return self.session.get("{0}/cuckoo/status/".format(self.api_root).json())['data']
