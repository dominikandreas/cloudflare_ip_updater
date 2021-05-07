#!/usr/bin/python3
import os
import yaml
import traceback

from core import CloudflareDNSUpdater
from utils import get_ipv6, get_ipv4

base_dir = os.path.abspath(os.path.dirname(__file__))


class Config:
    def __init__(self, domain_name, email, api_key, sub_domains, ipv4=True, ipv6=False):
        self.domain_name, self.email, self.api_key, self.sub_domains, self.ipv4, self.ipv6 = \
            domain_name, email, api_key, sub_domains, ipv4, ipv6

    def __repr__(self):
        return "Config(domain=" + self.domain_name + ", email=" + self.email + \
               ", sub domains=" + str(self.sub_domains) + ")"


def update_all_in_config(config, ipv4, ipv6):
    if config.ipv6 and ipv6 is None:
        ipv6 = get_ipv6()
    if config.ipv4 and ipv4 is None:
        ipv4 = get_ipv4()

    assert any((ipv4, ipv6)), "need either ipv4 or ipv6 to continue"
    print("ipv4: %s, ipv6: %s" % (ipv4, ipv6))
    print(config)

    updater = CloudflareDNSUpdater(email=config.email, api_key=config.api_key, domain_name=config.domain_name)
    updater.update_subdomain_ips(ipv4=ipv4, ipv6=ipv6 if config.ipv6 else None, sub_domains=config.sub_domains)


def update_single(config, domain_name, sub_domain_name, ipv4=None, ipv6=None):
    updater = CloudflareDNSUpdater(email=config.email, api_key=config.api_key,
                                   domain_name=domain_name or config.domain_name)
    record = updater.get_single_dns_record(sub_domain_name)
    updater.update_records([record], ipv4, ipv6)


def get_config(config_path):
    with open(config_path) as f:
        return Config(**yaml.safe_load(f.read()))


def main():
    import time
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="path to a config file, ./config.yaml by default",
                        default=base_dir + "/config.yaml")
    parser.add_argument("--loop", help="whether to keep updating in an infinite loop", default=True)
    parser.add_argument("--sleep_time", help="how long to sleep between update iterations", default=300)
    parser.add_argument("--subdomain", help="the subdomain to update", default=None)
    parser.add_argument("--domain", help="the domain to update", default=None)
    parser.add_argument("--ipv4", help="override the ipv4 to set domains to. "
                                       "if not given, will by acquired automatically", default=None)
    parser.add_argument("--ipv6", help="override the ipv6 to set domains to. "
                                       "if not given, will by acquired automatically", default=None)

    args = parser.parse_args()

    config = get_config(args.config)

    if args.ipv4 is None and config.ipv4:
        args.ipv4 = get_ipv4()
    if args.ipv6 is None and config.ipv6:
        args.ipv6 = get_ipv6()

    if args.subdomain:
        update_single(config, args.domain, args.subdomain, args.ipv4, args.ipv6)
    else:
        while True:
            try:
                config = get_config(args.config)
                update_all_in_config(config, args.ipv4, args.ipv6)
            except Exception as e:
                print("exception occurred:", e)
                traceback.print_exc()
            print("waiting for %s seconds before next update" % args.sleep_time)
            time.sleep(args.sleep_time)


if __name__ == "__main__":
    main()
