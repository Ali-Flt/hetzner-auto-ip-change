from hcloud import Client
from random import randint
from time import sleep
from datetime import datetime

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
            
    def delete_unassigned_ips(self):
        all_ips = self._client.primary_ips.get_all()
        deleted_ips = []
        for ip in all_ips:
            if ip.assignee_id is None:
                deleted_ips.append(ip.ip)
                ip.delete()
                sleep(10)
        return deleted_ips
        
    @staticmethod
    def _info_logger_(log):
        with open(f"hetzner_log_{str(datetime.now().date())}.txt", "a") as file:
            file.write(str(datetime.now().time()) + ":\n" + log + "\n")

    def change_ip(self):
        server = self._client.servers.get_by_name(self._server_name)
        self._info_logger_("Shutting the server down...")
        server.shutdown()
        sleep(60)
        self._info_logger_("Creating a new IP...")
        new = self._create_new_ip()
        sleep(10)
        self._info_logger_(f"New IP created: {new.ip}")
        new_but_used_ips = []
        while new.ip in self._already_used_ips:
            new_but_used_ips.append(new.name)
            self._info_logger_("Creating a new IP...")
            new = self._create_new_ip()
            sleep(10)
            self._info_logger_(f"New IP created: {new.ip}")
        for ip_name in new_but_used_ips:
            ip = self._client.primary_ips.get_by_name(ip_name)
            self._info_logger_(f"Deleting IP: {ip.ip}")
            ip.delete()
            sleep(10)
            self._info_logger_(f"IP deleted: {ip.ip}")
        curr_ip = server.public_net.primary_ipv4
        self._info_logger_(f"Unassigning IP: {curr_ip.ip}")
        curr_ip.unassign()
        sleep(10)
        self._info_logger_(f"IP unassigned: {curr_ip.ip}")
        self._info_logger_(f"Deleting IP: {curr_ip.ip}")
        curr_ip.delete()
        sleep(10)
        self._info_logger_(f"IP deleted: {curr_ip.ip}")
        self._info_logger_(f"Assigning IP: {new.ip}")
        new.assign(assignee_id=server.id, assignee_type='server')
        sleep(10)
        self._info_logger_(f"IP assigned: {new.ip}")
        self._already_used_ips.append(new.ip)
        self._info_logger_(f"Powering on the server...")
        server.power_on()
        return new.ip
    
    def _create_new_ip(self):
        server = self._client.servers.get_by_name(self._server_name)
        return self._client.primary_ips.create(type='ipv4', name=f'primary_ip-{random_with_N_digits(9)}', datacenter=server.datacenter).primary_ip
    
