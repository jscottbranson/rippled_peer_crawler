from collections import Counter
import json

INPUT_FILE = 'peers.json'
OUTPUT_FILE = 'peer_counts.txt'

with open(INPUT_FILE) as peers_raw:
    peers = json.load(peers_raw)
    peers_raw.close()

c = Counter()
v = Counter()
d = Counter()
p = Counter()

ips = []

for peer in peers:
    try:
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

open(OUTPUT_FILE, "w").close()
with open(OUTPUT_FILE, "a") as output:
    output.write("Server Country:\n" + str(c))
    output.write("\n\nServer Version:\n" + str(v))
    output.write("\n\nConnection Direction:\n" + str(d))
    output.write("\n\nPeer Port:\n" + str(p))
    output.write("\n\nTotal Peers: " + str(c.total()))
    output.write("\n\nTotal IPs: " + str(len(ips)))
