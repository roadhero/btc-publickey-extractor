import os
import time
import requests

# File containing addresses, one per line
address_file = 'address.txt'
# Output file to save the public keys
output_file = 'public_keys.txt'
# Maximum number of retries after hitting rate limit
max_retries = 5

# Manually define the BlockCypher API base URL
BASE_URL = "https://api.blockcypher.com/v1/btc/main"

# Variables to track API usage limits
requests_per_second = 3
requests_per_hour = 100
requests_per_day = 1000

# Initialize counters
request_count = 0
hourly_request_count = 0
daily_request_count = 0

# Time tracking
start_time = time.time()
hour_start_time = time.time()
day_start_time = time.time()

def fetch_with_rate_limiting(url, params=None):
    """Fetch data from the BlockCypher API with rate limiting."""
    global request_count, hourly_request_count, daily_request_count, start_time, hour_start_time, day_start_time

    while True:
        # Enforce request limits
        current_time = time.time()

        # Check if we're exceeding the per-second limit
        if request_count >= requests_per_second:
            elapsed_time = current_time - start_time
            if elapsed_time < 1:
                time.sleep(1 - elapsed_time)
            start_time = time.time()
            request_count = 0

        # Check if we're exceeding the per-hour limit
        if hourly_request_count >= requests_per_hour:
            elapsed_time = current_time - hour_start_time
            if elapsed_time < 3600:
                time_to_wait = 3600 - elapsed_time
                print(f"Hourly limit reached. Waiting for {int(time_to_wait)} seconds...")
                time.sleep(time_to_wait)
            hour_start_time = time.time()
            hourly_request_count = 0

        # Check if we're exceeding the per-day limit
        if daily_request_count >= requests_per_day:
            elapsed_time = current_time - day_start_time
            if elapsed_time < 86400:
                time_to_wait = 86400 - elapsed_time
                print(f"Daily limit reached. Waiting for {int(time_to_wait)} seconds...")
                time.sleep(time_to_wait)
            day_start_time = time.time()
            daily_request_count = 0

        response = requests.get(url, params=params)

        if response.status_code == 200:
            request_count += 1
            hourly_request_count += 1
            daily_request_count += 1
            return response.json()
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 1))
            print(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
            time.sleep(retry_after)
        else:
            response.raise_for_status()

def get_address_data(address, api_key):
    """Get address data with rate limiting."""
    url = f"{BASE_URL}/addrs/{address}"
    params = {'token': api_key}
    data = fetch_with_rate_limiting(url, params=params)
    return data

def get_full_transaction_data(tx_hash, api_key):
    """Get full transaction data by hash."""
    url = f"{BASE_URL}/txs/{tx_hash}"
    params = {'token': api_key}
    data = fetch_with_rate_limiting(url, params=params)
    return data

def extract_public_key_from_script(script):
    """Extract the public key from the script."""
    try:
        if len(script) >= 66 and (script[-66:][:2] == '02' or script[-66:][:2] == '03'):
            return script[-66:]  # Compressed public key
        elif len(script) >= 130 and script[-130:][:2] == '04':
            return script[-130:]  # Uncompressed public key
        else:
            return None
    except Exception:
        return None

def extract_and_compress_public_keys(address, api_key):
    """Extract and compress public keys from transaction data."""
    try:
        address_data = get_address_data(address, api_key)
        found_public_keys = set()  # To store unique public keys

        if 'txrefs' not in address_data:
            return found_public_keys

        for txref in address_data['txrefs']:
            tx_hash = txref['tx_hash']
            full_tx_data = get_full_transaction_data(tx_hash, api_key)

            for inp in full_tx_data['inputs']:
                if 'addresses' in inp and address in inp['addresses']:
                    if 'script' in inp:
                        public_key = extract_public_key_from_script(inp['script'])
                        if public_key:
                            found_public_keys.add(public_key)

        return found_public_keys

    except Exception as e:
        print(f"Error processing address {address}: {e}")
        return set()

def main():
    api_key = input("Enter your BlockCypher API key: ")

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
            public_keys = extract_and_compress_public_keys(address, api_key)

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
