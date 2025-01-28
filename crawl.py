'''
Returns a list of details for unique rippled peers that are either connected to specified servers
or that are found through recursive network crawls using rippled peer ports.

Includes MaxMind integration for geolocating servers (additional subscription required.)
'''
import json
import logging
import time
import base64
import hashlib
import ipaddress

import aiohttp
import asyncio


from dns.asyncresolver import Resolver
import dns.resolver
import dns.rrset

import geoip2.database


# User adjustable variables
#BOOTSTRAP_ADDRESS = ["bacab.alloy.ee:21337", "hubs.xahau.as16089.net:21337"] # Can be an IP or URL. Include port. Enclose IPv6 in brackets: "[::]:port". Omit "https".
#DEFAULT_PORT = 21337
BOOTSTRAP_ADDRESS = ["23.88.13.20:51235", "217.15.175.95:51235","46.202.194.114:51235"] # Can be an IP or URL. Include port. Enclose IPv6 in brackets: "[::]:port". Omit "https".
DEFAULT_PORT = 51235

NUM_ITERATIONS = 10 # int. Set to 0 to only crawl bootstrap address(es).
RUN_FOREVER = True # bool. Query the network every SLEEP_TIME seconds indefinitely.
SLEEP_TIME = 300 # int. Time in seconds to sleep between queries.
TIMEOUT = 2 # int. Seconds to wait for HTTP requests to timeout.
OUTPUT_FILE = 'output/peers.json' # str. Location where peer JSON will be output.
MAX_MIND_DB = "GeoLite2-City.mmdb" # str. Location where the MMDB is located.
LOG_FILE = 'output/peer_crawl.log' # str. Logfile location.
LOG_LEVEL = logging.WARNING # Log level


# Global variables to track recursive queries
CRAWLED_PEERS = set()
COLLECTED_IPS = BOOTSTRAP_ADDRESS
PEER_KEYS = set()
CRAWL_ERRORS = []

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
        except(KeyError, ValueError, geoip2.errors.AddressNotFoundError):
            peer['country'] = None
            peer['city'] = None
        except FileNotFoundError:
            logging.warning(f"Unable to locate MaxMind DB: {MAX_MIND_DB}.")
    return peers

async def dns_query(peer) -> dns.rrset.RRset:
    try:
        res: dns.resolver.Answer = await Resolver().resolve_address(peer['ip'], rdtype="PTR")
        ptr = res.rrset
        peer['ptr'] = str(ptr[0])[:-1]
    except:
        peer['ptr'] = None
    return peer

async def dns_bulk(*peers):
    coros = [dns_query(peer) for peer in peers]
    return await asyncio.gather(*coros)

async def rdns_query(peers):
    peers = await dns_bulk(*peers)
    return peers

def to_base58(v):
    __b58chars = 'rpshnaf39wBUDNEGHJKLM4PQRST7VWXYZ2bcdeCg65jkm8oFqi1tuvAxyz'
    __b58base = len(__b58chars)

    long_value = 0
    for (i, c) in enumerate(v[::-1]):
        long_value += (256 ** i) * c

    result = ''
    while long_value >= __b58base:
        div, mod = divmod(long_value, __b58base)
        result = __b58chars[mod] + result
        long_value = div
    result = __b58chars[long_value] + result

    nPad = 0
    for c in v:
        if c == 0:
            nPad += 1
        else:
            break

    return (__b58chars[0] * nPad) + result

def decode_pubkey(peer):
    '''
    Decode pubkey_node.
    '''
    try:
        x = base64.b64decode(peer['public_key'])
        vdata = bytes([28]) + x
        h = hashlib.sha256(hashlib.sha256(vdata).digest()).digest()
        key = vdata + h[0:4]
        peer['public_key'] = to_base58(key)
    except Exception as e:
        logging.warning(f"Error normalizing public key: {e}")
    return peer
def sort_ip4_ip6(peer):
    '''
    Check if a peer address is IPv4 or IPv6
    '''
    try:
        ip = ipaddress.ip_address(peer['ip'])
        if isinstance(ip, ipaddress.IPv6Address):
            peer['ip'] = f'[{peer['ip']}]'
    except ValueError:
        pass
    return peer

def clean_ip(peer):
    '''
    Remove `::ffff:` prefix from IPv4 addresses.
    Add newly discovered IPs to the list for crawling.
    '''
    global COLLECTED_IPS
    try:
        if peer['ip'].startswith( "::ffff:"):
            peer['ip'] = peer['ip'][7:]
        peer = sort_ip4_ip6(peer)
        try:
            peer_id = f"{peer['ip']}:{peer['port']}"
        except KeyError:
            # If a server reports an IP address without a port, assume the default.
            peer_id = f"{peer['ip']}:{DEFAULT_PORT}"
        if peer_id not in COLLECTED_IPS:
            COLLECTED_IPS.append(peer_id)
    except KeyError:
        pass
    return peer

def clean_peers(peer_responses):
    '''
    Creates a list of IP addresses with redundant entries and IPv6
    removed. Input is a decoded /crawl endpoint response.
    '''
    peers = []
    global PEER_KEYS
    for peer in peer_responses:
        peer = clean_ip(peer)
        peer = decode_pubkey(peer)
        if peer['public_key'] not in PEER_KEYS:
            peers.append(peer)
            PEER_KEYS.add(peer['public_key'])
    return peers

async def http_query(url, session):
    '''
    Query a peer server.
    '''
    global CRAWL_ERRORS
    try:
        async with session.get(url, ssl=False, timeout=TIMEOUT) as response:
            logging.info("Preparing to query server: " + url)
            response = await response.json()
            response = response['overlay']['active']
    except(aiohttp.client_exceptions.ClientOSError, aiohttp.client_exceptions.ClientConnectorError, aiohttp.client_exceptions.ServerDisconnectedError, asyncio.exceptions.TimeoutError, json.decoder.JSONDecodeError) as error:
        logging.warning("Error: " + str(error) + " querying: " + url)
        CRAWL_ERRORS.append({'url': url, 'error': error})
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
            url = f"https://{ip}/crawl"
            peers_to_crawl.append(url)
            CRAWLED_PEERS.add(ip)
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
        logging.info("Preparing to complete the: " + str(count) + " iteration with: " + str(len(COLLECTED_IPS)) + " prospective addresses.")
        count += 1
        peers = peers + crawl_batch(COLLECTED_IPS)
    return peers

def query_network():
    '''
    Run the program.
    '''
    start_time = time.time()
    print("Preparing to crawl.")
    peers = iterate_peers()
    peers = lookup_location(peers)
    peers = asyncio.run(rdns_query(peers))
    write_to_text(peers)
    output_text = f"\nRuntime: {round(time.time() - start_time, 2)} seconds.\nConnected to: {len(COLLECTED_IPS) - len(CRAWL_ERRORS)} / {len(COLLECTED_IPS)} potential IP addresses.\nTotal public keys identified: {len(peers)}."
    logging.warning(output_text)
    print(output_text)

def run():
    while True:
        try:
            query_network()
            if not RUN_FOREVER:
                break
            time.sleep(SLEEP_TIME)
            global CRAWLED_PEERS
            global PEER_KEYS
            global CRAWL_ERRORS
            CRAWLED_PEERS = set()
            PEER_KEYS = set()
            CRAWL_ERRORS = []
        except KeyboardInterrupt:
            break

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
    logging.info("Logging configured successfully.")

if __name__ == "__main__":
    start_log()
    run()
