from hcloud import Client
from random import randint
from time import sleep

def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

class Hetzner:

    def __init__(self, token : str = None, server_name : str = None, used_ips: list = []):
        self._client = Client(token=token)
        self._server_name = server_name
        curr_ip = self._client.servers.get_by_name(server_name).public_net.primary_ipv4.ip
        self._already_used_ips = used_ips
        if curr_ip not in self._already_used_ips:
            self._already_used_ips.append(curr_ip)
        
    def change_ip(self):
        server = self._client.servers.get_by_name(self._server_name)
        server.shutdown()
        sleep(60)
        new = self._create_new_ip()
        sleep(5)
        new_but_used_ips = []
        while new.ip in self._already_used_ips:
            new_but_used_ips.append(new.name)
            new = self._create_new_ip()
            sleep(5)
        for ip_name in new_but_used_ips:
            ip = self._client.primary_ips.get_by_name(ip_name)
            ip.delete()
            sleep(5)
        curr_ip = server.public_net.primary_ipv4
        curr_ip.unassign()
        sleep(5)
        curr_ip.delete()
        sleep(5)
        new.assign(assignee_id=server.id, assignee_type='server')
        sleep(5)
        self._already_used_ips.append(new.ip)
        server.power_on()
        return new.ip
    
    def _create_new_ip(self):
        server = self._client.servers.get_by_name(self._server_name)
        return self._client.primary_ips.create(type='ipv4', name=f'primary_ip-{random_with_N_digits(9)}', datacenter=server.datacenter).primary_ip
