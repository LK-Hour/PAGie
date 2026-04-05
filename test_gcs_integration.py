#!/usr/bin/env python3
"""
test_gcs_integration.py — Quick test for GCS sync functionality
===============================================================
Tests the GCS integration without deploying to Streamlit Cloud.

Usage:
    # Test with .env configuration
    python test_gcs_integration.py
    
    # Test download only
    python test_gcs_integration.py --download
    
    # Test upload only
    python test_gcs_integration.py --upload
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_imports():
    """Test that all required modules can be imported."""
    print("🧪 Testing imports...")
    try:
        import google.cloud.storage
        print("  ✅ google-cloud-storage installed")
    except ImportError:
        print("  ❌ google-cloud-storage not found")
        print("     Install with: pip install google-cloud-storage")
        return False
    
    try:
        import gcs_sync
        print("  ✅ gcs_sync module found")
    except ImportError as e:
        print(f"  ❌ gcs_sync module not found: {e}")
        return False
    
    return True

def test_configuration():
    """Test that GCS configuration is properly set."""
    print("\n🔧 Testing configuration...")
    
    gcs_enabled = os.getenv("GCS_ENABLED", "false").lower() == "true"
    gcs_bucket = os.getenv("GCS_BUCKET_NAME", "")
    gcs_creds = os.getenv("GCS_CREDENTIALS_JSON", "")
    
    if not gcs_enabled:
        print("  ⚠️  GCS_ENABLED is false")
        print("     Set GCS_ENABLED=true in .env to enable GCS sync")
        return False
    
    print(f"  ✅ GCS_ENABLED: {gcs_enabled}")
    
    if not gcs_bucket:
        print("  ❌ GCS_BUCKET_NAME not set")
        print("     Set GCS_BUCKET_NAME in .env")
        return False
    
    print(f"  ✅ GCS_BUCKET_NAME: {gcs_bucket}")
    
    if not gcs_creds:
        print("  ❌ GCS_CREDENTIALS_JSON not set")
        print("     Set GCS_CREDENTIALS_JSON in .env (path to JSON key or JSON content)")
        return False
    
    # Check if it's a file path or JSON content
    if gcs_creds.startswith("{"):
        print("  ✅ GCS_CREDENTIALS_JSON: JSON content provided")
    elif Path(gcs_creds).exists():
        print(f"  ✅ GCS_CREDENTIALS_JSON: {gcs_creds} (file exists)")
    else:
        print(f"  ❌ GCS_CREDENTIALS_JSON: {gcs_creds} (file not found)")
        return False
    
    return True

def test_gcs_client():
    """Test that GCS client can be initialized."""
    print("\n🔌 Testing GCS client initialization...")
    try:
        from gcs_sync import _get_gcs_client
        
        client = _get_gcs_client()
        if client is None:
            print("  ❌ GCS client initialization failed (returned None)")
            return False
        
        print("  ✅ GCS client initialized successfully")
        
        # Test bucket access
        gcs_bucket_name = os.getenv("GCS_BUCKET_NAME", "")
        bucket = client.bucket(gcs_bucket_name)
        
        # Try to list blobs (this will fail if permissions are wrong)
        try:
            list(bucket.list_blobs(max_results=1))
            print(f"  ✅ Successfully accessed bucket: {gcs_bucket_name}")
        except Exception as e:
            print(f"  ❌ Failed to access bucket: {e}")
            print("     Check bucket permissions and service account roles")
            return False
        
        return True
    
    except Exception as e:
        print(f"  ❌ GCS client initialization failed: {e}")
        return False

def test_download():
    """Test downloading ChromaDB from GCS."""
    print("\n⬇️  Testing ChromaDB download from GCS...")
    try:
        from gcs_sync import sync_chromadb_from_cloud
        
        success = sync_chromadb_from_cloud(force=False)
        if success:
            print("  ✅ ChromaDB download successful")
        else:
            print("  ❌ ChromaDB download failed")
        
        return success
    
    except Exception as e:
        print(f"  ❌ Download test failed: {e}")
        return False

def test_upload():
    """Test uploading ChromaDB to GCS."""
    print("\n⬆️  Testing ChromaDB upload to GCS...")
    
    # Check if ChromaDB exists locally
    chroma_path = Path(os.getenv("CHROMA_DB_PATH", "./chroma_db"))
    if not chroma_path.exists():
        print(f"  ⚠️  ChromaDB not found at {chroma_path}")
        print("     Creating a dummy file for testing...")
        chroma_path.mkdir(parents=True, exist_ok=True)
        (chroma_path / "test_file.txt").write_text("Test content for GCS sync")
    
    try:
        from gcs_sync import sync_chromadb_to_cloud
        
        success = sync_chromadb_to_cloud(incremental=True)
        if success:
            print("  ✅ ChromaDB upload successful")
        else:
            print("  ❌ ChromaDB upload failed")
        
        return success
    
    except Exception as e:
        print(f"  ❌ Upload test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("PAGie GCS Integration Test Suite")
    print("=" * 60)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Test GCS integration")
    parser.add_argument("--download", action="store_true", help="Test download only")
    parser.add_argument("--upload", action="store_true", help="Test upload only")
    args = parser.parse_args()
    
    # Run tests
    results = {}
    
    if not args.download and not args.upload:
        # Run all tests
        results["imports"] = test_imports()
        if results["imports"]:
            results["configuration"] = test_configuration()
            if results["configuration"]:
                results["gcs_client"] = test_gcs_client()
                if results["gcs_client"]:
                    results["download"] = test_download()
                    results["upload"] = test_upload()
    elif args.download:
        # Download only
        results["imports"] = test_imports()
        if results["imports"]:
            results["download"] = test_download()
    elif args.upload:
        # Upload only
        results["imports"] = test_imports()
        if results["imports"]:
            results["upload"] = test_upload()
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()
