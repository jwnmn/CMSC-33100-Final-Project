"""
RSA vs No Encryption - Clean Comparison Test
For direct comparison with Fernet results
"""

import time
import rsa
import tempfile
import os

def test_no_encryption(data_size_kb, num_iterations=10):
    """Baseline: Write/read without encryption."""
    content = "X" * (data_size_kb * 1024)
    content_bytes = content.encode('utf-8')
    
    times = []
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        for i in range(num_iterations):
            start = time.time()
            with open(tmp_path, 'wb') as f:
                f.write(content_bytes)
            with open(tmp_path, 'rb') as f:
                data = f.read()
            times.append(time.time() - start)
        
        return sum(times) / len(times)
    finally:
        os.unlink(tmp_path)

def test_with_rsa(data_size_kb, num_iterations=10):
    """Write/read with RSA-2048 encryption."""
    key_size = 2048
    max_chunk_size = (key_size // 8) - 11
    content = "X" * (data_size_kb * 1024)
    content_bytes = content.encode('utf-8')
    
    # Generate keys once
    (public_key, private_key) = rsa.newkeys(key_size)
    
    times = []
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        for i in range(num_iterations):
            start = time.time()
            
            # Encrypt and write
            encrypted_chunks = []
            for j in range(0, len(content_bytes), max_chunk_size):
                chunk = content_bytes[j:j + max_chunk_size]
                encrypted_chunks.append(rsa.encrypt(chunk, public_key))
            
            with open(tmp_path, 'wb') as f:
                for chunk in encrypted_chunks:
                    f.write(chunk)
            
            # Read and decrypt
            with open(tmp_path, 'rb') as f:
                encrypted_data = f.read()
            
            chunk_size = key_size // 8
            decrypted_parts = []
            for j in range(0, len(encrypted_data), chunk_size):
                encrypted_chunk = encrypted_data[j:j + chunk_size]
                if encrypted_chunk:
                    decrypted_parts.append(rsa.decrypt(encrypted_chunk, private_key))
            
            times.append(time.time() - start)
        
        return sum(times) / len(times)
    finally:
        os.unlink(tmp_path)

print("=" * 70)
print("ENCRYPTION PERFORMANCE COMPARISON")
print("=" * 70)

file_sizes = [10, 100]
results = {}

# Test both sizes
for size in file_sizes:
    print(f"\nTesting {size}KB files...")
    no_enc = test_no_encryption(size)
    rsa_enc = test_with_rsa(size)
    results[size] = {'no_enc': no_enc, 'rsa': rsa_enc}
    print(f"  No encryption: {no_enc:.6f}s")
    print(f"  RSA-2048:     {rsa_enc:.6f}s")

# Summary table
print("\n" + "=" * 70)
print("RESULTS FOR YOUR REPORT")
print("=" * 70)
print(f"\n{'Method':<25} {'Write 10KB':<20} {'Write 100KB':<20}")
print("-" * 65)
print(f"{'No Encryption':<25} {results[10]['no_enc']:.6f}s{'':<12} {results[100]['no_enc']:.6f}s")
print(f"{'RSA-2048':<25} {results[10]['rsa']:.6f}s{'':<12} {results[100]['rsa']:.6f}s")
fernet_label = "Fernet (friend data)"
friend_data = "[your friend's]"
print(f"{fernet_label:<25} {friend_data:<20} {friend_data:<20}")

print("\n" + "=" * 70)
print("OVERHEAD ANALYSIS")
print("=" * 70)
for size in file_sizes:
    overhead = ((results[size]['rsa'] - results[size]['no_enc']) / results[size]['no_enc']) * 100
    slowdown = results[size]['rsa'] / results[size]['no_enc']
    print(f"{size}KB: RSA-2048 is {slowdown:.1f}x slower (+{overhead:.0f}% overhead)")

print("\n" + "=" * 70)
