# RSA Encryption in LSFS - Performance Testing Guide

## Overview

RSA encryption has been added to the LSFS (Local Storage File System) to enable performance impact testing. This implementation encrypts file version history stored in Redis while keeping files on disk unencrypted for compatibility.

## Installation

First, install the required dependencies:

```bash
pip install -r requirements.txt
```

Or install just the RSA package:

```bash
pip install rsa>=4.9
```

**Note:** Ensure Redis is running before using LSFS with encryption.

## Usage

### Basic Usage

```python
from aios.storage.filesystem.lsfs import LSFS

# Without encryption (baseline)
lsfs_no_encryption = LSFS(
    root_dir="/path/to/directory",
    use_encryption=False
)

# With encryption (RSA-2048)
lsfs_encrypted = LSFS(
    root_dir="/path/to/directory",
    use_encryption=True,
    rsa_key_size=2048
)

# With larger key size (RSA-4096) for higher security
lsfs_encrypted_4096 = LSFS(
    root_dir="/path/to/directory",
    use_encryption=True,
    rsa_key_size=4096
)
```

### Parameters

- **`use_encryption`** (bool): Enable/disable RSA encryption (default: `False`)
- **`rsa_key_size`** (int): RSA key size in bits - common values: 1024, 2048, 4096 (default: `2048`)
- **`use_vector_db`** (bool): Enable vector database for search (default: `True`)
- **`max_versions`** (int): Maximum number of versions to keep in Redis (default: `20`)

## Performance Testing

Run the provided benchmark script to measure performance impact:

```bash
python test_rsa_performance.py
```

This script will:
1. Test operations **without encryption** (baseline)
2. Test with **RSA-2048** encryption
3. Test with **RSA-4096** encryption
4. Compare and display performance overhead

### Sample Output

```
========================================================
RSA ENCRYPTION PERFORMANCE IMPACT TEST
========================================================

========================================================
Benchmark: Encryption=OFF, Key Size=N/A
========================================================

Initialization time: 0.0123 seconds

Test 1: Writing 10 files (10 KB each)
  Average write time: 0.0456 seconds
  Total time: 0.4560 seconds

... (more results)

========================================================
PERFORMANCE COMPARISON
========================================================

Operation                      No Encryption   RSA-2048        RSA-4096        Impact 2048     Impact 4096    
---------------------------------------------------------------------------------------------------------
Initialization                 0.0123          0.5234          1.2456          +425.1%         +912.3%        
Write (10KB avg)               0.0456          0.2123          0.5234          +365.6%         +1047.8%       
Write (100KB avg)              0.3421          1.5678          3.2134          +358.4%         +839.2%        
Rollback (avg)                 0.0234          0.1234          0.2567          +427.4%         +996.2%        
```

## What Gets Encrypted?

### ✅ Encrypted:
- File content stored in **Redis version history**
- Historical versions of files

### ❌ NOT Encrypted:
- Files stored on **disk** (for compatibility)
- **Vector database** content (for search functionality)

## Implementation Details

### Chunked Encryption
RSA has size limitations based on key size. The implementation automatically:
- Splits large files into chunks
- Encrypts each chunk separately
- Stores chunks with a delimiter (`|||`)
- Decrypts and reassembles on retrieval

### Key Management
- Keys are generated when LSFS is initialized with `use_encryption=True`
- Public key used for encryption
- Private key used for decryption
- Keys are stored in memory (not persisted)

## Security Considerations

⚠️ **Important Notes:**
1. The `rsa` package is **archived** and no longer maintained
2. It's vulnerable to **timing attacks** due to Python's internal number storage
3. This implementation is for **performance testing only**
4. **DO NOT use in production** for sensitive data
5. For production, use the `cryptography` library instead

## Expected Performance Impact

Based on typical results:

| Key Size | Initialization | Write Operations | Rollback | Security Level |
|----------|---------------|------------------|----------|----------------|
| No encryption | Fast | Fast | Fast | None |
| RSA-1024 | Moderate | Moderate | Moderate | Low (deprecated) |
| RSA-2048 | Slow | Slow | Slow | Good |
| RSA-4096 | Very Slow | Very Slow | Very Slow | Better |

**General guidance:**
- RSA-2048: ~300-500% slower than no encryption
- RSA-4096: ~800-1200% slower than no encryption
- Larger files = proportionally more overhead

## Troubleshooting

### Redis Connection Error
```
Failed to connect to Redis: Error connecting to localhost:6379
```

**Solution:** Start Redis server:
```bash
# macOS
brew services start redis

# Linux
sudo systemctl start redis

# Or run directly
redis-server
```

### Import Error
```
ModuleNotFoundError: No module named 'rsa'
```

**Solution:** Install dependencies:
```bash
pip install rsa>=4.9
```

### Decryption Error
If you see decryption errors, ensure:
- The same LSFS instance is used for encryption and decryption
- Keys are not lost between operations
- File was actually encrypted before attempting decryption

## Future Improvements

For production use, consider:
1. Using the `cryptography` library (actively maintained, more secure)
2. Implementing hybrid encryption (RSA + AES) for better performance
3. Key persistence and rotation mechanisms
4. Encrypting files on disk as well
5. Adding encryption to vector database storage

## Example: Custom Performance Test

```python
import time
from aios.storage.filesystem.lsfs import LSFS
import os

# Create test environment
test_dir = "/tmp/lsfs_test"
os.makedirs(test_dir, exist_ok=True)

# Initialize with encryption
lsfs = LSFS(test_dir, use_encryption=True, rsa_key_size=2048)

# Measure write time
content = "X" * 50000  # 50KB of data
file_path = os.path.join(test_dir, "test.txt")

start = time.time()
lsfs.sto_write("test.txt", file_path, content)
write_time = time.time() - start

print(f"Write time: {write_time:.4f} seconds")

# Measure rollback time
start = time.time()
lsfs.sto_rollback(file_path, n=1)
rollback_time = time.time() - start

print(f"Rollback time: {rollback_time:.4f} seconds")
```

## Questions?

This implementation is designed for **educational and research purposes** to measure the performance impact of RSA encryption on the AIOS file system operations.
