# cuckoo-modified-utils
Useful scripts for [Brad Spengler's fork of Cuckoo](https://github.com/spender-sandbox/cuckoo-modified)

`cuckoo.py` - A basic module for interacting with the API

`tor-to-cuckoo.py` - A utility that can take in command line options to
download a file to memory, though a Privoxy instance chained to Tor,
submit it to a Cuckoo instance, and return the task ID(s)

`submit-to-cuckoo.py` - Submits local files or a URL to Cuckoo

`wildfire-to-cuckoo.py` - Submits a sample from Palo Alto Networks' WildFire to Cuckoo using [pyldfire](https://github.com/seanthegeek/pyldfire)
