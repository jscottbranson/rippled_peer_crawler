'''
Returns a list of details for unique rippled peers that are connected to specified servers.
'''

import requests
import json

import geoip2.database


IPS = [
"52.32.149.27",
"54.237.246.60",
"52.23.250.193",
"100.24.12.73",
"3.122.10.154",
"72.44.58.240",
"34.221.145.175",
"35.162.59.23",
"35.92.8.75",
"34.230.16.97",
"3.67.69.93",
"34.222.89.232",
"52.27.230.2",
"52.32.242.103",
]

IPS_ZAPHOD = [
"46.4.218.119",
"95.216.102.182",
"45.139.107.4",
"46.4.138.103",
"195.201.61.31",
"45.139.107.16",
"46.4.218.120",
"45.139.107.6",
"45.139.107.12",
"95.216.5.218",
"116.202.148.26",
"94.130.221.23",
"95.216.102.188",
"116.202.163.130",
]

IPS = IPS_ZAPHOD

OUTPUT_FILE = 'peers.json'


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
                with geoip2.database.Reader('GeoLite2-City.mmdb') as reader:
                    response = reader.city(peer['ip'])
                    peer['country'] = response.country.iso_code
                    peer['city'] = response.city.name
        except KeyError:
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
    for peer in peer_responses:
        try:
            if peer['ip'].startswith( "::ffff:"):
                peer['ip'] = peer['ip'][7:]
        except KeyError:
            pass
        if peer['public_key'] not in peer_keys:
            peers.append(peer)
            peer_keys.append(peer['public_key'])
    return peers

def query_peer_endpoint(server):
        url = str("https://" + server + ":51235/crawl")
        response = []
        try:
            response = requests.get(url, verify=False).json()['overlay']['active']
        except (KeyError, requests.exceptions.RequestException):
            print("Connection error:", url)
        return response

def run():
    '''
    Run the program.
    '''
    peer_responses = []
    for server in IPS:
        peer_responses = peer_responses + query_peer_endpoint(server)
    peer_responses = clean_peers(peer_responses)
    peer_responses = lookup_location(peer_responses)
    write_to_text(peer_responses)

if __name__ == "__main__":
    run()
