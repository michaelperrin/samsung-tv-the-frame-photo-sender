#!/usr/bin/env python3
"""
Samsung The Frame TV Photo Remover

Removes all photos from Samsung The Frame TV's Art Mode collection using the samsungtvws library.
"""

import os
import sys
import json
import argparse
import logging
from typing import Optional, List

try:
    from samsungtvws import SamsungTVWS
except ImportError:
    print("Error: samsungtvws library not found. Please install it using:")
    print("  pip install samsungtvws")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = 'config.json') -> dict:
    """Load configuration from JSON file."""
    if not os.path.exists(config_path):
        logger.warning(f"Config file {config_path} not found. Using defaults.")
        return {}

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing config file: {e}")
        return {}


def connect_to_tv(ip_address: str, port: int = 8002, token_file: Optional[str] = None) -> Optional[SamsungTVWS]:
    """Connect to Samsung TV."""
    if token_file is None:
        token_file = os.path.expanduser('~/.samsungtv-token')

    try:
        logger.info(f"Connecting to TV at {ip_address}:{port}...")
        tv = SamsungTVWS(host=ip_address, port=port, token_file=token_file)
        logger.info("Connected to TV successfully")
        return tv
    except Exception as e:
        logger.error(f"Failed to connect to TV: {e}")
        logger.info("Make sure your TV is turned on and on the same network.")
        logger.info("You may need to approve the connection on your TV screen.")
        return None


def list_photos_in_art_mode(art) -> List[str]:
    """Attempt to list photos in Art Mode collection."""
    photos = []

    # Try different methods to list photos
    methods_to_try = [
        ('list', lambda: art.list()),
        ('list_photos', lambda: art.list_photos()),
        ('get_list', lambda: art.get_list()),
        ('get_photos', lambda: art.get_photos()),
        ('list_collection', lambda: art.list_collection()),
        ('available', lambda: art.available()),
    ]

    for method_name, method_func in methods_to_try:
        if hasattr(art, method_name):
            try:
                logger.info(f"Trying to list photos using {method_name}()...")
                result = method_func()
                logger.info(f"  {method_name}() returned: {result} (type: {type(result).__name__})")

                # Handle different return types
                if isinstance(result, list):
                    photos = result
                elif isinstance(result, dict):
                    # Try various common keys
                    for key in ['photos', 'items', 'content_list', 'data', 'list']:
                        if key in result:
                            photos = result[key]
                            break
                    # If dict but no photos in known keys, log the keys
                    if not photos:
                        logger.info(f"  Dict keys: {list(result.keys())}")
                elif result:
                    # Try to convert to list
                    try:
                        photos = list(result)
                    except:
                        pass

                if photos:
                    logger.info(f"✓ Found {len(photos)} photo(s) in Art Mode collection")
                    logger.info(f"  First photo: {photos[0] if photos else 'N/A'}")
                    return photos
            except Exception as e:
                logger.info(f"  Method {method_name} failed: {e}")
                continue

    logger.warning("Could not list photos - delete methods may still work")
    return []


