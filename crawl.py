'''
Returns a list of details for unique rippled peers that are either connected to specified servers
or that are found through recursive network crawls using rippled peer ports.

Includes MaxMind integration for geolocating servers (additional subscription required.)
'''

import json
import logging
import time

import aiohttp
import asyncio

import geoip2.database


# User adjustable variables
BOOTSTRAP_ADDRS = ["45.139.107.12:51235",] # Can be an IP address or URL. If URL, omit "http/s".
NUM_ITERATIONS = 6 # Set to 0 to only crawl bootstrap address(es)
TIMEOUT = 5 # Seconds to wait for HTTP requests to timeout
OUTPUT_FILE = 'peers.json'
MAX_MIND_DB = "GeoLite2-City.mmdb"
LOG_FILE = 'peer_crawl.log'
LOG_LEVEL = logging.INFO

# Global variables to track recursive queries
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
            peer_id = str("[" + peer['ip'] + "]:" + str(peer['port']))
            if peer_id not in COLLECTED_IPS:
                COLLECTED_IPS.append(peer_id)
        except KeyError:
            pass
        if peer['public_key'] not in PEER_KEYS:
            peers.append(peer)
            PEER_KEYS.append(peer['public_key'])
    return peers

async def http_query(url, session):
    '''
    Query a peer server.
    '''
    try:
        async with session.get(url, ssl=False, timeout=TIMEOUT) as response:
            logging.info("Preparing to query server: " + url)
            response = await response.json()
            response = response['overlay']['active']
    except(asyncio.exceptions.TimeoutError, json.decoder.JSONDecodeError):
        response = []
    return response

async def query_multiple_peers(urls):
    '''
    Pass multiple requests to http_query.
    '''
    async with aiohttp.ClientSession() as session:
        replies = [http_query(url, session) for url in urls]
        responses = await asyncio.gather(*replies)
        return responses

def crawl_batch(ips):
    '''
    Create a peer list based on a list of IPs.
    '''
    global CRAWLED_PEERS
    peer_responses = []
    peers_to_crawl = []
    for ip in ips:
        if ip not in CRAWLED_PEERS:
            url = str("https://" + ip + "/crawl")
            peers_to_crawl.append(url)
            CRAWLED_PEERS.append(ip)
    responses = asyncio.run(query_multiple_peers(peers_to_crawl))
    for response in responses:
        peer_responses = peer_responses + response
    return clean_peers(peer_responses)

def iterate_peers():
    '''
    Attempt to query newly acquired peers a defined number of times.
    '''
    count = 1
    peers = []

    while count <= NUM_ITERATIONS:
        count += 1
        logging.info("Preparing to complete the: " + str(count) + " iteration with: " + str(len(COLLECTED_IPS)) + " prospective addresses.")
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
