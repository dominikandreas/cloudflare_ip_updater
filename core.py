import CloudFlare


class Record:
    def __init__(self, id, name, type, content, **other_props):
        self.id, self.name, self.type, self.ip = id, name, type, content
        self.other_props = other_props

    def get_data(self):
        return {'content': self.ip, 'name': self.name, 'type': self.type, **self.other_props}

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
            raise RuntimeError("Could not find a domain with name %s, found: %s" % (domain_name, str(self.zones)))

    def get_dns_records(self):
        records = [Record(**response) for response in self.cf.zones.dns_records.get(self.zone_id)]
        print("got records: ", ", ".join([r.name for r in records]))
        return records

    def get_single_dns_record(self, sub_domain_name):
        name = (sub_domain_name + '.' + self.zone_name) if len(sub_domain_name) > 0 else self.zone_name
        responses = self.cf.zones.dns_records.get(self.zone_id, params={'name': name})
        if len(responses):
            return Record(**responses[0])
        else:
            print("got empty response for " + name + ". skipping...")

    def update_record(self, record, ip):
        print("updating %-25s to %s... " % (record.name, ip), end="")
        record.ip = ip
        self.cf.zones.dns_records.put(self.zone_id, record.id, data=record.get_data())
        print("done")

    def update_records(self, records, ipv4, ipv6, force=False):
        for record in records:
            if record.type == "A" and ipv4 and (ipv4 != record.ip or force):
                self.update_record(record, ipv4)
            elif record.type == "AAAA" and ipv6 and (ipv6 != record.ip or force):
                self.update_record(record, ipv6)
            else:
                print(("ip %s matches. " % record.ip) if record.ip in (ipv4, ipv6)
                      else "invalid record type", "skipping record", record)

    def update_subdomain_ips(self, ipv4=None, ipv6=None, sub_domains=None, force_updates=False):
        records_to_update = {}
        for record in self.get_dns_records():
            print("handling record %s" % record.name)
            if sub_domains is not None:
                sub_domain_matches = True in [(sub.lower() == record.name.split(".")[0].lower()) for sub in sub_domains]
            else:
                sub_domain_matches = True
            if sub_domain_matches:
                records_to_update[record.name.split(".")[0]] = record
            else:
                print("subdomain %s does not match any of the given records" % record.name)

        for sub_domain_name in (sub_domains or ()):
            if sub_domain_name.lower() not in records_to_update:
                if sub_domain_name == self.zone_name:
                    sub_domain_name = ""
                record = self.get_single_dns_record(sub_domain_name)
                if record is not None:
                    records_to_update[sub_domain_name] = record

        self.update_records(records_to_update.values(), ipv4, ipv6, force=force_updates)