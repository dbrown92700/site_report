#!python3

from vmanage_api import VmanageRestApi
from vmanage_classes import Site
import argparse
import pickle


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--address", help="vManage IP address", required=True)
    parser.add_argument("-p", "--port", default=8443, help="vManage port")
    parser.add_argument("-u", "--username", help="vManage username", required=True)
    parser.add_argument("-pw", "--password", help="vManage password", required=True)
    subparser = parser.add_subparsers(dest='command', help="'sid' - run script on a specific site id's",
                                      required=True)
    # sid: pull the details from a specific site-id's
    sid = subparser.add_parser('sid')
    sid.add_argument('-id', nargs='+', required=True, help="-id 10 20 30")
    sid.add_argument('-tlocext', choices=["yes", "no"], default="no",
                     help="will identify TLOC EXT interface only when the interface is directly connected."
                          " 'yes/no'")
    sid.add_argument('-filename', required=True,
                     help="path/filename same filename for multiple iteration")

    args = parser.parse_args()
    vmanage_host = args.address
    vmanage_port = args.port
    username = args.username
    password = args.password
    sites = args.id
    filename = args.filename

    vmanage = VmanageRestApi(f'{vmanage_host}:{vmanage_port}', username, password)

    for site_id in sites:

        site = Site(vmanage, site_id)
        if not site.valid:
            # Site is not in vManage. Print error message and continue to next site
            print(f'Site_id: {site.site_id} has no edges assigned in vManage')
            continue
        else:
            # Site is valid in vManage.  Gather Edge data at site
            print(f'Site_id: {site.site_id}:')
            valid_edges = list(range(len(site.edges)))
            for num, edge in enumerate(site.edges):
                if edge.reachability != 'reachable' or edge.validity != 'valid':
                    # Edge is not reachable.  Remove from valid list.
                    print(f'  Edge: {edge.sys_ip} skipped. Status: {edge.reachability}, {edge.validity}')
                    valid_edges.remove(num)
                    continue
                else:
                    # Edge is reachable.  Get edge data
                    edge.get_arp(vmanage)
                    edge.get_wan_interfaces(vmanage)
                    edge.get_interface_stats(vmanage, interval=5)
                    edge.get_config(vmanage)
                    edge.get_tloc_ext_interfaces()
        with open(f'site{site.site_id}.pickle', 'wb') as file:
            pickle.dump(site, file)

    vmanage.logout()
