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
    ip = Counter()

    ips = []
    peer_data = []
    no_ip = 0
    amazon = 0
    ysd = 0
    google = 0
    zaphod = 0
    zh_out = []
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
            ip[peer['ip']] +=1
        except KeyError:
            pass
        try:
            if peer['ptr'][-13:] == "amazonaws.com":
                amazon +=1
        except(KeyError, TypeError):
            pass
        try:
            if peer['ptr'][-14:] == "your-server.de":
                ysd +=1
        except(KeyError, TypeError):
            pass
        try:
            if peer['ptr'][-21:] == "googleusercontent.com":
                google +=1
        except(KeyError, TypeError):
            pass
        try:
            if not peer['ptr']:
                ptr_uk +=1
        except(KeyError, TypeError):
                ptr_uk +=1
        try:
            if peer['ptr'].lower() == "zaphod.alloy.ee":
                zaphod +=1
                zh_out.append(f"{peer['public_key']}    {peer['ip']}   {peer['version']}")
        except(KeyError, TypeError, AttributeError):
            pass



    open(OUTPUT_FILE, "w").close()
    with open(OUTPUT_FILE, "a") as output:
        output.write("Server Country:\n" + str(c))
        output.write("\n\nServer Version:\n" + str(v))
        output.write(f"\nTotal versions reported: {sum(v.values())}")
        output.write("\n\nConnection Direction:\n" + str(d))
        output.write("\n\nPeer Port:\n" + str(p))
        output.write("\n\nUnknown PTR Records: " + str(ptr_uk))
        output.write("\n\nAmazon PTR Records: " + str(amazon))
        output.write("\n\nYour-Server.de PTR Records: " + str(ysd))
        output.write("\n\nGoogle PTR Records: " + str(google))
        output.write("\n\nZaphod PTR Records: " + str(zaphod))
        output.write("\n\nUnknown IP Address: " + str(no_ip))
        output.write("\n\nTotal IPs: " + str(len(ips)))
        output.write("\n\nUnique public keys: " + str(c.total()))

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
