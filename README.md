# cloudflare ip updater

Updates the IPs for several DNS records on CloudFlare using their native API

# Howto:

* create a config.yaml with contents:
```yaml
some_name: # you can enter any name you want
  api_key: ...  # your api_key (get it from your cloudflare account console)
  email: ...    # your cloudflare account email
  domain_name: ...  # the domain name to target
  ipv4: true        # whether to update ipv4 records
  ipv6: false       # whether to update ipv6 records
  sub_domains: [...] # the sub domain names to include in the update
```

* run 

  ```bash
  git clone git@github.com:dominikandreas/cloudflare_ip_updater.git
  python3 cloudflare_ip_updater/main.py
  ```
  
## Use crontab to run the updater every 5 minutes:
* ``crontab -e``
* add the following line: ``*/5 * * * * python3 /path_to_cloudflare_ip_updater/main.py``

I'm using this personally, but can't guarantee for anything. Code should be simple enough to adapt though should you run into any issues..
