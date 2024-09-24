# rippled_peer_crawler
Crawls rippled servers and tallies information on connected peers, including geolocating IP addresses using a MaxMind City database.

## Requires
`pip install aiohttp dnspython geoip2`

MaxMind DB must be downloaded manually and extracted.

## Running the program
1. Download and extract the MaxMind City DB.
2. `pip install -r reqirements.txt`
3. Check variables in crawl.py and tallies.py
4. `python3 crawl.py`
5. (optional) `python3 tallies.py`
6. Do stuff with the JSON output from crawl.py and/or View the output file specified in tallies.py
