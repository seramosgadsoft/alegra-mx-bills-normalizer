"""
Quick test script to verify the system components without processing all invoices.
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config_loader import ConfigLoader
from core.uuid_loader import UUIDLoader
from core.xml_file_searcher import XMLFileSearcher

def test_config_loader():
    """Test configuration loading."""
    print("\n" + "="*70)
    print("Testing Configuration Loader...")
    print("="*70)
    
    try:
        config_loader = ConfigLoader("config.json")
        alegra_config = config_loader.get_alegra_config("MX")
        
        print(f"✅ Config loaded successfully")
        print(f"   Alegra endpoint: {alegra_config.get('endpoint')}")
        print(f"   Alegra user: {alegra_config.get('user')}")
        print(f"   Tax mappings: {len(alegra_config.get('tax_map', []))} taxes configured")
        return True
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False


def test_uuid_loader():
    """Test UUID loading."""
    print("\n" + "="*70)
    print("Testing UUID Loader...")
    print("="*70)
    
    try:
        uuid_loader = UUIDLoader("uuids.txt")
        uuids = uuid_loader.load_uuids()
        
        print(f"✅ UUIDs loaded successfully")
        print(f"   Total UUIDs: {len(uuids)}")
        print(f"   First UUID: {uuids[0] if uuids else 'None'}")
        print(f"   Last UUID: {uuids[-1] if uuids else 'None'}")
        return True
    except Exception as e:
        print(f"❌ UUID loading failed: {e}")
        return False


def test_xml_searcher():
    """Test XML file searcher."""
    print("\n" + "="*70)
    print("Testing XML File Searcher...")
    print("="*70)
    
    try:
        searcher = XMLFileSearcher("bills")
        
        # Load a few UUIDs to test
        uuid_loader = UUIDLoader("uuids.txt")
        uuids = uuid_loader.load_uuids()
        
        if not uuids:
            print("❌ No UUIDs to test")
            return False
        
        # Test first 5 UUIDs
        print(f"\nSearching for first 5 UUIDs...")
        for i, uuid in enumerate(uuids[:5], 1):
            result = searcher.search_by_uuid(uuid)
            
            if result.found and result.is_unique:
                print(f"  [{i}] ✅ {uuid}")
                print(f"      → Found in: {result.single_month}/{os.path.basename(result.single_file_path)}")
            elif result.has_duplicates:
                print(f"  [{i}] ⚠️  {uuid} - MULTIPLE FILES ({len(result.file_paths)})")
                for fp in result.file_paths:
                    print(f"      → {fp}")
            else:
                print(f"  [{i}] ❌ {uuid} - NOT FOUND")
        
        return True
    except Exception as e:
        print(f"❌ XML search failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("🧪 MEXICO BILLS NORMALIZATION - COMPONENT TESTS")
    print("="*70)
    
    results = {
        "Config Loader": test_config_loader(),
        "UUID Loader": test_uuid_loader(),
        "XML Searcher": test_xml_searcher()
    }
    
    print("\n" + "="*70)
    print("📊 TEST RESULTS SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<20} {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All tests passed! The system is ready to run.")
        print("\nTo process all invoices, run:")
        print("  python main.py")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
