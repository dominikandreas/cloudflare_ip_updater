import json
import os
import sys
from urllib.request import urlopen


def get_ipv6():
    # CAUTION! DIRTY INSUFFICIENTLY TESTED HACK INCOMING
    try:
        def get_res(command):
            return os.popen(command).read().split("\n")

        ips = get_res("/sbin/ifconfig eth0 |  awk '/inet6/{print $3}'")
        scopes = get_res("/sbin/ifconfig eth0 |  awk '/inet6/{print $4}'")
        if len(sys.argv) > 1 and sys.argv[1] == "debug":
            print("ips, scopes:", ips, scopes)
        ip = [ip for ip, scope in zip(ips, scopes) if "Global" in scope][0]
        if ":" not in ip:
            raise RuntimeError("got invalid ipv6: %s" % ip)
        return ip.split("/")[0]
    except:
        pass


def get_ipv4():
    try:
        return json.load(urlopen('http://api.ipify.org/?format=json'))['ip']
    except:
        try:
            return json.load(urlopen('http://jsonip.com'))['ip']
        except:
            return json.load(urlopen('http://httpbin.org/ip'))['origin']