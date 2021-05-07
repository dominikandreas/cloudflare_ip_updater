# cloudflare ip updater

Updates the IPs for several DNS records on CloudFlare using their native API

# Howto:

* clone repo and setup dependencies

  ```bash
  git clone git@github.com:dominikandreas/cloudflare_ip_updater.git
  cd cloudflare_ip_updater
  python3 -m pip install -r requirements.txt
  ```
  
* create a config.yaml:

    ```bash
    nano config.yaml
    ```

    populate the config file with the following information:
    ```yaml
    api_key: ...  # your api_key (get it from your cloudflare account console)
    email: ...    # your cloudflare account email
    domain_name: ...  # the domain name to target
    ipv4: true        # whether to update ipv4 records
    ipv6: false       # whether to update ipv6 records
    sub_domains:  # the sub domain names to include in the update
      - ...     
      - ... 
    ```
    (`ctr+x`, `enter` to write file and exit nano)

* run the cloudflare updater
  ```bash
  python3 main.py
  ```
  to disable infinite loop:
  ```bash
  python3 main.py --loop false
  ```
* Alternatively: Update only a specific domain to a target ip (ip is optional)
  ```bash
  python3 main.py --subdomain www --domain mydomain.de --ipv4 1.1.1.1
  ```
  
## Use crontab to run the updater every 5 minutes:
* ``crontab -e``
* add the following line: ``*/5 * * * * python3 /path_to_cloudflare_ip_updater/main.py``

I'm using this personally, but can't guarantee for anything. Code should be simple enough to adapt though should you run into any issues..
