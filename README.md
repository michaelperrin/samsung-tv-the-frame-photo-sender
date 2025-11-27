# Samsung The Frame TV Photo Uploader

A Python script to upload photos from a folder to your Samsung The Frame TV's Art Mode using the direct TV API.

## Requirements

- Python 3.7 or higher
- macOS (or any system with Python)
- Samsung The Frame TV (QE43LS03A or compatible models)
- TV and computer on the same network

## Installation

1. **Install Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

   Or install directly:

   ```bash
   pip install samsungtvws
   ```

2. **Configure your TV IP address:**

   Edit `config.json` and set your TV's IP address, or use command-line arguments.

## Finding Your TV's IP Address

1. On your Samsung TV, go to **Settings** → **General** → **Network** → **Network Status**
2. Note the IP address displayed (e.g., `192.168.1.100`)

Alternatively, you can find it on your router's admin page or by using:

```bash
# On macOS/Linux, scan your network
arp -a | grep -i samsung

# Or use nmap (if installed)
nmap -sn 192.168.1.0/24 | grep -B 2 -i samsung
```

## Configuration

### Using config.json

Edit `config.json` with your settings:

```json
{
  "tv_ip": "192.168.1.100",
  "tv_port": 8002,
  "folder_path": "~/SelectedPhotos",
  "token_file": "~/.samsungtv-token"
}
```

- `tv_ip`: Your TV's IP address (required)
- `tv_port`: TV port (default: 8002)
- `folder_path`: Default folder path for photos (optional, can be overridden)
- `token_file`: Path to save authentication token (optional)

### Using Command-Line Arguments

You can override config file settings using command-line arguments:

```bash
python3 send_photos_to_tv.py /path/to/photos --ip 192.168.1.100
```

## Usage

### Basic Usage

```bash
python3 send_photos_to_tv.py /path/to/your/photos
```

### With IP Address

```bash
python3 send_photos_to_tv.py /path/to/your/photos --ip 192.168.1.100
```

### Using Config File

If you've set `folder_path` in `config.json`:

```bash
python3 send_photos_to_tv.py
```

### Command-Line Options

```
usage: send_photos_to_tv.py [-h] [--config CONFIG] [--ip IP] [--port PORT]
                             [--token-file TOKEN_FILE] [folder]

positional arguments:
  folder                Path to folder containing photos (or use config.json)

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG       Path to configuration file (default: config.json)
  --ip IP               TV IP address (overrides config file)
  --port PORT           TV port (default: 8002)
  --token-file TOKEN_FILE
                        Path to token file (default: ~/.samsungtv-token)
```

## First-Time Setup

1. **Make sure your TV is turned on** and connected to the same network as your computer.

2. **Run the script** - On first run, your TV will display a connection request:

   ```
   Allow connection from [your computer name]?
   ```

3. **Approve the connection** on your TV using the remote control.

4. A token will be saved to `~/.samsungtv-token` for future connections.

## Supported Image Formats

- `.jpg` / `.jpeg`
- `.png`
- `.jfif`

## Troubleshooting

### Connection Failed

- **Check TV is on**: Make sure your TV is powered on and not in standby mode
- **Check network**: Ensure TV and computer are on the same Wi-Fi network
- **Check IP address**: Verify the IP address in `config.json` is correct
- **Firewall**: Make sure your firewall isn't blocking port 8002

### Art Mode Not Supported

- Some older TV models may not support Art Mode via API
- Ensure your TV firmware is up to date
- Check that Art Mode is enabled on your TV

### Authentication Issues

- Delete the token file (`~/.samsungtv-token`) and try again
- Make sure to approve the connection when prompted on your TV

### No Images Found

- Check that the folder path is correct
- Ensure images are in supported formats (jpg, png, jpeg, jfif)
- Verify folder permissions allow reading files

## Example Workflow

1. **Prepare your photos:**

   ```bash
   mkdir ~/SelectedPhotos
   # Copy or move photos to ~/SelectedPhotos
   ```

2. **Run the script:**

   ```bash
   python3 send_photos_to_tv.py ~/SelectedPhotos --ip 192.168.1.100
   ```

3. **Photos will be uploaded** to your TV's Art Mode collection

## Removing Photos from Art Mode

A separate script is provided to remove all photos from your TV's Art Mode collection:

### Basic Usage

```bash
python3 remove_photos_from_tv.py
```

### With Confirmation (default)

The script will ask for confirmation before deleting:

```bash
python3 remove_photos_from_tv.py
# ⚠️  WARNING: This will delete ALL photos from your TV's Art Mode collection!
# Are you sure you want to continue? (yes/no):
```

### Skip Confirmation

Use `--force` to skip the confirmation prompt:

```bash
python3 remove_photos_from_tv.py --force
```

### Command-Line Options

```
usage: remove_photos_from_tv.py [-h] [--config CONFIG] [--ip IP] [--port PORT]
                                  [--token-file TOKEN_FILE] [--force]

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG       Path to configuration file (default: config.json)
  --ip IP               TV IP address (overrides config file)
  --port PORT           TV port (default: 8002)
  --token-file TOKEN_FILE
                        Path to token file (default: ~/.samsungtv-token)
  --force               Skip confirmation prompt
```

### Complete Workflow Example

1. **Remove existing photos:**

   ```bash
   python3 remove_photos_from_tv.py --force
   ```

2. **Upload new photos:**
   ```bash
   python3 send_photos_to_tv.py ~/SelectedPhotos
   ```

**Note:** If the delete functionality is not available via API (which may vary by TV model/firmware), the script will provide instructions for manually deleting photos using the SmartThings app.

## Notes

- The script uses the `samsungtvws` library which communicates with Samsung TVs via WebSocket
- Photos are uploaded directly to the TV's Art Mode collection
- The first connection requires TV approval; subsequent connections use the saved token
- Recommended image resolution: 3840×2160 pixels (4K) for best quality on The Frame TV

## License

This script is provided as-is for personal use.
