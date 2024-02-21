'''
Returns a list of details for unique rippled peers that are either connected to specified servers
or that are found through recursive network crawls using rippled peer ports.

Includes MaxMind integration for geolocating servers (additional subscription required.)
'''

import requests
import json
import logging
import time

import geoip2.database


BOOTSTRAP_ADDRS = ["45.139.107.12:51235",] # Can be an IP address or URL. If URL, omit "http/s".
NUM_ITERATIONS = 100 # Set to 0 to only crawl bootstrap address(es)
LOG_FILE = 'peer_crawl.log'
LOG_LEVEL = logging.INFO
OUTPUT_FILE = 'peers.json'
MAX_MIND_DB = "GeoLite2-City.mmdb"

CRAWLED_PEERS = []
COLLECTED_IPS = []
PEER_KEYS = []


def write_to_text(peers):
    '''
    Output information to a new text file.
    '''
    open(OUTPUT_FILE, "w").close()
    with open(OUTPUT_FILE, "a") as output_file:
        json.dump(peers, output_file)
        output_file.close()

def lookup_location(peers):
    '''
    Search MaxMind DB to locate IP.
    '''
    for peer in peers:
        try:
            if peer['ip']:
                with geoip2.database.Reader(MAX_MIND_DB) as reader:
                    response = reader.city(peer['ip'])
                    peer['country'] = response.country.iso_code
                    peer['city'] = response.city.name
        except(KeyError, geoip2.errors.AddressNotFoundError):
            peer['country'] = "Unknown"
            peer['city'] = "Unknown"
    return peers

def clean_peers(peer_responses):
    '''
    Creates a list of IP addresses with redundant entries and IPv6
    removed. Input is a decoded /crawl endpoint response.
    '''
    peers = []
    peer_keys = []
    global COLLECTED_IPS
    global PEER_KEYS
    for peer in peer_responses:
        try:
            if peer['ip'].startswith( "::ffff:"):
                peer['ip'] = peer['ip'][7:]
            if peer['ip'] not in COLLECTED_IPS:
                COLLECTED_IPS.append(str(peer['ip'] + ":" + str(peer['port'])))
        except KeyError:
            pass
        if peer['public_key'] not in PEER_KEYS:
            peers.append(peer)
            PEER_KEYS.append(peer['public_key'])
    return peers

def query_peer_endpoint(server):
        response = []
        try:
            url = str("https://" + server + "/crawl")
            response = requests.get(url, verify=False, timeout=2).json()['overlay']['active']
        except (KeyError, requests.exceptions.RequestException):
            logging.error("Connection error: " + url)
        return response

def crawl_batch(ips):
    '''
    Create a peer list based on a list of IPs.
    '''
    global CRAWLED_PEERS
    peer_responses = []
    for server in ips:
        if server not in CRAWLED_PEERS:
            logging.info("Preparing to call server: " + server)
            CRAWLED_PEERS.append(server)
            peer_responses = peer_responses + query_peer_endpoint(server)
    return clean_peers(peer_responses)

def iterate_peers():
    '''
    Attempt to query newly acquired peers a defined number of times.
    '''
    count = 1
    peers = []

    while count <= NUM_ITERATIONS:
        count += 1
        peers = peers + crawl_batch(COLLECTED_IPS)
    return peers

def start_log():
    '''
    Setup log.
    '''
    logging.basicConfig(
        filename=LOG_FILE,
        level=LOG_LEVEL,
        datefmt="%Y-%m-%d %H:%M:%S",
        format='%(asctime)s %(levelname)s: %(module)s - %(funcName)s (%(lineno)d): %(message)s',
    )

def run():
    '''
    Run the program.
    '''
    start_time = time.time()
    start_log()
    peers = crawl_batch(BOOTSTRAP_ADDRS) + iterate_peers()
    peers = lookup_location(peers)
    write_to_text(peers)
    logging.warning(str(len(CRAWLED_PEERS)) + " peers crawled in: " + str(round(time.time() - start_time, 1)) + " seconds.")

if __name__ == "__main__":
    run()
