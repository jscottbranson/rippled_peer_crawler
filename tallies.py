from collections import Counter
import json
import time

INPUT_FILE = 'output/peers.json'
OUTPUT_FILE = 'output/peer_counts.txt'
IPS_FILE = 'output/peer_ips.txt'
PUBLIC_KEYS_FILE = 'output/peer_pubkeys.txt'
PEERS_FILE = 'output/peers_summary.txt'

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

    print(f'There are {len(peers)} peers identified.')

    c = Counter()
    v = Counter()
    d = Counter()
    p = Counter()
    k = Counter()
    ip = Counter()

    peer_data = []
    ips = []
    reused_ips = 0
    no_ip = 0
    amazon = 0
    ysd = 0
    google = 0
    hstgr = 0
    edu = 0
    ptr_uk = 0

    for peer in peers:
        try:
            peer_data.append(f"{peer['public_key']}: {peer['ip']}:{peer['port']}")
        except KeyError:
            try:
                peer_data.append(f"{peer['public_key']}: {peer['ip']} no port")
            except KeyError:
                try:
                    peer_data.append(f"{peer['public_key']}: {peer['port']} no IP")
                except KeyError:
                    peer_data.append(f"{peer['public_key']}: no IP no port")

        try:
            if peer['ip'] not in ips:
                ips.append(peer['ip'])
            elif peer['ip'] in ips:
                reused_ips +=1
        except KeyError:
            no_ip +=1
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
            k[peer["public_key"]] +=1
        except KeyError:
            pass
        try:
            ip[peer['ip']] +=1
        except KeyError:
            pass

        # Count PTR Records
        try:
            if peer['ptr'][-13:].lower() == "amazonaws.com":
                amazon +=1
        except(KeyError, TypeError):
            pass
        try:
            if peer['ptr'][-14:].lower() == "your-server.de":
                ysd +=1
        except(KeyError, TypeError):
            pass
        try:
            if peer['ptr'][-21:].lower() == "googleusercontent.com":
                google +=1
        except(KeyError, TypeError):
            pass
        try:
            if peer['ptr'][-11:].lower() == "hstgr.cloud":
                hstgr +=1
        except(KeyError, TypeError):
            pass
        try:
            if peer['ptr'][-4:].lower() == ".edu":
                edu +=1
        except(KeyError, TypeError, AttributeError):
            pass
        try:
            if not peer['ptr']:
                ptr_uk +=1
        except(KeyError, TypeError):
                ptr_uk +=1



    open(OUTPUT_FILE, "w").close()
    with open(OUTPUT_FILE, "a") as output:
        output.write("Server Country:\n" + str(c))
        output.write("\n\nServer Version:\n" + str(v))
        output.write(f"\nTotal versions reported: {sum(v.values())}")
        output.write("\n\nConnection Direction:\n" + str(d))
        output.write("\n\nPeer Port:\n" + str(p))
        output.write("\n\nAmazon PTR Records: " + str(amazon))
        output.write("\nYour-Server.de PTR Records: " + str(ysd))
        output.write("\nGoogle PTR Records: " + str(google))
        output.write("\nHostinger PTR Records: " + str(hstgr))
        output.write("\n.edu PTR Records: " + str(edu))
        output.write("\nNo PTR Record: " + str(ptr_uk))
        output.write("\n\nUnique countries: " + str(len(c.keys())))
        output.write("\n\nServers without published IP Address: " + str(no_ip))
        output.write("\nServers sharing an IP address: " + str(reused_ips))
        output.write("\nUnique IPs: " + str(len(ips)))
        output.write("\n\nUnique public keys: " + str(k.total()))

    open(IPS_FILE, "w").close()
    with open(IPS_FILE, "a") as output:
        for address in ips:
            output.write(address + "\n")

    open(PEERS_FILE, "w").close()
    with open(PEERS_FILE, "a") as output:
        for peer in peer_data:
            output.write(peer + "\n")

if __name__ == "__main__":
    while True:
        run()
        time.sleep(15)
