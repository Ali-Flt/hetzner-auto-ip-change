# hetzner-auto-ip-change
This repository contains scripts to use Hetzner and Cloudflare API to automatically renew the ipv4 of a cloud server.

# How to build
```shell
./build_docker.sh
```
# Config file
```yaml
hetzner:
  token: 'some_token'
  server_name: 'hetzner_server_name'

cloudflare:
  token: 'some_token'
  zone_name: 'domain_name'
  dns_name_proxied: 'subdomain_name'
  dns_name_not_proxied: 'subdomain_name2'
```
# Commands:
To change the ip:
```shell
cmd="--change_ip" docker compose up
```
To reset the used ips stored in the db:
```shell
cmd="--reset_db" docker compose up
```