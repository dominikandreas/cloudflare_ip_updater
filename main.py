#!/usr/bin/python3
import os
import sys
import CloudFlare
import json
from urllib.request import urlopen
import yaml


base_dir = os.path.abspath(os.path.dirname(__file__))



def get_ipv6():
    # CAUTION! DIRTY INSUFFICIENTLY TESTED HACK INCOMING
    def get_res(command):
        return os.popen(command).read().split("\n")
    ips = get_res("/sbin/ifconfig eth0 |  awk '/inet6/{print $3}'")
    scopes = get_res("/sbin/ifconfig eth0 |  awk '/inet6/{print $4}'")
    if len(sys.argv)>1 and sys.argv[1]=="debug":
        print("ips, scopes:", ips, scopes)
    ip = [ip for ip,scope in zip(ips,scopes) if "Global" in scope][0]
    if not ":" in ip:
        raise RuntimeError("got invalid ipv6: %s"%ip)
    return ip.split("/")[0]


def get_ip():
    try:
        return json.load(urlopen('http://api.ipify.org/?format=json'))['ip']
    except:
        try:
            return json.load(urlopen('http://jsonip.com'))['ip']
        except:
            return json.load(urlopen('http://httpbin.org/ip'))['origin']

class Record():
    def __init__(self, id, name, type, content, **other_props):
        self.id, self.name, self.type, self.ip = id, name, type, content
        self.other_props = other_props

    def get_data(self):
        return {'content':self.ip, 'name':self.name, 'type': self.type, **self.other_props}

    def __repr__(self):
        return "Record(id=%s, name=%s, type=%s, ip=%s)" % (self.id, self.name, self.type, self.ip)


class CloudflareDNSUpdater:
    def __init__(self, email, api_key, domain_name):
        print("initializing cloudflare api")
        self.cf = CloudFlare.CloudFlare(email=email, token=api_key)
        self.zone_name = domain_name
        print("getting zones... ", end="")
        self.zones = self.cf.zones.get()
        print("done")
        zone_matches = [e for e in self.zones if e['name'] == domain_name]
        if zone_matches:
            self.zone_id = zone_matches[0]['id']
        else:
            raise RuntimeError("Could not find a domain with name %s, found: %s" % (zone_name, str(self.zones)))

    def get_dns_records(self):
        records = [Record(**response) for response in self.cf.zones.dns_records.get(self.zone_id)]
        print("got records: ", ", ".join([r.name.split(".")[0] for r in records]))
        return records

    def update_record(self, record, ip):
        print("updating %-25s to %s... " % (record.name, ip), end="")
        record.ip = ip
        self.cf.zones.dns_records.put(self.zone_id, record.id, data=record.get_data())
        print("done")

    def update_all_records(self, ipv4=None, ipv6=None, sub_domains=None, force=False):
        for record in self.get_dns_records():
            print("handling record %s" % record.name)
            if sub_domains is not None:
                sub_domain_matches = True in [(sub.lower() == record.name.split(".")[0].lower()) for sub in sub_domains]
            else:
                sub_domain_matches = True
            if sub_domain_matches:
                if record.type == "A" and ipv4 and ipv4 != record.ip:
                    self.update_record(record, ipv4)
                elif record.type == "AAAA" and ipv6 and ipv6 != record.ip:
                    self.update_record(record, ipv6)
                else:
                    print(("ip %s matches. " %record.ip) if record.ip in (ipv4, ipv6)
                          else "invalid record type", "skipping record", record)
            else:
                print("subdomain %s does not match any of the given records" % record.name)


class Config:
    def __init__(self, domain_name, email, api_key, sub_domains, ipv4=True, ipv6=False):
        self.domain_name, self.email, self.api_key, self.sub_domains, self.ipv4, self.ipv6 = \
             domain_name, email, api_key, sub_domains, ipv4, ipv6
    def __repr__(self):
        return "Config(domain="+self.domain_name+", email="+self.email+\
                ", sub domains="+str(self.sub_domains)+")"


if __name__ == "__main__":
    with open(base_dir+"/config.yaml") as f:
        configs = yaml.load(f.read())

    ipv4, ipv6 = get_ip(), None
    print("ipv4: %s, ipv6: %s" % (ipv4, ipv6))

    for name, config in configs.items():
        config = Config(**config)
        if config.ipv6 and ipv6 is None:
            try:
                ipv6 = get_ipv6()
            except Exception as e:
                print("unable to get ipv6: %s, skipping ipv6 update" % e)
        print(config)
        updater = CloudflareDNSUpdater(email=config.email, api_key=config.api_key, domain_name=config.domain_name)
        updater.update_all_records(ipv4=ipv4, ipv6=ipv6 if config.ipv6 else None)
