"""

To load the .jsonl file:

with open("straininfo_strains.jsonl") as f:
    d = [json.loads(line) for line in f]


"""

import requests
import json
import time
from pathlib import Path

BASE = "https://api.straininfo.dsmz.de/v2"
BATCH_SIZE = 1000 

base_dir = Path('/var/external_data/straininfo/')
base_dir.mkdir(exist_ok=True)

session = requests.Session()
session.headers.update({"accept": "application/json"})

# Get strain count
r = session.get(f"{BASE}/count/strains", timeout=60)
r.raise_for_status()

count_data = r.json()
print("Count response:", count_data)

# Set this after inspecting the count response
total = int(count_data[0])

output = Path(base_dir, "straininfo_strains.jsonl")
missing = []

with output.open("w", encoding="utf-8") as f:
    
    #f.write("[\n")
    #first_record = True

    for strain_id_f in range(1, 20000 + 1, BATCH_SIZE):

        strain_id_l = min(strain_id_f + BATCH_SIZE - 1, total)

        url = f"{BASE}/data/strain/max/{strain_id_f}-{strain_id_l}"

        try:
            response = session.get(url, timeout=60)

            if response.status_code == 404:
                missing.append(strain_id)
                continue

            response.raise_for_status()

            records = response.json()

            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

                #if not first_record:
                #    f.write(",\n")

                #json.dump(record, f, ensure_ascii=False)
                #first_record = False


            #f.write(json.dumps(records, ensure_ascii=False) + "\n")

        except requests.RequestException as e:
            print(f"Error retrieving {strain_id}: {e}")
            missing.append(strain_id)

        if strain_id_l % 1000 == 0:
            print(f"Processed {strain_id_l}/{total}")

        time.sleep(0.1)

print("Missing IDs:", len(missing))
