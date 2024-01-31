from collections import Counter
import json

INPUT_FILE = 'peers.json'
OUTPUT_FILE = 'counts.txt'

with open(INPUT_FILE) as peers_raw:
    peers = json.load(peers_raw)
    peers_raw.close()

c = Counter()
v = Counter()
for peer in peers:
    try:
        v[peer["version"]] +=1
        c[peer["country"]] +=1
    except KeyError:
        pass

open(OUTPUT_FILE, "w").close()
with open(OUTPUT_FILE, "a") as output:
    output.write(str(c))
    output.write("\n" + str(v))
    output.write("\nTotal Peers: " + str(c.total()))
