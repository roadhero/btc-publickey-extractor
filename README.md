# Bitcoin Public Key Extractor

This Python script extracts unique Bitcoin public keys from a list of addresses. It connects to the BlockCypher API to retrieve transaction data for each address and identifies the public keys involved in the transactions. The script ensures that each public key is listed only once per address, regardless of the number of transactions.

## Overview

### Features
- Extracts public keys from Bitcoin addresses that have made transactions.
- Identifies and processes both compressed and uncompressed public keys.
- Ensures each public key is listed only once, even if associated with multiple transactions.
- Outputs the public keys in a simple text file.

## Prerequisites

### Python
- Ensure Python 3 is installed on your system. You can verify this by running:

```python3 --version```

### Required Python Packages
blockcypher: This library is used to interact with the BlockCypher API to fetch transaction data. To install the necessary packages, run the following command:

```pip3 install blockcypher```

This will install the blockcypher library, which is required for the script to function correctly.

## Getting Started

### Step 1: Clone the Repository

```git clone https://github.com/yourusername/bitcoin-public-key-extractor.git```

```cd bitcoin-public-key-extractor```

### Step 2: Prepare the Input File

Create a file named address.txt in the same directory as the script. This file should contain a list of Bitcoin addresses, one per line. For example:

```1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH```

### Step 3: Run the Script

Run the script using Python 3:

```python3 extract_public_keys.py```

### Step 4: View the Output

After running the script, a file named public_keys.txt will be generated in the same directory. This file will contain the unique public keys extracted from the provided Bitcoin addresses, one per line.

Example Output:

```0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798```

## Troubleshooting

If you encounter any issues, ensure the following:

- The address.txt file exists and is correctly formatted.
- The blockcypher package is installed correctly.
- The Bitcoin addresses provided have associated transactions with public keys that can be extracted.

## Acknowledgments
BlockCypher for their robust API
