import os
import time
import random
import requests
import sys
from multiprocessing import Pool, TimeoutError

# File containing addresses, one per line
address_file = 'address.txt'
# Output file to save the public keys
output_file = 'public_keys.txt'
# Maximum number of retries after hitting rate limit
max_retries = 5
# Time limit for processing each address (in seconds)
processing_timeout = 15

# Manually define the BlockCypher API base URL
BASE_URL = "https://api.blockcypher.com/v1/btc/main"
# Time to wait between requests (in seconds)
request_delay = 1  # Adjust this as needed to avoid hitting rate limits

# URLs of the proxy lists on GitHub
proxy_urls = {
    'http': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
    'socks4': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt',
    'socks5': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt'
}

def fetch_proxies():
    """Fetch proxy lists from GitHub and combine them."""
    combined_proxies = []
    for proxy_type, url in proxy_urls.items():
        try:
            response = requests.get(url)
            response.raise_for_status()
            proxies = response.text.splitlines()
            combined_proxies.extend([(proxy, proxy_type) for proxy in proxies])
            print(f"Fetched {len(proxies)} {proxy_type.upper()} proxies")
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch {proxy_type.upper()} proxies: {e}")
    return combined_proxies

def test_proxy(proxy, proxy_type):
    """Test if a proxy is alive."""
    test_url = 'https://httpbin.org/ip'
    proxies = {
        'http': f'{proxy_type}://{proxy}',
        'https': f'{proxy_type}://{proxy}'
    }
    try:
        response = requests.get(test_url, proxies=proxies, timeout=5)
        if response.status_code == 200:
            return True
    except Exception:
        return False

def get_random_alive_proxy(proxies):
    """Randomly pick and test an alive proxy from the list."""
    print("Searching for a proxy", end="")
    animation = ["   ", ".  ", ".. ", "..."]
    animation_index = 0

    while proxies:
        proxy, proxy_type = random.choice(proxies)
        proxies.remove((proxy, proxy_type))  # Remove it from the list to avoid re-testing
        if test_proxy(proxy, proxy_type):
            print("\nProxy found.")
            return {'http': f'{proxy_type}://{proxy}', 'https': f'{proxy_type}://{proxy}'}

        # Display animation
        sys.stdout.write("\r" + "Searching for a proxy" + animation[animation_index % len(animation)])
        sys.stdout.flush()
        animation_index += 1
        time.sleep(0.5)

    print("\nNo alive proxies found.")
    return None

def fetch_with_rate_limiting(url, params=None, proxy=None):
    """Fetch data from the BlockCypher API with rate limiting."""
    retries = 0

    while retries < max_retries:
        try:
            response = requests.get(url, params=params, proxies=proxy, timeout=processing_timeout)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                print(f"Rate limit exceeded with proxy {proxy}.")
                return None  # Return None to indicate rate limiting
            else:
                response.raise_for_status()
        except requests.exceptions.ProxyError:
            print(f"Proxy error with {proxy}. Retrying with a new proxy...")
            return None  # Return None to switch proxy
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}. Retrying...")
            retries += 1

    raise Exception("Max retries exceeded for API request.")

def get_address_data(address, proxy=None):
    """Get address data with rate limiting."""
    url = f"{BASE_URL}/addrs/{address}"
    data = fetch_with_rate_limiting(url, proxy=proxy)
    if data:
        time.sleep(request_delay)  # Introduce a delay between requests
    return data

def get_full_transaction_data(tx_hash, proxy=None):
    """Get full transaction data by hash."""
    url = f"{BASE_URL}/txs/{tx_hash}"
    data = fetch_with_rate_limiting(url, proxy=proxy)
    if data:
        time.sleep(request_delay)  # Introduce a delay between requests
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
    except IndexError:
        return None
    except Exception as e:
        return None

def extract_and_compress_public_keys(address, proxy=None):
    try:
        # Fetch address data
        address_data = get_address_data(address, proxy)
        if not address_data:  # If rate-limited or failed, return immediately
            return None

        found_public_keys = set()  # To store unique public keys

        # Check if 'txrefs' is in the data
        if 'txrefs' not in address_data:
            return found_public_keys

        # Retrieve and process each full transaction
        for txref in address_data['txrefs']:
            tx_hash = txref['tx_hash']
            full_tx_data = get_full_transaction_data(tx_hash, proxy)
            if not full_tx_data:  # If rate-limited or failed, return immediately
                return None

            # Process each input in the transaction
            for input in full_tx_data['inputs']:
                if 'addresses' in input and address in input['addresses']:
                    if 'script' in input:
                        public_key = extract_public_key_from_script(input['script'])
                        if public_key:
                            found_public_keys.add(public_key)

        return found_public_keys

    except Exception as e:
        return None

def process_address(address, proxy):
    """Wrapper function to process an address within a timeout limit."""
    return extract_and_compress_public_keys(address, proxy)

def main():
    if not os.path.exists(address_file):
        print(f"The file {address_file} does not exist.")
        return

    # Fetch and validate proxies
    proxies = fetch_proxies()

    found_keys = []
    not_found_keys = []
    proxy = get_random_alive_proxy(proxies)  # Get the first random alive proxy

    with open(address_file, 'r') as f:
        addresses = [line.strip() for line in f if line.strip()]

    with open(output_file, 'w') as out_file:
        for address in addresses:
            if not address:  # Skip empty lines
                continue

            print(f"Processing address: {address}")

            while True:  # Keep trying until we process the address
                with Pool(1) as p:
                    result = p.apply_async(process_address, (address, proxy))

                    try:
                        public_keys = result.get(timeout=processing_timeout)
                    except TimeoutError:
                        print(f"Processing timed out for address: {address}. Switching proxy.")
                        public_keys = None

                if public_keys is None:
                    proxy = get_random_alive_proxy(proxies)
                    if not proxy:
                        print("No more alive proxies available.")
                        break  # Exit the loop if no more proxies are available
                    continue  # Retry with the new proxy

                if public_keys:
                    print(f"Public key found for address: {address}")
                    found_keys.append(address)
                    for pk in public_keys:
                        out_file.write(f"{pk}\n")
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
