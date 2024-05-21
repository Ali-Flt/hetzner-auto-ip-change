from hcloud import Client
from random import randint
from asyncio import sleep
from retry.api import retry_call

def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

class Hetzner:

    def __init__(self, token : str = None, server_name : str = None, used_ips: list = [], logger = None):
        self._client = Client(token=token)
        self._server_name = server_name
        self._already_used_ips = used_ips
        self._logger = logger
            
    async def delete_unassigned_ips(self) -> list:
        all_ips = retry_call(self._client.primary_ips.get_all, delay=1)
        deleted_ips = []
        for ip in all_ips:
            if ip.assignee_id is None:
                deleted_ips.append(ip.ip)
                retry_call(ip.delete, delay=1)
        return deleted_ips

    async def get_current_ip(self) -> str:
        server = self.get_server()
        curr_ip = server.public_net.primary_ipv4
        return curr_ip.ip
    
    async def power_on_server(self) -> None:
        server = self.get_server()
        self._logger.log(f"Powering on the server...")
        retry_call(server.power_on, delay=1)
        await sleep(60)
        
    async def shutdown_server(self) -> None:
        server = self.get_server()
        self._logger.log("Shutting the server down...")
        retry_call(server.shutdown, delay=1)
        
    async def get_server_status(self):
        self._logger.log("Getting server status...")
        return retry_call(self._client.servers.get_by_name, fargs=[self._server_name], delay=1).status
        
    async def change_ip(self) -> str:
        server = self.get_server()
        self._logger.log("Shutting the server down...")
        retry_call(server.shutdown, delay=1)
        self._logger.log("Creating a new IP...")
        new = self._create_new_ip()
        self._logger.log(f"New IP created: {new.ip}")
        new_but_used_ips = []
        while new.ip in self._already_used_ips:
            new_but_used_ips.append(new.name)
            self._logger.log("Creating a new IP...")
            new = self._create_new_ip()
            self._logger.log(f"New IP created: {new.ip}")
        for ip_name in new_but_used_ips:
            ip = retry_call(self._client.primary_ips.get_by_name, fargs=[ip_name], delay=1)
            self._logger.log(f"Deleting IP: {ip.ip}")
            retry_call(ip.delete, delay=1)
            self._logger.log(f"IP deleted: {ip.ip}")
        curr_ip = server.public_net.primary_ipv4
        self._logger.log(f"Unassigning IP: {curr_ip.ip}")
        retry_call(curr_ip.unassign, delay=10)
        self._logger.log(f"IP unassigned: {curr_ip.ip}")
        self._logger.log(f"Deleting IP: {curr_ip.ip}")
        retry_call(curr_ip.delete, delay=1)
        self._logger.log(f"IP deleted: {curr_ip.ip}")
        self._logger.log(f"Assigning IP: {new.ip}")
        retry_call(new.assign, fkwargs={"assignee_id": server.id, "assignee_type": 'server'}, delay=10)
        self._logger.log(f"IP assigned: {new.ip}")
        self._already_used_ips.append(curr_ip.ip)
        self._logger.log(f"Powering on the server...")
        retry_call(server.power_on, delay=1)
        return new.ip
    
    def _create_new_ip(self):
        server = self.get_server()
        return retry_call(self._client.primary_ips.create, fkwargs={"type":'ipv4', "name":f'primary_ip-{random_with_N_digits(9)}', "datacenter":server.datacenter}).primary_ip
    
    def get_server(self):
        return retry_call(self._client.servers.get_by_name, fargs=[self._server_name], delay=1)
