from collections import Counter
import json
import time

INPUT_FILE = 'peers.json'
OUTPUT_FILE = 'peer_counts.txt'
IPS_FILE = 'peer_ips.txt'

def run():
    '''
    Count things!
    '''
    try:
        with open(INPUT_FILE) as peers_raw:
            peers = json.load(peers_raw)
            peers_raw.close()
    except (json.decoder.JSONDecodeError, FileNotFoundError):
        peers = {}

    c = Counter()
    v = Counter()
    d = Counter()
    p = Counter()
    ip = Counter()

    ips = []
    amazon = 0
    ysd = 0
    google = 0
    zaphod = 0
    ptr_uk = 0

    for peer in peers:
        try:
            if peer['ip'] not in ips:
                ips.append(peer['ip'])
        except KeyError:
            pass
        try:
            v[peer["version"]] +=1
        except KeyError:
            pass
        try:
            c[peer["country"]] +=1
        except KeyError:
            pass
        try:
            d[peer["type"]] +=1
        except KeyError:
            pass
        try:
            p[str(peer["port"])] +=1
        except KeyError:
            pass
        try:
            ip[peer['ip']] +=1
        except KeyError:
            pass
        try:
            if peer['ptr'][-13:] == "amazonaws.com":
                amazon +=1
        except KeyError:
            pass
        try:
            if peer['ptr'][-14:] == "your-server.de":
                ysd +=1
        except KeyError:
            pass
        try:
            if peer['ptr'][-21:] == "googleusercontent.com":
                google +=1
        except KeyError:
            pass
        try:
            if peer['ptr'] == "Unknown":
                ptr_uk +=1
        except KeyError:
            pass
        try:
            if peer['ptr'].lower() == "zaphod.alloy.ee":
                zaphod +=1
        except KeyError:
            pass



    open(OUTPUT_FILE, "w").close()
    with open(OUTPUT_FILE, "a") as output:
        output.write("Server Country:\n" + str(c))
        output.write("\n\nServer Version:\n" + str(v))
        output.write("\n\nConnection Direction:\n" + str(d))
        output.write("\n\nPeer Port:\n" + str(p))
        output.write("\n\nUnknown PTR Records: " + str(ptr_uk))
        output.write("\n\nAmazon PTR Records: " + str(amazon))
        output.write("\n\nYour-Server.de PTR Records: " + str(ysd))
        output.write("\n\nGoogle PTR Records: " + str(google))
        output.write("\n\nZaphod PTR Records: " + str(zaphod))
        output.write("\n\nTotal Peers: " + str(c.total()))
        output.write("\n\nTotal IPs: " + str(len(ips)))

    open(IPS_FILE, "w").close()
    with open(IPS_FILE, "a") as output:
        for address in ips:
            output.write(address + "\n")

if __name__ == "__main__":
    while True:
        run()
        time.sleep(15)
