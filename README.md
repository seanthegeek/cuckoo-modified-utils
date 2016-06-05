# cuckoo-modified-utils
Useful scripts for [Brad Spengler's fork of Cuckoo](https://github.com/spender-sandbox/cuckoo-modified)

## Requirements

These scripts require changes to the Cuckoo API that were proposed in 
[PR #160](https://github.com/spender-sandbox/cuckoo-modified/pull/160).
They currently have not been merged.

- [`requests`](https://pypi.python.org/pypi/requests/) - HTTP for humans
- [`pyldfire`](https://github.com/seanthegeek/pyldfire) - A python module for the Wildfire API (required for
`wildfire-to-cuckoo.py` only)
- `cuckoo.py` - A basic module for interacting with the Cuckoo API (included in this repository)

## Command line scripts

Each one of these scripts will submit one or more samples to a Cuckoo sandbox, and track the task as the sample is
being analyzed. When submitting individual files, the scripts will check for existing reports, and notify you of any
before submitting a new task.

    usage: submit-to-cuckoo.py [-h] [-v] [--tags TAGS] [--options OPTIONS] [--tor]
                               [--procmemdump]
                               sample [sample ...]
    
    Submits files or a URL to Cuckoo
    
    positional arguments:
      sample             One or more filenames or globs, or a single URL
    
    optional arguments:
      -h, --help         show this help message and exit
      -v, --version      show program's version number and exit
      --tags TAGS        Comma separated tags for selecting an analysis VM
      --options OPTIONS  Comma separated option=value pairs
      --tor              Enable Tor during analysis
      --procmemdump      Dump and analyze process memory

--------------------------------------------------------------------------------

    usage: tor-to-cuckoo.py [-h] [-v] [--tags TAGS] [--options OPTIONS] [--tor]
                            [--procmemdump] [--user-agent USER_AGENT]
                            URL
    
    Downloads a file via Tor, through a privoxy chain, and sends it to Cuckoo
    
    positional arguments:
      URL                   URL of the sample
    
    optional arguments:
      -h, --help            show this help message and exit
      -v, --version         show program's version number and exit
      --tags TAGS           Comma separated tags for selecting an analysis VM
      --options OPTIONS     Comma separated option=value pairs
      --tor                 Enable Tor during analysis
      --procmemdump         Dump and analyze process memory
      --user-agent USER_AGENT
                            The user agent to spoof. Default: Mozilla/5.0
                            (compatible; MSIE 10.0; Windows NT 6.1; Trident/4.0;
                            InfoPath.2; .NET CLR 2.0.50727; WOW64)

-----------------------------------------------------------------------------

    usage: wildfire-to-cuckoo.py [-h] [-v] [--tags TAGS] [--options OPTIONS]
                                 [--tor] [--procmemdump]
                                 hash [filename]
    
    Downloads a sample from Palo Alto Network's Wildfire service and sends it to
    Cuckoo. Requires pyldfire - https://github.com/seanthegeek/pyldfire
    
    positional arguments:
      hash               A MD5, SHA1, or SHA256 hash of a sample
      filename           The filename of the sample
    
    optional arguments:
      -h, --help         show this help message and exit
      -v, --version      show program's version number and exit
      --tags TAGS        Comma separated tags for selecting an analysis VM
      --options OPTIONS  Comma separated option=value pairs
      --tor              Enable Tor during analysis
      --procmemdump      Dump and analyze process memory
 