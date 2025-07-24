import json
import sys
import dns.rdata
import dns.rdtypes.IN.A
import dns.rdtypes.IN.AAAA
import dns.rdtypes.IN.MX
import dns.rdtypes.IN.TXT
import dns.rdtypes.IN.SRV
import dns.rdtypes.IN.NS
import dns.rdtypes.IN.SOA
import dns.rdtypes.IN.HINFO
import dns.rdtypes.IN.CAA
import dns.rdtypes.IN.LOC
import dns.rdtypes.IN.SSHFP
import dns.rdtypes.IN.URI
import dns.rdtypes.IN.CNAME
from dns.rdataclass import IN
from dns.rdatatype import *

def export_json_to_zone(json_file_path, output_zone_path, default_ttl=3600):
    try:
        with open(json_file_path, 'r') as f:
            json_data = json.load(f)

        zone_lines = []
        
        # Add default TTL
        zone_lines.append(f"$TTL {default_ttl}")

        # Process SOA record first if it exists, to get origin and other details
        soa_data = json_data.get("SOA", {}).get("@")
        if soa_data:
            # Assuming soa_data is a string like "mname rname serial refresh retry expire minimum"
            parts = soa_data.split()
            if len(parts) == 7:
                mname, rname, serial, refresh, retry, expire, minimum = parts
                # The origin for the zone file is typically the domain itself, derived from the file name or mname
                # For simplicity, we'll assume the origin is derived from the JSON file name or needs to be passed.
                # For now, let's just write the SOA record as is.
                zone_lines.append(f"@ IN SOA {mname} {rname} (")
                zone_lines.append(f"\t\t\t{serial} ; serial")
                zone_lines.append(f"\t\t\t{refresh} ; refresh")
                zone_lines.append(f"\t\t\t{retry} ; retry")
                zone_lines.append(f"\t\t\t{expire} ; expire")
                zone_lines.append(f"\t\t\t{minimum} ) ; minimum")
            else:
                print(f"Warning: Malformed SOA record for @: {soa_data}", file=sys.stderr)
            
            # Remove SOA from json_data to avoid re-processing
            json_data.pop("SOA", None)

        for record_type, records in json_data.items():
            for name, value in records.items():
                # Handle multiple records for the same name/type
                if isinstance(value, list):
                    for item in value:
                        zone_lines.append(format_record(record_type, name, item))
                else:
                    zone_lines.append(format_record(record_type, name, value))

        with open(output_zone_path, 'w') as f:
            f.write("\n".join(zone_lines))
        
        print(f"Successfully exported '{json_file_path}' to '{output_zone_path}'")

    except FileNotFoundError:
        print(f"Error: JSON file not found at '{json_file_path}'", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{json_file_path}'", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

def format_record(record_type, name, value):
    # Replace '@' with empty string for origin
    formatted_name = name if name != '@' else ''
    
    # Handle specific record types
    if record_type == 'MX':
        # Value is "preference exchange"
        parts = value.split(' ', 1)
        if len(parts) == 2:
            preference, exchange = parts
            return f"{formatted_name}\tIN\tMX\t{preference}\t{exchange}"
        else:
            print(f"Warning: Malformed MX record for {name}: {value}", file=sys.stderr)
            return ""
    elif record_type == 'SRV':
        # Value is "priority weight port target"
        parts = value.split(' ', 3)
        if len(parts) == 4:
            priority, weight, port, target = parts
            return f"{formatted_name}\tIN\tSRV\t{priority}\t{weight}\t{port}\t{target}"
        else:
            print(f"Warning: Malformed SRV record for {name}: {value}", file=sys.stderr)
            return ""
    elif record_type == 'TXT':
        # TXT records need to be quoted
        return f"{formatted_name}\tIN\tTXT\t\"{value}\""
    elif record_type == 'CAA':
        # Value is "flags tag \"value\""
        parts = value.split(' ', 2)
        if len(parts) == 3:
            flags, tag, val = parts
            return f"{formatted_name}\tIN\tCAA\t{flags}\t{tag}\t{val}"
        else:
            print(f"Warning: Malformed CAA record for {name}: {value}", file=sys.stderr)
            return ""
    elif record_type == 'SSHFP':
        # Value is "algorithm fp_type fingerprint"
        parts = value.split(' ', 2)
        if len(parts) == 3:
            algorithm, fp_type, fingerprint = parts
            return f"{formatted_name}\tIN\tSSHFP\t{algorithm}\t{fp_type}\t{fingerprint}"
        else:
            print(f"Warning: Malformed SSHFP record for {name}: {value}", file=sys.stderr)
            return ""
    elif record_type == 'URI':
        # Value is "priority weight \"target\""
        parts = value.split(' ', 2)
        if len(parts) == 3:
            priority, weight, target = parts
            return f"{formatted_name}\tIN\tURI\t{priority}\t{weight}\t{target}"
        else:
            print(f"Warning: Malformed URI record for {name}: {value}", file=sys.stderr)
            return ""
    elif record_type == 'CNAME':
        # CNAME values should not be quoted and should end with a dot if not an alias to another record in the same zone
        # For simplicity, we'll assume it's a simple name for now.
        return f"{formatted_name}\tIN\tCNAME\t{value}"
    else:
        # Default format for A, AAAA, NS, HINFO, LOC, etc.
        return f"{formatted_name}\tIN\t{record_type}\t{value}"

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 zone_exporter.py <json_file_path> <output_zone_path>", file=sys.stderr)
        sys.exit(1)
    
    json_file = sys.argv[1]
    output_zone = sys.argv[2]
    
    export_json_to_zone(json_file, output_zone)
