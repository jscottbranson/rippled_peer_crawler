# rippled_peer_crawler
Crawls rippled servers and tallies information on connected peers, including geolocating IP addresses using a MaxMind City database.

MaxMind DB must be downloaded manually and extracted.

## Running the program
1. Download and extract the MaxMind City DB.
2. `pip install -r reqirements.txt`
3. Check variables in crawl.py and tallies.py
4. `python3 crawl.py`
5. `python3 tallies.py`
6. View the output file specified in tallies.py
