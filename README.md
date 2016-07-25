# cloudflare_ip_updater

Updates the IPs for several DNS records on CloudFlare using their native API

# Howto:
* run ``python main.py``
* it will ask you for the necessary info, such as email, api and subdomains
* see if it works

## Use crontab to run the updater every 5 minutes:
* ``crontab -e``
* add the following line: ``*/5 * * * * python /path_to_cloudflare_ip_updater/main.py``

