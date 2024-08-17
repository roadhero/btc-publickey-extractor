import os
import time
import requests
from blockcypher import get_address_full

# File containing addresses, one per line
address_file = 'address.txt'
# Output file to save the public keys
output_file = 'public_keys.txt'
# Maximum number of retries after hitting rate limit
max_retries = 5

# Manually define the BlockCypher API base URL
BASE_URL = "https://api.blockcypher.com/v1/btc/main"
# Time to wait between requests (in seconds)
request_delay = 1  # Adjust this as needed to avoid hitting rate limits

def fetch_with_rate_limiting(url, params=None):
    """Fetch data from the BlockCypher API with rate limiting."""
    retries = 0

    while retries < max_retries:
        response = requests.get(url, params=params)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 1))
            print(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
            time.sleep(retry_after)
            retries += 1
        else:
            response.raise_for_status()

    raise Exception("Max retries exceeded for API request.")

def get_address_data(address):
    """Get address data with rate limiting."""
    url = f"{BASE_URL}/addrs/{address}"
    data = fetch_with_rate_limiting(url)
    time.sleep(request_delay)  # Introduce a delay between requests
    return data

def get_full_transaction_data(tx_hash):
    """Get full transaction data by hash."""
    url = f"{BASE_URL}/txs/{tx_hash}"
    data = fetch_with_rate_limiting(url)
    time.sleep(request_delay)  # Introduce a delay between requests
    return data

def extract_public_key_from_script(script):
    """
    Extract the public key from the script.
    This function assumes that the public key is located in the correct position in the script.
    """
    try:
        if len(script) >= 66 and (script[-66:][:2] == '02' or script[-66:][:2] == '03'):
            return script[-66:]  # Compressed public key
        elif len(script) >= 130 and script[-130:][:2] == '04':
            return script[-130:]  # Uncompressed public key
        else:
            return None
    except IndexError:
        return None
    except Exception as e:
        return None

def extract_and_compress_public_keys(address):
    try:
        # Fetch address data
        address_data = get_address_data(address)
        found_public_keys = set()  # To store unique public keys

        # Check if 'txrefs' is in the data
        if 'txrefs' not in address_data:
            return found_public_keys

        # Retrieve and process each full transaction
        for txref in address_data['txrefs']:
            tx_hash = txref['tx_hash']
            full_tx_data = get_full_transaction_data(tx_hash)

            # Process each input in the transaction
            for input in full_tx_data['inputs']:
                if 'addresses' in input and address in input['addresses']:
                    if 'script' in input:
                        public_key = extract_public_key_from_script(input['script'])
                        if public_key:
                            found_public_keys.add(public_key)

        return found_public_keys

    except Exception as e:
        return set()

def main():
    if not os.path.exists(address_file):
        print(f"The file {address_file} does not exist.")
        return

    with open(address_file, 'r') as f:
        addresses = [line.strip() for line in f if line.strip()]

    found_keys = []
    not_found_keys = []

    with open(output_file, 'w') as out_file:
        for address in addresses:
            if not address:  # Skip empty lines
                continue

            print(f"Processing address: {address}")
            public_keys = extract_and_compress_public_keys(address)

            if public_keys:
                print(f"Public key found for address: {address}")
                found_keys.append(address)
                for pk in public_keys:
                    out_file.write(f"{pk}\n")
            else:
                print(f"No public key found for address: {address}")
                not_found_keys.append(address)

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
