import socket
import logging
import json
import configparser
from dns import query, message, rcode, rrset, rdatatype

import os

# --- Configuration ---
CONFIG_FILE = "config/config.ini"

class DNSResolver:
    """
    A DNS resolver that can use both a static hosts file and a forwarder.
    """
    def __init__(self, config_file):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        self.listen_ip = self.config.get("DNS", "LISTEN_IP", fallback="127.0.0.1")
        self.listen_port = self.config.getint("DNS", "LISTEN_PORT", fallback=5353)
        self.forwarders = self.config.get("DNS", "FORWARDERS", fallback="8.8.8.8").split(',')
        self.log_level = self.config.get("DNS", "LOG_LEVEL", fallback="INFO")
        self.zones_dir = self.config.get("DNS", "ZONES_DIR", fallback="zones")
        logging.basicConfig(level=self.log_level, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        self.static_records = self.load_zones()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def load_zones(self):
        """
        Loads all zone files from the zones directory.
        """
        zones = {}
        if not os.path.isdir(self.zones_dir):
            self.logger.warning(f"Zones directory not found: {self.zones_dir}")
            return zones

        for filename in os.listdir(self.zones_dir):
            if filename.endswith(".json"):
                zone_name = filename[:-5]
                try:
                    with open(os.path.join(self.zones_dir, filename), 'r') as f:
                        zone_data = json.load(f)
                        zones[zone_name] = zone_data
                        self.logger.info(f"Loaded zone: {zone_name}")
                except json.JSONDecodeError:
                    self.logger.error(f"Error decoding JSON from {filename}")
        return zones

    def start(self):
        """
        Starts the DNS server.
        """
        try:
            self.sock.bind((self.listen_ip, self.listen_port))
            self.logger.info(f"DNS server started on {self.listen_ip}:{self.listen_port}")
            while True:
                data, addr = self.sock.recvfrom(512)
                self.handle_query(data, addr)
        except PermissionError:
            self.logger.error(f"Permission denied to bind to port {self.listen_port}. Try running as root or using a port > 1024.")
        except OSError as e:
            self.logger.error(f"Failed to start server: {e}")
        finally:
            self.sock.close()
            self.logger.info("DNS server stopped.")

    def handle_query(self, data, addr):
        """
        Handles an incoming DNS query.
        """
        try:
            request = message.from_wire(data)
            qname = request.question[0].name.to_text()
            qtype = request.question[0].rdtype

            self.logger.info(f"Received query from {addr} for {qname} ({rdatatype.to_text(qtype)})")

            # Check static records first
            response = self.get_static_response(request)
            if response:
                self.logger.info(f"Found static record for {qname}")
                self.sock.sendto(response.to_wire(), addr)
                self.logger.info(f"Sent static response to {addr}")
                return

            # If not in static records, forward the query
            self.logger.info(f"No static record for {qname}, forwarding query")
            response = self.forward_query(request)
            if response:
                self.sock.sendto(response.to_wire(), addr)
                self.logger.info(f"Sent forwarded response to {addr}")

        except Exception as e:
            self.logger.error(f"Error handling query from {addr}: {e}")

    def get_static_response(self, request):
        """
        Checks for a static record and returns a response if found.
        """
        qname = request.question[0].name.to_text()
        qtype = request.question[0].rdtype
        qtype_text = rdatatype.to_text(qtype)

        # Normalize qname to ensure it ends with a dot
        if not qname.endswith('.'):
            qname += '.'

        # Find the longest matching zone for the query
        matched_zone_name = None
        for zone_name in self.static_records.keys():
            # Normalize zone_name to ensure it ends with a dot for comparison
            normalized_zone_name = zone_name if zone_name.endswith('.') else zone_name + '.'

            # Special handling for PTR records
            if qtype_text == 'PTR' and qname.endswith('in-addr.arpa.'):
                # For PTR, we need to check if the query is within the reverse zone
                # e.g., query for 1.0.0.127.in-addr.arpa. should match 127.in-addr.arpa.
                if normalized_zone_name.endswith('in-addr.arpa.') and qname.endswith(normalized_zone_name):
                    if matched_zone_name is None or len(normalized_zone_name) > len(matched_zone_name):
                        matched_zone_name = normalized_zone_name
            elif qname.endswith(normalized_zone_name):
                if matched_zone_name is None or len(normalized_zone_name) > len(matched_zone_name):
                    matched_zone_name = normalized_zone_name

        if matched_zone_name:
            zone_data = self.static_records[matched_zone_name.rstrip('.')] # Get data using original key
            subdomain = qname[:-len(matched_zone_name)].rstrip('.')
            if qtype_text == 'PTR':
                # For PTR, the subdomain is the reversed IP part
                subdomain = qname[:len(qname) - len(matched_zone_name)].rstrip('.')
            elif not subdomain: # apex domain
                subdomain = "@"

            if qtype_text in zone_data and subdomain in zone_data[qtype_text]:
                response = message.make_response(request)
                answer_data = zone_data[qtype_text][subdomain]

                # Handle CNAMEs where the target is also in the zone
                if qtype_text == 'CNAME':
                    # Ensure CNAME target ends with a dot for consistency
                    if not answer_data.endswith('.'):
                        answer_data += '.'
                    # If the CNAME target is an A record in the same zone, resolve it
                    if answer_data.rstrip('.') in zone_data.get('A', {}):
                        answer_data = zone_data['A'][answer_data.rstrip('.')]
                        qtype_text = 'A' # Change type to A if we're returning an A record

                # Format answer_data for rrset.from_text based on qtype
                formatted_answer_data = self._format_answer_data(qtype_text, answer_data)

                answer = rrset.from_text(
                    qname, 300, 'IN', qtype_text, formatted_answer_data
                )
                response.answer.append(answer)
                return response
        return None

    def _format_answer_data(self, qtype_text, answer_data):
        """
        Helper to format answer_data string for rrset.from_text based on record type.
        """
        if qtype_text == 'MX':
            # answer_data is expected as "preference hostname" e.g., "10 mail.example.com."
            # If it's just a hostname, assume preference 10
            parts = answer_data.split(' ', 1)
            if len(parts) == 1:
                return f"10 {answer_data}"
            return answer_data
        elif qtype_text == 'TXT':
            # TXT records need to be quoted
            return f
            # SRV records are "priority weight port target" e.g., "0 5 5060 sip.example.com."
            # Ensure target ends with a dot
            parts = answer_data.split(' ')
            if len(parts) == 4:
                target = parts[3]
                if not target.endswith('.'):
                    parts[3] = target + '.'
                return ' '.join(parts)
            return answer_data # Return as is if not correctly formatted, rrset.from_text will likely fail
        elif qtype_text == 'NS' or qtype_text == 'PTR':
            # NS and PTR records are hostnames, ensure they end with a dot
            if not answer_data.endswith('.'):
                return answer_data + '.'
            return answer_data
        elif qtype_text == 'SOA':
            # SOA records are "mname rname serial refresh retry expire minimum"
            # Ensure mname and rname end with a dot
            parts = answer_data.split(' ')
            if len(parts) == 7:
                mname = parts[0]
                rname = parts[1]
                if not mname.endswith('.'):
                    parts[0] = mname + '.'
                if not rname.endswith('.'):
                    parts[1] = rname + '.'
                return ' '.join(parts)
            return answer_data
        elif qtype_text == 'HINFO':
            # HINFO records are "CPU OS", need to be quoted
            parts = answer_data.split(' ', 1)
            if len(parts) == 2:
                return f"\"{parts[0]}\" \"{parts[1]}\""
            return answer_data
        # A, AAAA, CNAME (already handled for target dot), etc. can be used as is
        return answer_data

    def forward_query(self, request):
        """
        Forwards a DNS query to the upstream resolver.
        """
        for forwarder in self.forwarders:
            try:
                response = query.udp(request, forwarder, timeout=5)
                return response
            except Exception as e:
                self.logger.error(f"Failed to forward query to {forwarder}: {e}")
        
        # If all forwarders fail, return a SERVFAIL response
        response_message = message.make_response(request)
        response_message.set_rcode(rcode.SERVFAIL)
        return response_message

def main():
    """
    Main function to run the DNS server.
    """
    resolver_server = DNSResolver(CONFIG_FILE)
    resolver_server.start()

if __name__ == "__main__":
    main()