#!/usr/bin/env python3
"""
Samsung The Frame TV Photo Uploader

Sends photos from a folder to Samsung The Frame TV's Art Mode using the samsungtvws library.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Optional

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

# Supported image formats
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.jfif'}


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


def get_image_files(folder_path: str) -> List[str]:
    """Get all image files from the specified folder."""
    folder = Path(folder_path)

    if not folder.exists():
        logger.error(f"Folder does not exist: {folder_path}")
        return []

    if not folder.is_dir():
        logger.error(f"Path is not a directory: {folder_path}")
        return []

    image_files = []
    for ext in SUPPORTED_FORMATS:
        image_files.extend(folder.glob(f'*{ext}'))
        image_files.extend(folder.glob(f'*{ext.upper()}'))

    # Remove duplicates and sort
    image_files = sorted(set(image_files))

    logger.info(f"Found {len(image_files)} image file(s) in {folder_path}")
    return [str(f) for f in image_files]


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


def get_file_type(image_path: str) -> str:
    """Determine file type from extension."""
    ext = os.path.splitext(image_path)[1].lower()
    if ext in {'.jpg', '.jpeg', '.jfif'}:
        return 'JPEG'
    elif ext == '.png':
        return 'PNG'
    else:
        return 'JPEG'  # Default


def upload_photos_to_tv(tv: SamsungTVWS, image_files: List[str]) -> bool:
    """Upload photos to TV's Art Mode."""
    try:
        # Get Art Mode interface
        art = tv.art()

        # Check if Art Mode is supported
        if not hasattr(art, 'upload') and not hasattr(art, 'upload_image'):
            logger.error("Art Mode is not supported on this TV.")
            return False

        logger.info(f"Starting upload of {len(image_files)} photo(s)...")

        success_count = 0
        failed_count = 0

        for image_path in image_files:
            image_name = os.path.basename(image_path)
            try:
                logger.info(f"Uploading {image_name}...")

                with open(image_path, 'rb') as img_file:
                    image_data = img_file.read()
                    file_type = get_file_type(image_path)

                    # Try different API methods based on library version
                    if hasattr(art, 'upload'):
                        art.upload(image_data, file_type=file_type)
                    elif hasattr(art, 'upload_image'):
                        art.upload_image(image_data, image_name)
                    else:
                        logger.error(f"Unknown Art Mode API for {image_name}")
                        failed_count += 1
                        continue

                logger.info(f"✓ Successfully uploaded {image_name}")
                success_count += 1

            except Exception as e:
                logger.error(f"✗ Failed to upload {image_name}: {e}")
                failed_count += 1
                continue

        logger.info(f"\nUpload complete: {success_count} succeeded, {failed_count} failed")
        return success_count > 0

    except Exception as e:
        logger.error(f"Error uploading photos: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Send photos to Samsung The Frame TV Art Mode'
    )
    parser.add_argument(
        'folder',
        nargs='?',
        help='Path to folder containing photos (or use config.json)'
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

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Determine folder path
    folder_path = args.folder or config.get('folder_path')
    if not folder_path:
        logger.error("No folder path specified. Provide it as argument or in config.json")
        parser.print_help()
        sys.exit(1)

    # Determine TV IP address
    tv_ip = args.ip or config.get('tv_ip')
    if not tv_ip:
        logger.error("No TV IP address specified. Provide it via --ip or in config.json")
        sys.exit(1)

    # Get port and token file from args or config
    tv_port = args.port or config.get('tv_port', 8002)
    token_file = args.token_file or config.get('token_file')

    # Get image files
    image_files = get_image_files(folder_path)
    if not image_files:
        logger.error("No image files found in the specified folder")
        sys.exit(1)

    # Connect to TV
    tv = connect_to_tv(tv_ip, tv_port, token_file)
    if not tv:
        sys.exit(1)

    # Upload photos
    success = upload_photos_to_tv(tv, image_files)

    if success:
        logger.info("Photos uploaded successfully!")
        sys.exit(0)
    else:
        logger.error("Failed to upload photos")
        sys.exit(1)


if __name__ == '__main__':
    main()

