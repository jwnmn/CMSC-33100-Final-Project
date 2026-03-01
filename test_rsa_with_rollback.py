"""
Complete RSA Performance Test - Matching Friend's Fernet Format
Tests: Write, Read, and Rollback operations with 10KB and 100KB files
"""

import time
import rsa
import tempfile
import os
import json

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
            # Base64 encode like in LSFS
            import base64
            encrypted_chunks.append(base64.b64encode(encrypted_chunk).decode('utf-8'))
        
        # Join with delimiter (as string)
        return '|||'.join(encrypted_chunks)
    
    def _decrypt(self, encrypted_content):
        """Decrypt content from chunks."""
        if not self.use_encryption:
            return encrypted_content
        
        import base64
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
    """Test writing files."""
    content = "X" * (data_size_kb * 1024)
    times = []
    
    for i in range(num_iterations):
        start = time.time()
        storage.write_version(f"test_{data_size_kb}.txt", content)
        times.append(time.time() - start)
    
    return sum(times) / len(times)

def test_rollback(storage, data_size_kb, num_iterations=10):
    """Test rollback (retrieving and decrypting old version)."""
    content = "X" * (data_size_kb * 1024)
    file_path = f"rollback_{data_size_kb}.txt"
    
    # Create 5 versions first (same content for consistency)
    for i in range(5):
        storage.write_version(file_path, content)
    
    times = []
    for i in range(num_iterations):
        start = time.time()
        restored = storage.rollback(file_path, version_index=2)
        times.append(time.time() - start)
    
    return sum(times) / len(times)

def run_complete_test():
    """Run complete test matching Fernet format."""
    print("=" * 75)
    print("RSA ENCRYPTION PERFORMANCE TEST")
    print("Testing Write and Rollback operations")
    print("=" * 75)
    
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
    
    # Summary Table - Format for your report
    print("\n" + "=" * 75)
    print("RESULTS TABLE (for comparison with Fernet)")
    print("=" * 75)
    
    # Write operations
    print(f"\n{'WRITE Operations':<30} {'10KB':<20} {'100KB':<20}")
    print("-" * 70)
    print(f"{'No Encryption':<30} "
          f"{results['no_encryption'][10]['write']:.6f}s{'':<12} "
          f"{results['no_encryption'][100]['write']:.6f}s")
    print(f"{'RSA-2048':<30} "
          f"{results['rsa_2048'][10]['write']:.6f}s{'':<12} "
          f"{results['rsa_2048'][100]['write']:.6f}s")
    print(f"{'Fernet (your friend)':<30} {'[insert here]':<20} {'[insert here]':<20}")
    
    # Rollback operations
    print(f"\n{'ROLLBACK Operations':<30} {'10KB':<20} {'100KB':<20}")
    print("-" * 70)
    print(f"{'No Encryption':<30} "
          f"{results['no_encryption'][10]['rollback']:.6f}s{'':<12} "
          f"{results['no_encryption'][100]['rollback']:.6f}s")
    print(f"{'RSA-2048':<30} "
          f"{results['rsa_2048'][10]['rollback']:.6f}s{'':<12} "
          f"{results['rsa_2048'][100]['rollback']:.6f}s")
    print(f"{'Fernet (your friend)':<30} {'[insert here]':<20} {'[insert here]':<20}")
    
    # Performance overhead
    print("\n" + "=" * 75)
    print("RSA-2048 OVERHEAD (compared to no encryption)")
    print("=" * 75)
    
    print(f"\n{'Operation':<20} {'10KB Slowdown':<25} {'100KB Slowdown':<25}")
    print("-" * 70)
    
    for op in ['write', 'rollback']:
        overhead_10 = results['rsa_2048'][10][op] / results['no_encryption'][10][op]
        overhead_100 = results['rsa_2048'][100][op] / results['no_encryption'][100][op]
        
        op_name = op.capitalize()
        print(f"{op_name:<20} {overhead_10:.1f}x slower{'':<14} {overhead_100:.1f}x slower")
    
    print("\n" + "=" * 75)
    print("WHAT IS ROLLBACK?")
    print("-" * 75)
    print("Rollback = Restoring a file to a previous version from storage")
    print("  - In LSFS: Retrieves old version from Redis and restores it")
    print("  - With encryption: Must decrypt the old version")
    print("  - Tests read + decrypt performance for version history")
    print("=" * 75 + "\n")

if __name__ == "__main__":
    run_complete_test()
