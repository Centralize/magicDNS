# My Custom DNS Server

This project implements a simple, custom DNS server written in Python 3 for Linux environments. It aims to provide a lightweight and configurable DNS resolution service, primarily for local network use, development environments, or specialized applications.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Features

- **Custom DNS Resolution:** Resolve domain names based on predefined records or act as a forwarding resolver.
- **Supported Record Types:** A, AAAA, MX, TXT, SRV, NS, PTR, SOA, HINFO, CAA, LOC, SSHFP, URI.
- **Python 3 Based:** Leverages Python's network capabilities for ease of development and readability.
- **Linux Native:** Designed and optimized for Linux operating systems.
- **Lightweight:** Minimal dependencies, suitable for embedded systems or low-resource environments.
- **Configurable:** Easy-to-edit configuration for DNS records and forwarding settings.
- **Logging:** Basic logging for requests and responses to aid in debugging.

## Requirements

- Linux Operating System (e.g., Ubuntu, Debian, CentOS, Fedora)
- Python 3.8+
- `dnspython` library (can be installed via pip)

## Installation

Follow these steps to set up and run your DNS server.

### 1. Clone the Repository

```bash
git clone [https://github.com/your-username/my-dns-server.git](https://github.com/your-username/my-dns-server.git)
cd my-dns-server
```

*(Note: Replace `https://github.com/your-username/my-dns-server.git` with your actual repository URL once available.)*

### 2\. Install Dependencies

It is highly recommended to use a Python virtual environment to manage dependencies.

```bash
python3 -m venv venv
source venv/bin/activate
pip install dnspython
```

### 3\. Database/Configuration Setup (if applicable)

If your DNS server uses a database (e.g., SQLite3) or specific configuration files, ensure they are set up.

Example for `config.ini`:

```ini
[DNS]
LISTEN_IP = 0.0.0.0
LISTEN_PORT = 53
FORWARDERS = 8.8.8.8, 8.8.4.4
RECORDS_FILE = records.json # Or similar, if using a file for static records

# Example records.json (if used)
# {
#    "example.com.": "192.168.1.100",
#    "dev.local.": "127.0.0.1"
# }
```

### 4\. Configure Systemd Service (Optional, Recommended for Production)

For continuous operation, create a systemd service unit file.

Create `/etc/systemd/system/my-dns-server.service`:

```ini
[Unit]
Description=My Custom DNS Server
After=network.target

[Service]
User=nobody # Or a dedicated user like 'dnsuser'
Group=nogroup # Or 'dnsuser'
WorkingDirectory=/path/to/my-dns-server
ExecStart=/path/to/my-dns-server/venv/bin/python /path/to/my-dns-server/src/app.py --config /path/to/my-dns-server/config.ini
Restart=on-failure
StandardOutput=journal
StandardError=journal
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

Remember to replace `/path/to/my-dns-server` with the actual path to your project directory.

Then, enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable my-dns-server.service
sudo systemctl start my-dns-server.service
sudo systemctl status my-dns-server.service
```

### 5\. Configure Firewall (e.g., UFW/firewalld)

Allow UDP traffic on port 53.

**For UFW (Debian/Ubuntu):**

```bash
sudo ufw allow 53/udp
sudo ufw enable # if not already enabled
```

**For firewalld (RHEL/CentOS/Fedora):**

```bash
sudo firewall-cmd --add-port=53/udp --permanent
sudo firewall-cmd --reload
```

## Configuration

The server's behavior is controlled by a `config.ini` file (or similar, depending on your implementation).

**Example `config.ini`:**

```ini
[DNS]
LISTEN_IP = 0.0.0.0       # IP address to listen on (0.0.0.0 for all interfaces)
LISTEN_PORT = 53        # Port to listen on (default DNS port)
FORWARDERS = 8.8.8.8, 1.1.1.1 # Comma-separated list of upstream DNS servers
LOG_LEVEL = INFO        # Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
STATIC_RECORDS_FILE = config/records.json # Path to a JSON file for static DNS records

[RECORDS] # Example for static records loaded from config.ini directly
# A records
example.com. = 192.168.1.1
[www.example.com](https://www.example.com). = 192.168.1.1
# CNAME records
app.example.com. = [www.example.com](https://www.example.com).
# PTR records (for reverse DNS)
1.1.168.192.in-addr.arpa. = example.com.
```

**Example `config/records.json` (if used for static records):**

```json
{
  "A": {
    "localapp.dev.": "127.0.0.1",
    "myservice.local.": "192.168.1.50"
  },
  "CNAME": {
    "www.localapp.dev.": "localapp.dev."
  },
  "PTR": {
    "1.0.0.127.in-addr.arpa.": "localapp.dev."
  }
}
```

*(Your Python implementation will need to parse these configurations.)*

## Usage

Once the server is running, you can configure your Linux machine (or other devices) to use it as the primary DNS resolver.

### Temporary DNS Configuration (Linux)

Edit `/etc/resolv.conf` (changes may be overwritten by NetworkManager):

```bash
# Add your DNS server IP as the first nameserver
sudo sed -i '1s/^/nameserver 127.0.0.1\n/' /etc/resolv.conf
# Or if your server is on another IP:
# sudo sed -i '1s/^/nameserver YOUR_SERVER_IP\n/' /etc/resolv.conf
```

### Permanent DNS Configuration (NetworkManager - GUI or nmcli)

**Using `nmcli` (command line):**

Replace `eth0` with your network interface name.

```bash
nmcli connection show # Find your connection name (e.g., "Wired connection 1")
nmcli connection modify "Wired connection 1" ipv4.dns "127.0.0.1"
nmcli connection modify "Wired connection 1" ipv4.dns-search "local" # Add search domains if needed
nmcli connection up "Wired connection 1"
```

**For Server Environments (No NetworkManager):**

Edit `/etc/netplan/01-netcfg.yaml` (Ubuntu Server 20.04+ example):

```yaml
network:
  version: 2
  ethernets:
    enp0s3: # Your interface name
      dhcp4: no
      addresses: [192.168.1.10/24] # Your static IP
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
          addresses: [127.0.0.1, 8.8.8.8] # Your DNS server first, then fallback
          search: [local, example.com]
```

Apply Netplan changes:

```bash
sudo netplan try
sudo netplan apply
```

### Testing the DNS Server

Use `dig` or `nslookup` to test resolutions.

```bash
dig @127.0.0.1 example.com # Query your server for example.com
dig @127.0.0.1 localapp.dev # Query for a static record
```

## Project Structure

```
my-dns-server/
├── src/
│   └── app.py              # Main DNS server application logic
│   └── config.py           # (Optional) Configuration parsing module
│   └── utils.py            # (Optional) Utility functions
├── config/
│   └── config.ini          # Server configuration
│   └── records.json        # (Optional) Static DNS records in JSON format
├── venv/                   # Python virtual environment
├── README.md               # Project documentation
├── GEMINI.md               # Specific instructions/notes for Gemini AI
├── LICENSE.md              # Project license (CC BY-NC 4.0)
├── .gitignore              # Files/directories to ignore in Git
```

## Contributing

Contributions are welcome\! Please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add new feature'`).
5.  Push to the branch (`git push origin feature/your-feature`).
6.  Open a Pull Request.

## License

This project is licensed under the [Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0) License](LICENSE.md).

## Contact

For any questions or suggestions, please open an issue on the GitHub repository.
