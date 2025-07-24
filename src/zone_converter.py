import dns.zone
import json
import sys
import os

def convert_zone_to_json(zone_file_path, output_json_path):
    try:
        # Read the zone file
        zone = dns.zone.from_file(zone_file_path, origin=None, relativize=False)
        
        json_output = {}

        # Iterate over all RdataSets in the zone
        for name, node in zone.nodes.items():
            for rdataset in node.rdatasets:
                record_type = rdataset.rdtype.to_text()
                
                if record_type not in json_output:
                    json_output[record_type] = {}
                
                # Get the relative name for the record
                relative_name = str(name.relativize(zone.origin)) if zone.origin else str(name)
                if relative_name == '@.': # Handle the origin itself
                    relative_name = '@'
                elif relative_name.endswith('.'): # Remove trailing dot for other records
                    relative_name = relative_name[:-1]

                # Process each record in the rdataset
                for rdata in rdataset:
                    # Special handling for MX records to include preference
                    if record_type == 'MX':
                        record_value = f"{rdata.preference} {rdata.exchange}"
                    # Special handling for SRV records to include weight, priority, port
                    elif record_type == 'SRV':
                        record_value = f"{rdata.priority} {rdata.weight} {rdata.port} {rdata.target}"
                    # Special handling for SOA records
                    elif record_type == 'SOA':
                        record_value = f"{rdata.mname} {rdata.rname} {rdata.serial} {rdata.refresh} {rdata.retry} {rdata.expire} {rdata.minimum}"
                    # Special handling for CAA records
                    elif record_type == 'CAA':
                        record_value = f"{rdata.flags} {rdata.tag} "{rdata.value.decode()}""
                    # Special handling for SSHFP records
                    elif record_type == 'SSHFP':
                        record_value = f"{rdata.algorithm} {rdata.fp_type} {rdata.fingerprint}"
                    # Special handling for URI records
                    elif record_type == 'URI':
                        record_value = f"{rdata.priority} {rdata.weight} "{rdata.target.decode()}""
                    else:
                        record_value = str(rdata)
                    
                    # Append to list if multiple records of same type for same name
                    if relative_name in json_output[record_type]:
                        if not isinstance(json_output[record_type][relative_name], list):
                            json_output[record_type][relative_name] = [json_output[record_type][relative_name]]
                        json_output[record_type][relative_name].append(record_value)
                    else:
                        json_output[record_type][relative_name] = record_value

        # Write the JSON output to a file
        with open(output_json_path, 'w') as f:
            json.dump(json_output, f, indent=2)
        
        print(f"Successfully converted '{zone_file_path}' to '{output_json_path}'")

    except dns.zone.BadZone as e:
        print(f"Error parsing zone file '{zone_file_path}': {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: Zone file not found at '{zone_file_path}'", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 zone_converter.py <zone_file_path> <output_json_path>", file=sys.stderr)
        sys.exit(1)
    
    zone_file = sys.argv[1]
    output_json = sys.argv[2]
    
    convert_zone_to_json(zone_file, output_json)
