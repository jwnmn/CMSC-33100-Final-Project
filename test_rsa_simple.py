"""
Minimal RSA encryption performance test without full LSFS dependencies.
Tests raw RSA encryption/decryption performance.
"""

import time
import rsa

def test_rsa_key_generation(key_size):
    """Test RSA key generation time."""
    print(f"\nGenerating RSA-{key_size} keys...")
    start = time.time()
    (public_key, private_key) = rsa.newkeys(key_size)
    elapsed = time.time() - start
    print(f"  Time: {elapsed:.4f} seconds")
    return public_key, private_key

def test_encryption_decryption(public_key, private_key, data_size_kb, key_size):
    """Test encryption and decryption performance."""
    # RSA can only encrypt data smaller than the key size
    max_chunk_size = (key_size // 8) - 11
    
    # Create test data
    content = "X" * (data_size_kb * 1024)
    content_bytes = content.encode('utf-8')
    
    print(f"\nTesting {data_size_kb}KB data encryption/decryption:")
    print(f"  Data size: {len(content_bytes)} bytes")
    print(f"  Max chunk size: {max_chunk_size} bytes")
    print(f"  Number of chunks: {(len(content_bytes) + max_chunk_size - 1) // max_chunk_size}")
    
    # Encryption
    start = time.time()
    encrypted_chunks = []
    for i in range(0, len(content_bytes), max_chunk_size):
        chunk = content_bytes[i:i + max_chunk_size]
        encrypted_chunk = rsa.encrypt(chunk, public_key)
        encrypted_chunks.append(encrypted_chunk)
    encryption_time = time.time() - start
    print(f"  Encryption time: {encryption_time:.4f} seconds")
    
    # Decryption
    start = time.time()
    decrypted_parts = []
    for encrypted_chunk in encrypted_chunks:
        decrypted_chunk = rsa.decrypt(encrypted_chunk, private_key)
        decrypted_parts.append(decrypted_chunk)
    decryption_time = time.time() - start
    print(f"  Decryption time: {decryption_time:.4f} seconds")
    print(f"  Total time: {encryption_time + decryption_time:.4f} seconds")
    
    # Verify
    decrypted_content = b''.join(decrypted_parts).decode('utf-8')
    assert decrypted_content == content, "Decryption failed!"
    
    return encryption_time, decryption_time

def run_benchmark(key_size, test_sizes=[1, 10, 50]):
    """Run complete benchmark for a given key size."""
    print("=" * 70)
    print(f"RSA-{key_size} PERFORMANCE BENCHMARK")
    print("=" * 70)
    
    # Generate keys
    public_key, private_key = test_rsa_key_generation(key_size)
    
    results = []
    for size_kb in test_sizes:
        enc_time, dec_time = test_encryption_decryption(
            public_key, private_key, size_kb, key_size
        )
        results.append({
            'size_kb': size_kb,
            'encryption': enc_time,
            'decryption': dec_time,
            'total': enc_time + dec_time
        })
    
    return results

def compare_key_sizes():
    """Compare performance across different RSA key sizes."""
    print("\n" + "=" * 70)
    print("RSA ENCRYPTION PERFORMANCE COMPARISON")
    print("=" * 70)
    
    test_sizes = [1, 10, 50]  # KB
    
    print("\nRunning benchmarks (this may take several minutes)...\n")
    
    results_1024 = run_benchmark(1024, test_sizes)
    results_2048 = run_benchmark(2048, test_sizes)
    results_4096 = run_benchmark(4096, test_sizes)
    
    # Summary table
    print("\n" + "=" * 70)
    print("SUMMARY - Total Time (Encryption + Decryption)")
    print("=" * 70)
    print(f"\n{'Data Size':<15} {'RSA-1024':<15} {'RSA-2048':<15} {'RSA-4096':<15}")
    print("-" * 60)
    
    for i, size_kb in enumerate(test_sizes):
        print(f"{size_kb:>3} KB {'':<9} "
              f"{results_1024[i]['total']:>8.4f}s      "
              f"{results_2048[i]['total']:>8.4f}s      "
              f"{results_4096[i]['total']:>8.4f}s")
    
    # Performance overhead comparison
    print("\n" + "=" * 70)
    print("PERFORMANCE OVERHEAD (vs RSA-1024)")
    print("=" * 70)
    print(f"\n{'Data Size':<15} {'RSA-2048':<20} {'RSA-4096':<20}")
    print("-" * 55)
    
    for i, size_kb in enumerate(test_sizes):
        baseline = results_1024[i]['total']
        overhead_2048 = ((results_2048[i]['total'] - baseline) / baseline) * 100
        overhead_4096 = ((results_4096[i]['total'] - baseline) / baseline) * 100
        print(f"{size_kb:>3} KB {'':<9} "
              f"+{overhead_2048:>6.1f}% slower      "
              f"+{overhead_4096:>6.1f}% slower")
    
    print("\n" + "=" * 70)
    print("KEY INSIGHTS:")
    print("-" * 70)
    print("• Larger key sizes provide better security but slower performance")
    print("• RSA-2048 is the current recommended minimum for production")
    print("• Performance degrades significantly with larger data (more chunks)")
    print("• Each chunk requires a separate RSA operation")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    compare_key_sizes()
