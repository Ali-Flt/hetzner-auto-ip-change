from hcloud import Client
from random import randint
from asyncio import sleep

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
        all_ips = self._client.primary_ips.get_all()
        deleted_ips = []
        for ip in all_ips:
            if ip.assignee_id is None:
                deleted_ips.append(ip.ip)
                ip.delete()
                await sleep(10)
        return deleted_ips

    async def get_current_ip(self) -> str:
        server = self._client.servers.get_by_name(self._server_name)
        curr_ip = server.public_net.primary_ipv4
        return curr_ip.ip
    
    async def power_on_server(self) -> None:
        server = self._client.servers.get_by_name(self._server_name)
        self._logger.log(f"Powering on the server...")
        server.power_on()
        await sleep(60)
        
    async def shutdown_server(self) -> None:
        server = self._client.servers.get_by_name(self._server_name)
        self._logger.log("Shutting the server down...")
        server.shutdown()
        await sleep(60)
        
    async def get_server_status(self):
        self._logger.log("Getting server status...")
        return self._client.servers.get_by_name(self._server_name).status
        
    async def change_ip(self) -> str:
        server = self._client.servers.get_by_name(self._server_name)
        self._logger.log("Shutting the server down...")
        server.shutdown()
        await sleep(60)
        self._logger.log("Creating a new IP...")
        new = self._create_new_ip()
        await sleep(10)
        self._logger.log(f"New IP created: {new.ip}")
        new_but_used_ips = []
        while new.ip in self._already_used_ips:
            new_but_used_ips.append(new.name)
            self._logger.log("Creating a new IP...")
            new = self._create_new_ip()
            await sleep(10)
            self._logger.log(f"New IP created: {new.ip}")
        for ip_name in new_but_used_ips:
            ip = self._client.primary_ips.get_by_name(ip_name)
            self._logger.log(f"Deleting IP: {ip.ip}")
            ip.delete()
            await sleep(10)
            self._logger.log(f"IP deleted: {ip.ip}")
        curr_ip = server.public_net.primary_ipv4
        self._logger.log(f"Unassigning IP: {curr_ip.ip}")
        curr_ip.unassign()
        await sleep(10)
        self._logger.log(f"IP unassigned: {curr_ip.ip}")
        self._logger.log(f"Deleting IP: {curr_ip.ip}")
        curr_ip.delete()
        await sleep(10)
        self._logger.log(f"IP deleted: {curr_ip.ip}")
        self._logger.log(f"Assigning IP: {new.ip}")
        new.assign(assignee_id=server.id, assignee_type='server')
        await sleep(10)
        self._logger.log(f"IP assigned: {new.ip}")
        self._already_used_ips.append(curr_ip.ip)
        self._logger.log(f"Powering on the server...")
        server.power_on()
        return new.ip
    
    def _create_new_ip(self):
        server = self._client.servers.get_by_name(self._server_name)
        return self._client.primary_ips.create(type='ipv4', name=f'primary_ip-{random_with_N_digits(9)}', datacenter=server.datacenter).primary_ip
    
