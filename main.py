import os,sys
import json
import requests
from subprocess import Popen, PIPE
import ConfigParser
import urllib2
import logging

base_path = os.path.dirname(os.path.abspath(__file__))


def parse_api_result(url_extension, headers, data=None):
    base_api_url = "https://api.cloudflare.com/client/v4/zones"
    if data is not None:
        res = requests.put(base_api_url+url_extension, headers=headers, data=json.dumps(options)).json()
    else:
        res = requests.get(base_api_url+url_extension, headers=headers).json()
    if not res.get("success", False):
        print("error occurred for %s:\n%s\n"%(url_extension, res))
    return res

def get_options():
    if not os.path.isfile(base_path+"/options.json"):
        options = {entry: raw_input("please enter your %s\n"%entry) \
            for entry in ["email", "api_key", "domain_name", "sub_domain_names"]}
        options["sub_domain_names"] = [e.replace(",","").strip() \
            for e in options["sub_domain_names"].split(" ") if "." in e]
        with open(base_path+"/options.json","wb") as f:
            f.write(json.dumps(options, sort_keys=True, indent=4))
            return options
    else:
        with open(base_path+"/options.json", "r") as f:
            return json.loads(f.read())

def get_zone_id():
    print("getting zone id")
    return parse_api_result("?name="+domain_name, headers={"X-Auth-Email":email, "X-Auth-Key":api_key})["result"][0]["id"]

def get_record_ids(zone_id, sub_domain_names):
    print("getting record ids for %s"%sub_domain_names)
    res = parse_api_result("/%s/dns_records"%(zone_id), headers={"X-Auth-Email":email, "X-Auth-Key":api_key})
    return [(e["name"],e["id"], e["type"]) for e in res["result"] if (e["type"] == "A" or e["type"] == "AAAA") and e["name"] in sub_domain_names]

def get_ip6():
    # CAUTION! DIRTY INSUFFICIENTLY TESTED HACK INCOMING
    def get_res(command):
        return os.popen(command).read().split("\n")
    ips = get_res("/sbin/ifconfig eth0 |  awk '/inet6/{print $3}'")
    scopes = get_res("/sbin/ifconfig eth0 |  awk '/inet6/{print $4}'")
    if len(sys.argv)>1 and sys.argv[1]=="debug":
        print "ips, scopes:", ips, scopes
    ip = [ip for ip,scope in zip(ips,scopes) if "Global" in scope][0]
    if not ":" in ip:
        raise RuntimeError("got invalid ipv6: %s"%ip)
    return ip.split("/")[0]


def get_ip():
    try:
        return json.load(urllib2.urlopen('http://api.ipify.org/?format=json'))['ip']
    except:
        try:
            return json.load(urlopen('http://jsonip.com'))['ip']
        except:
            return json.load(urlopen('http://httpbin.org/ip'))['origin']

def get_rec_options(rec_id,rec_type,name):
    options = {'id': rec_id, 'type': rec_type, 'proxied':True, 'name': name}
    url = "https://api.cloudflare.com/client/v4/zones/%s/dns_records/%s"%(zone_id, rec_id)
    headers={"X-Auth-Email":email, "X-Auth-Key":api_key}
    return requests.get(url, headers=headers, data="{}").json()["result"]


if __name__ == "__main__":
    try:
        globals().update(get_options())
        ipv4 = get_ip()
        zone_id = get_zone_id()
        record_ids = get_record_ids(zone_id, sub_domain_names)
        try:
            ipv6 = get_ip6()
        except Exception as e:
            logging.exception(e)
            ipv6 = None
            logging.warn("Unable to get IPv6, will ignore AAAA records")

        for name, rec_id, rec_type in get_record_ids(zone_id, sub_domain_names):
            if rec_type == "AAAA" and not ipv6 is None:
                logging.warn("Skipping %s since its a AAAA record and no IPV6 available")
                continue
            print("updating ip for " + name)
            url = "https://api.cloudflare.com/client/v4/zones/%s/dns_records/%s"%(zone_id, rec_id)
            headers={"X-Auth-Email":email, "X-Auth-Key":api_key}
            rec_options = get_rec_options(rec_id, rec_type, name)
            rec_options["content"] = ipv4 if rec_options["type"] == "A" else ipv6
            response = requests.put(url, headers=headers, data=json.dumps(rec_options)).json()
            print("success: %s \n%s"%(response["success"],("" if response["success"] else response["errors"])))
    except Exception as e:
        logging.exception(e)
