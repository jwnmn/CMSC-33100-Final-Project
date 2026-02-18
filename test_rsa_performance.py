"""
Performance benchmarking script for RSA encryption in LSFS.
Tests the impact of RSA encryption on file operations.
"""

import time
import os
import tempfile
import shutil
from aios.storage.filesystem.lsfs import LSFS

def benchmark_write_operations(lsfs, num_files=10, file_size_kb=10):
    """Benchmark file write operations."""
    times = []
    content = "A" * (file_size_kb * 1024)  # Create content of specified size
    
    for i in range(num_files):
        file_path = os.path.join(lsfs.root_dir, f"test_file_{i}.txt")
        
        start = time.time()
        lsfs.sto_write(
            file_name=f"test_file_{i}.txt",
            file_path=file_path,
            content=content
        )
        end = time.time()
        
        times.append(end - start)
    
    return times

def benchmark_rollback_operations(lsfs, num_rollbacks=5):
    """Benchmark file rollback operations."""
    times = []
    test_file = os.path.join(lsfs.root_dir, "rollback_test.txt")
    
    # Create file with multiple versions
    for i in range(10):
        lsfs.sto_write(
            file_name="rollback_test.txt",
            file_path=test_file,
            content=f"Version {i} content " * 100
        )
        time.sleep(0.1)  # Small delay to ensure different timestamps
    
    # Benchmark rollbacks
    for i in range(num_rollbacks):
        start = time.time()
        lsfs.sto_rollback(test_file, n=i+1)
        end = time.time()
        times.append(end - start)
    
    return times

def run_benchmark(use_encryption, rsa_key_size=2048):
    """Run complete benchmark suite."""
    # Create temporary directory for testing
    temp_dir = tempfile.mkdtemp(prefix="lsfs_benchmark_")
    
    try:
        print(f"\n{'='*60}")
        print(f"Benchmark: Encryption={'ON' if use_encryption else 'OFF'}, Key Size={rsa_key_size if use_encryption else 'N/A'}")
        print(f"{'='*60}\n")
        
        # Initialize LSFS
        init_start = time.time()
        lsfs = LSFS(
            root_dir=temp_dir,
            use_vector_db=False,  # Disable for pure encryption testing
            use_encryption=use_encryption,
            rsa_key_size=rsa_key_size
        )
        init_time = time.time() - init_start
        print(f"Initialization time: {init_time:.4f} seconds\n")
        
        # Test 1: Write operations with small files
        print("Test 1: Writing 10 files (10 KB each)")
        write_times_small = benchmark_write_operations(lsfs, num_files=10, file_size_kb=10)
        avg_write_small = sum(write_times_small) / len(write_times_small)
        print(f"  Average write time: {avg_write_small:.4f} seconds")
        print(f"  Total time: {sum(write_times_small):.4f} seconds\n")
        
        # Test 2: Write operations with medium files
        print("Test 2: Writing 5 files (100 KB each)")
        write_times_medium = benchmark_write_operations(lsfs, num_files=5, file_size_kb=100)
        avg_write_medium = sum(write_times_medium) / len(write_times_medium)
        print(f"  Average write time: {avg_write_medium:.4f} seconds")
        print(f"  Total time: {sum(write_times_medium):.4f} seconds\n")
        
        # Test 3: Rollback operations
        print("Test 3: Rollback operations (5 rollbacks)")
        rollback_times = benchmark_rollback_operations(lsfs, num_rollbacks=5)
        avg_rollback = sum(rollback_times) / len(rollback_times)
        print(f"  Average rollback time: {avg_rollback:.4f} seconds")
        print(f"  Total time: {sum(rollback_times):.4f} seconds\n")
        
        return {
            'init_time': init_time,
            'avg_write_small': avg_write_small,
            'avg_write_medium': avg_write_medium,
            'avg_rollback': avg_rollback,
            'total_write_small': sum(write_times_small),
            'total_write_medium': sum(write_times_medium),
            'total_rollback': sum(rollback_times)
        }
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

def compare_performance():
    """Compare performance with and without encryption."""
    print("\n" + "="*60)
    print("RSA ENCRYPTION PERFORMANCE IMPACT TEST")
    print("="*60)
    
    # Run without encryption
    results_no_encryption = run_benchmark(use_encryption=False)
    
    # Run with encryption (2048-bit key)
    results_2048 = run_benchmark(use_encryption=True, rsa_key_size=2048)
    
    # Optional: Test with larger key size
    results_4096 = run_benchmark(use_encryption=True, rsa_key_size=4096)
    
    # Calculate and display performance impact
    print("\n" + "="*60)
    print("PERFORMANCE COMPARISON")
    print("="*60)
    print(f"\n{'Operation':<30} {'No Encryption':<15} {'RSA-2048':<15} {'RSA-4096':<15} {'Impact 2048':<15} {'Impact 4096':<15}")
    print("-"*105)
    
    def calculate_impact(baseline, encrypted):
        if baseline == 0:
            return "N/A"
        increase = ((encrypted - baseline) / baseline) * 100
        return f"+{increase:.1f}%"
    
    print(f"{'Initialization':<30} {results_no_encryption['init_time']:<15.4f} {results_2048['init_time']:<15.4f} {results_4096['init_time']:<15.4f} {calculate_impact(results_no_encryption['init_time'], results_2048['init_time']):<15} {calculate_impact(results_no_encryption['init_time'], results_4096['init_time']):<15}")
    
    print(f"{'Write (10KB avg)':<30} {results_no_encryption['avg_write_small']:<15.4f} {results_2048['avg_write_small']:<15.4f} {results_4096['avg_write_small']:<15.4f} {calculate_impact(results_no_encryption['avg_write_small'], results_2048['avg_write_small']):<15} {calculate_impact(results_no_encryption['avg_write_small'], results_4096['avg_write_small']):<15}")
    
    print(f"{'Write (100KB avg)':<30} {results_no_encryption['avg_write_medium']:<15.4f} {results_2048['avg_write_medium']:<15.4f} {results_4096['avg_write_medium']:<15.4f} {calculate_impact(results_no_encryption['avg_write_medium'], results_2048['avg_write_medium']):<15} {calculate_impact(results_no_encryption['avg_write_medium'], results_4096['avg_write_medium']):<15}")
    
    print(f"{'Rollback (avg)':<30} {results_no_encryption['avg_rollback']:<15.4f} {results_2048['avg_rollback']:<15.4f} {results_4096['avg_rollback']:<15.4f} {calculate_impact(results_no_encryption['avg_rollback'], results_2048['avg_rollback']):<15} {calculate_impact(results_no_encryption['avg_rollback'], results_4096['avg_rollback']):<15}")
    
    print("\n" + "="*60)
    print("Notes:")
    print("- RSA encryption is applied to Redis version history only")
    print("- Files on disk remain unencrypted for compatibility")
    print("- Larger key sizes provide more security but slower performance")
    print("- Impact percentages show performance overhead")
    print("="*60 + "\n")

if __name__ == "__main__":
    compare_performance()
