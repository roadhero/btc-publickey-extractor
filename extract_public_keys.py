import os
from blockcypher import get_address_full

# File containing addresses, one per line
address_file = 'address.txt'
# Output file to save the public keys
output_file = 'public_keys.txt'

def extract_public_key_from_script(script):
    # A public key in a script is usually at the end, right before the signature
    # Assuming it's not already extracted directly, we'll take the last 66/130 characters if uncompressed/compressed
    # Usually, the public key in a script is 33 bytes (compressed) or 65 bytes (uncompressed)
    # We focus on valid pubkey formats (starts with 02, 03, or 04)
    
    if len(script) >= 66 and (script[-66:][:2] == '02' or script[-66:][:2] == '03'):
        return script[-66:]  # Compressed public key
    elif len(script) >= 130 and script[-130:][:2] == '04':
        return script[-130:]  # Uncompressed public key
    else:
        return None

def extract_and_compress_public_keys(address):
    try:
        # Fetch full address information including transactions
        address_data = get_address_full(address)

        found_public_keys = set()  # To store unique public keys

        # Iterate over transactions to find spent outputs
        for tx in address_data['txs']:
            for input in tx['inputs']:
                if input['addresses'][0] == address:
                    # Extract the public key from the scriptSig if available
                    if 'script' in input:
                        public_key = extract_public_key_from_script(input['script'])
                        if public_key and public_key not in found_public_keys:
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
        addresses = f.read().splitlines()

    with open(output_file, 'w') as out_file:
        for address in addresses:
            public_keys = extract_and_compress_public_keys(address)
            for pk in public_keys:
                out_file.write(f"{pk}\n")

    print(f"Public keys have been written to {output_file}")

if __name__ == "__main__":
    main()
