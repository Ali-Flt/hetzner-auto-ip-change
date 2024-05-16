import argparse
import yaml
from src.cloudflare import CF
from src.hetzner import Hetzner
from src import database

parser = argparse.ArgumentParser()
parser.add_argument('--config', default='config.yaml')
parser.add_argument('--change_ip', dest='change_ip', action='store_const', const=True, default=False)
parser.add_argument('--reset_db', dest='reset_db', action='store_const', const=True, default=False)
args = parser.parse_args()
config = {}
with open(args.config) as f:
    config = yaml.load(f, Loader=yaml.loader.SafeLoader)

if __name__ == '__main__':
    if args.change_ip:
        hetzner = Hetzner(token=config['hetzner']['token'], 
                        server_name=config['hetzner']['server_name'],
                        used_ips=database.get_parameter('used_ips'))
        cf = CF(token=config['cloudflare']['token'], 
                zone_name=config['cloudflare']['zone_name'], 
                dns_name=config['cloudflare']['dns_name'],
                proxied=config['cloudflare']['proxied'])
        new_ip = hetzner.change_ip()
        database.set_parameter('used_ips', hetzner._already_used_ips)
        cf.update_record(ip = new_ip)
        print(f"Successfully changed the ip to {new_ip}")
        print(f"used_ips: {database.get_parameter('used_ips')}")
    elif args.reset_db:
        database.reset_parameters()
