import os
import requests
import time
from multiprocessing import Pool, TimeoutError

# Define constants
processing_timeout = 15
max_retries = 5
output_file = "public_keys.txt"
address_file = "address.txt"

# BlockCypher API
blockcypher_api = {
    "url": "https://api.blockcypher.com/v1/btc/main/addrs/{address}/full",
    "name": "BlockCypher",
    "key_path": "txrefs",
    "script_key": "script"
}

def get_data_from_blockcypher(address):
    """Helper function to get data from BlockCypher API, respecting rate limits"""
    url = blockcypher_api["url"].format(address=address)
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                print(f"Address not found: {url}")
                return None
            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))  # Fallback to 60 seconds if no header
                print(f"Rate limit hit at {url}. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
                continue
            else:
                print(f"Unexpected error {response.status_code} at {url}: {response.text}. Retrying...")
        except requests.RequestException as e:
            print(f"Request error: {e}. Retrying...")
        time.sleep(2)  # brief pause before retrying
    return None

def extract_public_keys(data):
    """Extract public keys from the transaction data"""
    public_keys = set()
    key_path = blockcypher_api["key_path"]
    script_key = blockcypher_api["script_key"]

    if key_path in data:
        for item in data[key_path]:
            if script_key in item:
                script = item[script_key]
                if len(script) > 66:  # Check if the script is long enough to contain a public key
                    public_key = script[-66:]  # Example logic; may need adjustment
                    public_keys.add(public_key)
    return public_keys

def process_address(address):
    """Process an address by checking BlockCypher API"""
    data = get_data_from_blockcypher(address)
    if data:
        public_keys = extract_public_keys(data)
        return public_keys if public_keys else None
    return None

def main():
    if not os.path.exists(address_file):
        print(f"The file {address_file} does not exist.")
        return

    found_keys = []
    not_found_keys = []
    unique_public_keys = set()

    with open(address_file, 'r') as f:
        addresses = [line.strip() for line in f if line.strip()]

    with open(output_file, 'w') as out_file:
        for address in addresses:
            if not address:  # Skip empty lines
                continue

            print(f"Processing address: {address}")

            while True:  # Keep trying until we process the address
                with Pool(1) as p:
                    result = p.apply_async(process_address, (address,))

                    try:
                        public_keys = result.get(timeout=processing_timeout)
                    except TimeoutError:
                        print(f"Processing timed out for address: {address}. Retrying...")
                        public_keys = None

                if public_keys:
                    print(f"Public key found for address: {address}")
                    found_keys.append(address)
                    for pk in public_keys:
                        if pk not in unique_public_keys:
                            unique_public_keys.add(pk)
                            out_file.write(f"{pk}\n")
                    break
                else:
                    print(f"No public key found for address: {address}")
                    not_found_keys.append(address)
                    break

    # Print summary
    print("\nSummary:")
    print("\nAddresses with public keys found:")
    for address in found_keys:
        print(address)

    print("\nAddresses with no public keys found:")
    for address in not_found_keys:
        print(address)

    print(f"\nPublic keys have been written to {output_file}")

if __name__ == "__main__":
    main()