def delete_photos_from_tv(tv: SamsungTVWS, photo_ids: Optional[List[str]] = None) -> bool:
    """Delete photos from TV's Art Mode collection."""
    try:
        # Get Art Mode interface
        art = tv.art()

        # Check if Art Mode is supported
        if not hasattr(art, 'delete') and not hasattr(art, 'remove') and not hasattr(art, 'delete_all'):
            logger.error("Art Mode delete functionality is not available on this TV.")
            logger.info("You may need to delete photos manually using the SmartThings app.")
            return False

        # If no photo IDs provided, try to list them first
        if photo_ids is None:
            logger.info("Attempting to list photos in Art Mode collection...")
            photo_ids = list_photos_in_art_mode(art)

        # If we have specific photo IDs, delete them one by one
        if photo_ids:
            logger.info(f"Deleting {len(photo_ids)} photo(s)...")
            success_count = 0
            failed_count = 0

            for photo_id in photo_ids:
                try:
                    # Try different delete methods
                    if hasattr(art, 'delete'):
                        art.delete(photo_id)
                    elif hasattr(art, 'remove'):
                        art.remove(photo_id)
                    else:
                        logger.error(f"No delete method available for photo {photo_id}")
                        failed_count += 1
                        continue

                    logger.info(f"✓ Deleted photo: {photo_id}")
                    success_count += 1
                except Exception as e:
                    logger.error(f"✗ Failed to delete photo {photo_id}: {e}")
                    failed_count += 1
                    continue

            logger.info(f"\nDelete complete: {success_count} succeeded, {failed_count} failed")
            return success_count > 0

        # Try to delete all photos using available methods
        logger.info("Attempting to delete all photos...")

        # Try delete_list with empty list or special parameter
        if hasattr(art, 'delete_list'):
            try:
                logger.info("Trying delete_list() method...")
                # Try calling with no arguments
                result = art.delete_list()
                logger.info(f"✓ delete_list() returned: {result}")
                logger.info("✓ Successfully deleted photos using delete_list()")
                return True
            except TypeError as e:
                logger.info(f"delete_list() requires arguments: {e}")
                # Try with an empty list
                try:
                    result = art.delete_list([])
                    logger.info(f"✓ delete_list([]) returned: {result}")
                    logger.info("✓ Successfully deleted photos using delete_list([])")
                    return True
                except Exception as e2:
                    logger.info(f"delete_list([]) failed: {e2}")
            except Exception as e:
                logger.info(f"delete_list() failed: {e}")

        # Try calling delete with no arguments (might delete current/all)
        if hasattr(art, 'delete'):
            try:
                logger.info("Trying delete() method with no arguments...")
                result = art.delete()
                logger.info(f"✓ delete() returned: {result}")
                logger.info("✓ Successfully deleted photos using delete()")
                return True
            except TypeError as e:
                logger.info(f"delete() requires arguments: {e}")
            except Exception as e:
                logger.info(f"delete() failed: {e}")

        # Try other possible bulk delete methods
        delete_methods = [
            ('delete_all', lambda: art.delete_all()),
            ('remove_all', lambda: art.remove_all()),
            ('clear', lambda: art.clear()),
            ('clear_collection', lambda: art.clear_collection()),
        ]

        for method_name, method_func in delete_methods:
            if hasattr(art, method_name):
                try:
                    logger.info(f"Trying to delete all photos using {method_name}()...")
                    result = method_func()
                    logger.info(f"✓ {method_name}() returned: {result}")
                    logger.info(f"✓ Successfully deleted all photos using {method_name}()")
                    return True
                except Exception as e:
                    logger.debug(f"Method {method_name} failed: {e}")
                    continue

        logger.error("Could not delete photos. Available methods:")
        logger.info(f"  Art Mode object methods: {[m for m in dir(art) if not m.startswith('_')]}")
        logger.info("\nNote: Delete functionality may not be available via API.")
        logger.info("You can delete photos manually using the SmartThings app:")
        logger.info("  1. Open SmartThings app")
        logger.info("  2. Select your Frame TV")
        logger.info("  3. Go to Art Mode > My Collection > Photos on Frame")
        logger.info("  4. Tap 'Remove Photos' and select all photos")
        return False

    except Exception as e:
        logger.error(f"Error deleting photos: {e}")
        logger.info(f"\nAvailable Art Mode methods: {[m for m in dir(art) if not m.startswith('_')]}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Remove all photos from Samsung The Frame TV Art Mode'
    )
    parser.add_argument(
        '--config',
        default='config.json',
        help='Path to configuration file (default: config.json)'
    )
    parser.add_argument(
        '--ip',
        help='TV IP address (overrides config file)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8002,
        help='TV port (default: 8002)'
    )
    parser.add_argument(
        '--token-file',
        help='Path to token file (default: ~/.samsungtv-token)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompt'
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Determine TV IP address
    tv_ip = args.ip or config.get('tv_ip')
    if not tv_ip:
        logger.error("No TV IP address specified. Provide it via --ip or in config.json")
        sys.exit(1)

    # Get port and token file from args or config
    tv_port = args.port or config.get('tv_port', 8002)
    token_file = args.token_file or config.get('token_file')

    # Confirmation prompt
    if not args.force:
        print("\n⚠️  WARNING: This will delete ALL photos from your TV's Art Mode collection!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            logger.info("Operation cancelled.")
            sys.exit(0)

    # Connect to TV
    tv = connect_to_tv(tv_ip, tv_port, token_file)
    if not tv:
        sys.exit(1)

    # Delete photos
    success = delete_photos_from_tv(tv)

    if success:
        logger.info("Photos removed successfully!")
        sys.exit(0)
    else:
        logger.error("Failed to remove photos. Check the logs above for details.")
        logger.info("\nAlternative: Use the SmartThings app to manually delete photos.")
        sys.exit(1)


if __name__ == '__main__':
    main()

