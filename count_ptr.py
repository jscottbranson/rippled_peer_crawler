import json

INPUT_FILE = 'output/peers.json'

def run():
    try:
        with open(INPUT_FILE) as peers_raw:
            peers = json.load(peers_raw)
            peers_raw.close()
    except (json.decoder.JSONDecodeError, FileNotFoundError):
        peers = {}

    print(f"There are {len(peers)} peers identified.")
    found_ptrs = []
    for peer in peers:
        try:
            ptr = peer['ptr'][-11:].lower()
            found_ptrs.append(ptr)
        except (TypeError):
            pass


    counts = {i:found_ptrs.count(i) for i in found_ptrs}
    for i in counts:
        print(i, counts[i])

if __name__ == "__main__":
    run()
