import argparse
import ipaddress
import pyasn
import csv
import time
import os
import sys
import pandas as pd


debug = False
MIN_PREFIX_LENGTH = 24


def find_hrps(filename: str, output_dir, scan_port, scan_date, scan_location, asn_db, contains_headers=False, print_all=True):
    time_start = time.time()

    dense_entries = []

    zmap_fh = None
    replies = None
    if filename == '-':
        replies = csv.reader(sys.stdin)
    else:
        zmap_fh = open(filename, 'r')
        replies = csv.reader(zmap_fh)
    if contains_headers:
        replies.__next__()

    base_info = []
    base_info_header = []
    if scan_port:
        base_info.append(scan_port)
        base_info_header.append('port')
    if scan_date:
        base_info.append(scan_date)
        base_info_header.append('date')
    if scan_location:
        base_info.append(scan_location)
        base_info_header.append('location')

    ip_str = replies.__next__()[0]
    ip = ipaddress.ip_address(ip_str)
    network = ipaddress.ip_network(f'{ip_str}/{MIN_PREFIX_LENGTH}', strict=False)
    network_count = 1

    for reply in replies:
        ip_str = reply[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            print(f'Value Error for {reply[0]} of file {filename}', file=sys.stderr)
            continue

        if ip not in network:
            if print_all or network_count > 230:
                if asn_db:
                    asn, prefix = asn_db.lookup(ip_str)
                    dense_entries.append((str(network.network_address), network.prefixlen, str(prefix) if prefix else '', str(int(asn)) if asn else '', network_count, *base_info))
                else:
                    dense_entries.append((str(network.network_address), network.prefixlen, network_count, *base_info))

            if debug:
                print('restart net count')

            network_count = 0
            network = ipaddress.ip_network(f'{ip_str}/{MIN_PREFIX_LENGTH}', strict=False)

        network_count += 1
    else:
        if print_all or network_count > 230:
            if asn_db:
                asn, prefix = asn_db.lookup(ip_str)
                dense_entries.append((str(network.network_address), network.prefixlen, str(prefix) if prefix else '', str(int(asn)) if asn else '', network_count, *base_info))
            else:
                dense_entries.append((str(network.network_address), network.prefixlen, network_count, *base_info))

    if zmap_fh:
        zmap_fh.close()

    time_end = time.time()
    print('Finished looking for dense networks in ' + str(time_end - time_start) + ' seconds')
    columns = None
    if asn_db:
        columns = ['network_address', 'prefixlen', 'bgp_prefix', 'asn', 'responsive_addresses', *base_info_header]
        dense_entries_df = pd.DataFrame(dense_entries, columns=columns)
    else:
        columns = ['network_address', 'prefixlen', 'responsive_addresses', *base_info_header]
        dense_entries_df = pd.DataFrame(dense_entries, columns=columns)

    if filename == '-':
        denseentriescsvpath = os.path.join(output_dir, f'slash24-info.csv.gz')
    else:
        denseentriescsvpath = os.path.join(output_dir, f'{os.path.basename(filename)}.slash24-info.csv.gz')

    os.makedirs(os.path.dirname(denseentriescsvpath), exist_ok=True)

    dense_entries_df.to_csv(denseentriescsvpath, index=False, compression='gzip')


def main():
    parser = argparse.ArgumentParser('Parse zmap output and return high responsive prefix information')
    parser.add_argument('input_file', type=str, help='zmap file')
    parser.add_argument('--scan-port', type=int, help='Port or service which has been scanned')
    parser.add_argument('--scan-date', type=str, help='Date of the port scan')
    parser.add_argument('--scan-location', type=str, help='Location of the port scan')
    parser.add_argument('-o', '--output-dir', required=True, type=str, help='Output directory')
    parser.add_argument('--pyasn-file', '-p', type=str, help='Path to pyasn file')
    parser.add_argument('--headers-included', '-t', action='store_true', help='Set this flag if headers are included')
    parser.add_argument('--all', '-a', action='store_true', help='Print all subnets not only 90% HRPs')
    args = parser.parse_args()

    asn_db = None
    if args.pyasn_file:
        asn_db = pyasn.pyasn(args.pyasn_file)

    time_start = time.time()
    find_hrps(args.input_file, args.output_dir, args.scan_port, args.scan_date, args.scan_location, asn_db, contains_headers=args.headers_included, print_all=args.all)
    time_end = time.time()
    print('Total time for analysis: ' + str(time_end - time_start) + ' seconds')


if __name__ == '__main__':
    main()
