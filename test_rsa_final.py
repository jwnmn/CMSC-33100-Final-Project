"""
RSA Encryption Performance Test - Matching Friend's Fernet Format
Tests: Write and Rollback operations (Read from Redis not tested separately)
"""

import time
import rsa
import base64

class SimpleVersionStorage:
    """Simulates LSFS Redis version storage for testing."""
    
    def __init__(self, use_encryption=False):
        self.use_encryption = use_encryption
        self.versions = {}  # file_path -> list of versions
        
        if use_encryption:
            self.public_key, self.private_key = rsa.newkeys(2048)
            self.key_size = 2048
    
    def _encrypt(self, content):
        """Encrypt content in chunks."""
        if not self.use_encryption:
            return content
        
        max_chunk_size = (self.key_size // 8) - 11
        content_bytes = content.encode('utf-8')
        encrypted_chunks = []
        
        for i in range(0, len(content_bytes), max_chunk_size):
            chunk = content_bytes[i:i + max_chunk_size]
            encrypted_chunk = rsa.encrypt(chunk, self.public_key)
            encrypted_chunks.append(base64.b64encode(encrypted_chunk).decode('utf-8'))
        
        return '|||'.join(encrypted_chunks)
    
    def _decrypt(self, encrypted_content):
        """Decrypt content from chunks."""
        if not self.use_encryption:
            return encrypted_content
        
        encrypted_chunks = encrypted_content.split('|||')
        decrypted_parts = []
        
        for chunk in encrypted_chunks:
            if chunk:
                encrypted_data = base64.b64decode(chunk.encode('utf-8'))
                decrypted_parts.append(rsa.decrypt(encrypted_data, self.private_key))
        
        return b''.join(decrypted_parts).decode('utf-8')
    
    def write_version(self, file_path, content):
        """Write a new version (simulates file write + Redis storage)."""
        if file_path not in self.versions:
            self.versions[file_path] = []
        
        encrypted = self._encrypt(content)
        self.versions[file_path].insert(0, encrypted)  # New version at front
    
    def rollback(self, file_path, version_index=1):
        """Rollback to a previous version (simulates LSFS rollback)."""
        if file_path not in self.versions or len(self.versions[file_path]) <= version_index:
            return None
        
        encrypted_content = self.versions[file_path][version_index]
        return self._decrypt(encrypted_content)

def test_write(storage, data_size_kb, num_iterations=10):
    """Test writing files to Redis."""
    content = "X" * (data_size_kb * 1024)
    times = []
    
    for i in range(num_iterations):
        start = time.time()
        storage.write_version(f"test_{data_size_kb}_{i}.txt", content)
        times.append(time.time() - start)
    
    return sum(times) / len(times)

def test_rollback(storage, data_size_kb, num_iterations=10):
    """Test rollback (retrieving and decrypting from Redis)."""
    content = "X" * (data_size_kb * 1024)
    file_path = f"rollback_{data_size_kb}.txt"
    
    # Create 5 versions in Redis first
    for i in range(5):
        storage.write_version(file_path, content)
    
    times = []
    for i in range(num_iterations):
        start = time.time()
        # Retrieve version from Redis and decrypt
        restored = storage.rollback(file_path, version_index=2)
        times.append(time.time() - start)
    
    return sum(times) / len(times)

def run_comparison_test():
    """Run test matching friend's Fernet format."""
    print("=" * 80)
    print("RSA ENCRYPTION PERFORMANCE TEST")
    print("Comparing with Fernet (Write and Rollback operations)")
    print("=" * 80)
    
    file_sizes = [10, 100]
    results = {
        'no_encryption': {},
        'rsa_2048': {}
    }
    
    # Test 1: No Encryption
    print("\n[1/2] Testing WITHOUT encryption...")
    storage_no_enc = SimpleVersionStorage(use_encryption=False)
    
    for size in file_sizes:
        print(f"  {size}KB...", end=" ")
        write_time = test_write(storage_no_enc, size)
        rollback_time = test_rollback(storage_no_enc, size)
        results['no_encryption'][size] = {
            'write': write_time,
            'rollback': rollback_time
        }
        print(f"Write: {write_time:.6f}s, Rollback: {rollback_time:.6f}s")
    
    # Test 2: RSA-2048 Encryption
    print("\n[2/2] Testing WITH RSA-2048 encryption...")
    storage_rsa = SimpleVersionStorage(use_encryption=True)
    
    for size in file_sizes:
        print(f"  {size}KB...", end=" ")
        write_time = test_write(storage_rsa, size)
        rollback_time = test_rollback(storage_rsa, size)
        results['rsa_2048'][size] = {
            'write': write_time,
            'rollback': rollback_time
        }
        print(f"Write: {write_time:.6f}s, Rollback: {rollback_time:.6f}s")
    
    # Summary Table - Format for comparison with Fernet
    print("\n" + "=" * 80)
    print("RESULTS COMPARISON TABLE")
    print("=" * 80)
    
    print(f"\n{'Operation':<25} {'No Encryption':<20} {'Fernet':<20} {'RSA':<20}")
    print("-" * 85)
    
    # 10KB Write
    print(f"{'Write (10KB)':<25} "
          f"{results['no_encryption'][10]['write']:.6f}s{'':<12} "
          f"{'[0.0005s]':<20} "
          f"{results['rsa_2048'][10]['write']:.6f}s")
    
    # 100KB Write
    print(f"{'Write (100KB)':<25} "
          f"{results['no_encryption'][100]['write']:.6f}s{'':<12} "
          f"{'[0.0002s]':<20} "
          f"{results['rsa_2048'][100]['write']:.6f}s")
    
    # Rollback (average of 10KB and 100KB)
    avg_rollback_no_enc = (results['no_encryption'][10]['rollback'] + results['no_encryption'][100]['rollback']) / 2
    avg_rollback_rsa = (results['rsa_2048'][10]['rollback'] + results['rsa_2048'][100]['rollback']) / 2
    
    print(f"{'Rollback':<25} "
          f"{avg_rollback_no_enc:.6f}s{'':<12} "
          f"{'[0.0004s]':<20} "
          f"{avg_rollback_rsa:.6f}s")
    
    # Performance overhead
    print("\n" + "=" * 80)
    print("PERFORMANCE OVERHEAD ANALYSIS")
    print("=" * 80)
    
    print(f"\n{'Operation':<20} {'Overhead vs No Encryption':<40}")
    print("-" * 60)
    
    for size in file_sizes:
        # Write
        write_overhead = ((results['rsa_2048'][size]['write'] - results['no_encryption'][size]['write']) / 
                         results['no_encryption'][size]['write']) * 100
        print(f"Write ({size}KB){'':<10} +{write_overhead:.0f}%")
        
        # Rollback
        rollback_overhead = ((results['rsa_2048'][size]['rollback'] - results['no_encryption'][size]['rollback']) / 
                            results['no_encryption'][size]['rollback']) * 100
        print(f"Rollback ({size}KB){'':<7} +{rollback_overhead:.0f}%")
    
    print("\n" + "=" * 80)
    print("SUMMARY FOR YOUR REPORT")
    print("-" * 80)
    print("• Only Write and Rollback are tested (both use Redis storage)")
    print("• Normal file reads happen from DISK, not Redis (no encryption overhead)")
    print("• Fernet (symmetric) is much faster than RSA (asymmetric)")
    print("• RSA is impractical for file storage due to chunking limitations")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    run_comparison_test()
