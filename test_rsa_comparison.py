"""
RSA Encryption Performance Test - Comparable to Fernet Testing
Tests write operations with and without RSA encryption for 10KB and 100KB files.
"""

import time
import rsa
import tempfile
import os

def test_no_encryption(data_size_kb, num_iterations=10):
    """Baseline: Test write/read without any encryption."""
    content = "X" * (data_size_kb * 1024)
    content_bytes = content.encode('utf-8')
    
    times = []
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        for i in range(num_iterations):
            start = time.time()
            
            # Write (simulating storage operation)
            with open(tmp_path, 'wb') as f:
                f.write(content_bytes)
            
            # Read (simulating retrieval)
            with open(tmp_path, 'rb') as f:
                data = f.read()
            
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        return avg_time
    finally:
        os.unlink(tmp_path)

def test_with_rsa_encryption(data_size_kb, key_size, num_iterations=10):
    """Test write/read with RSA encryption."""
    max_chunk_size = (key_size // 8) - 11
    content = "X" * (data_size_kb * 1024)
    content_bytes = content.encode('utf-8')
    
    # Generate keys (one-time cost, amortized)
    print(f"  Generating RSA-{key_size} keys...", end=" ")
    key_gen_start = time.time()
    (public_key, private_key) = rsa.newkeys(key_size)
    key_gen_time = time.time() - key_gen_start
    print(f"{key_gen_time:.4f}s")
    
    times = []
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        for i in range(num_iterations):
            start = time.time()
            
            # Write with encryption
            encrypted_chunks = []
            for j in range(0, len(content_bytes), max_chunk_size):
                chunk = content_bytes[j:j + max_chunk_size]
                encrypted_chunk = rsa.encrypt(chunk, public_key)
                encrypted_chunks.append(encrypted_chunk)
            
            # Store encrypted data
            with open(tmp_path, 'wb') as f:
                for chunk in encrypted_chunks:
                    f.write(chunk)
            
            # Read and decrypt
            with open(tmp_path, 'rb') as f:
                encrypted_data = f.read()
            
            # Decrypt chunks
            chunk_size = key_size // 8  # Size of encrypted chunks
            decrypted_parts = []
            for j in range(0, len(encrypted_data), chunk_size):
                encrypted_chunk = encrypted_data[j:j + chunk_size]
                if encrypted_chunk:
                    decrypted_chunk = rsa.decrypt(encrypted_chunk, private_key)
                    decrypted_parts.append(decrypted_chunk)
            
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        return avg_time, key_gen_time
    finally:
        os.unlink(tmp_path)

def run_comparison_test():
    """Run comparison test similar to Fernet testing."""
    print("=" * 80)
    print("RSA ENCRYPTION PERFORMANCE TEST")
    print("Comparing write/read operations with and without encryption")
    print("=" * 80)
    
    file_sizes = [10, 100]  # KB
    iterations = 10
    
    print(f"\nTest parameters:")
    print(f"  - File sizes: {file_sizes} KB")
    print(f"  - Iterations per test: {iterations}")
    print(f"  - Averaging results across iterations\n")
    
    results = {}
    
    # Test 1: No Encryption (Baseline)
    print("\n" + "=" * 80)
    print("TEST 1: NO ENCRYPTION (Baseline)")
    print("=" * 80)
    
    results['no_encryption'] = {}
    for size in file_sizes:
        print(f"\nTesting {size}KB file...")
        avg_time = test_no_encryption(size, iterations)
        results['no_encryption'][size] = avg_time
        print(f"  Average time: {avg_time:.6f} seconds")
    
    # Test 2: RSA-2048 Encryption
    print("\n" + "=" * 80)
    print("TEST 2: RSA-2048 ENCRYPTION")
    print("=" * 80)
    
    results['rsa_2048'] = {}
    for size in file_sizes:
        print(f"\nTesting {size}KB file...")
        avg_time, key_gen_time = test_with_rsa_encryption(size, 2048, iterations)
        results['rsa_2048'][size] = avg_time
        print(f"  Average time: {avg_time:.6f} seconds (excluding key generation)")
    
    # Test 3: RSA-4096 Encryption (optional, slower)
    print("\n" + "=" * 80)
    print("TEST 3: RSA-4096 ENCRYPTION")
    print("=" * 80)
    
    results['rsa_4096'] = {}
    for size in file_sizes:
        print(f"\nTesting {size}KB file...")
        avg_time, key_gen_time = test_with_rsa_encryption(size, 4096, iterations)
        results['rsa_4096'][size] = avg_time
        print(f"  Average time: {avg_time:.6f} seconds (excluding key generation)")
    
    # Summary Table
    print("\n" + "=" * 80)
    print("SUMMARY - AVERAGE WRITE/READ TIME")
    print("=" * 80)
    print(f"\n{'Operation':<30} {'10KB':<20} {'100KB':<20}")
    print("-" * 70)
    
    print(f"{'No Encryption (baseline)':<30} "
          f"{results['no_encryption'][10]:.6f}s{'':<10} "
          f"{results['no_encryption'][100]:.6f}s")
    
    print(f"{'RSA-2048 Encryption':<30} "
          f"{results['rsa_2048'][10]:.6f}s{'':<10} "
          f"{results['rsa_2048'][100]:.6f}s")
    
    print(f"{'RSA-4096 Encryption':<30} "
          f"{results['rsa_4096'][10]:.6f}s{'':<10} "
          f"{results['rsa_4096'][100]:.6f}s")
    
    # Performance Overhead
    print("\n" + "=" * 80)
    print("PERFORMANCE OVERHEAD (vs No Encryption)")
    print("=" * 80)
    print(f"\n{'Operation':<30} {'10KB':<20} {'100KB':<20}")
    print("-" * 70)
    
    for size in file_sizes:
        baseline = results['no_encryption'][size]
        
        overhead_2048 = ((results['rsa_2048'][size] - baseline) / baseline) * 100
        overhead_4096 = ((results['rsa_4096'][size] - baseline) / baseline) * 100
        
        if size == 10:
            print(f"{'RSA-2048':<30} +{overhead_2048:.1f}%{'':<15}", end="")
        else:
            print(f"+{overhead_2048:.1f}%")
        
        if size == 10:
            print(f"{'RSA-4096':<30} +{overhead_4096:.1f}%{'':<15}", end="")
        else:
            print(f"+{overhead_4096:.1f}%")
    
    print("\n" + "=" * 80)
    print("COMPARISON WITH FERNET (for your report):")
    print("-" * 80)
    print("Format your friend's Fernet results like this for comparison:")
    print(f"\n{'Operation':<30} {'10KB':<20} {'100KB':<20}")
    print("-" * 70)
    print(f"{'Fernet Encryption':<30} {'[insert time]':<20} {'[insert time]':<20}")
    print(f"{'RSA-2048 Encryption':<30} "
          f"{results['rsa_2048'][10]:.6f}s{'':<10} "
          f"{results['rsa_2048'][100]:.6f}s")
    print("\nNote: Fernet uses symmetric encryption (faster) vs RSA asymmetric (slower)")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    run_comparison_test()
