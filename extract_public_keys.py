import os
from blockcypher import get_address_full

# File containing addresses, one per line
address_file = 'address.txt'
# Output file to save the public keys
output_file = 'public_keys.txt'

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
        print(f"Unexpected error extracting public key: {e}")
        return None

def extract_and_compress_public_keys(address):
    try:
        # Fetch full address information including transactions
        address_data = get_address_full(address)
        found_public_keys = set()  # To store unique public keys

        # Check if 'txs' is in the data
        if 'txs' not in address_data:
            return found_public_keys

        # Iterate over transactions to find spent outputs
        for tx in address_data['txs']:
            for input in tx['inputs']:
                if 'addresses' in input and address in input['addresses']:
                    # Extract the public key from the scriptSig if available
                    if 'script' in input:
                        public_key = extract_public_key_from_script(input['script'])
                        if public_key:
                            found_public_keys.add(public_key)
        return found_public_keys

    except Exception as e:
        print(f"Error processing address {address}: {e}")
        return set()

def main():
    if not os.path.exists(address_file):
        print(f"The file {address_file} does not exist.")
        return

    with open(address_file, 'r') as f:
        addresses = [line.strip() for line in f if line.strip()]

    with open(output_file, 'w') as out_file:
        for address in addresses:
            if not address:  # Skip empty lines
                continue

            print(f"Processing address: {address}")
            public_keys = extract_and_compress_public_keys(address)

            if public_keys:
                print(f"Public key found for address: {address}")
                for pk in public_keys:
                    out_file.write(f"{pk}\n")
            else:
                print(f"No public key found for address: {address}")

    print(f"Public keys have been written to {output_file}")

if __name__ == "__main__":
    main()
