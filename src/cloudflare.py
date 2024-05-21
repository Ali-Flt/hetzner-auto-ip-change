import CloudFlare

class CF:

    def __init__(self, token : str = None, zone_name : str = None, dns_name_proxied : str = None, dns_name_not_proxied : str = None, logger = None) -> None:
        self._cf = CloudFlare.CloudFlare(token=token)
        self._zone_name = zone_name
        self._dns_name_proxied = dns_name_proxied
        self._dns_name_not_proxied = dns_name_not_proxied
        self._zone_id = self._cf.zones.get(params={'name': zone_name})[0]['id']
        self._logger = logger
        
        
    def _delete_records_(self, dns_name: str):
        params = {'name':dns_name + '.' + self._zone_name}
        dns_records = self._cf.zones.dns_records.get(self._zone_id, params=params)
        self._logger.log(f"Deleting DNS records: {params}")
        for dns_record in dns_records:
            dns_record_id = dns_record['id']
            self._cf.zones.dns_records.delete(self._zone_id, dns_record_id)
        
    def _create_record_(self, ip : str, dns_name: str, proxied: bool):
        dns_record = {'name' : dns_name, 'type' : 'A', 'content' : ip, 'proxied': proxied}
        self._logger.log(f"Creating DNS record: {dns_record}")
        self._cf.zones.dns_records.post(self._zone_id, data=dns_record)
        
    async def update_record(self, ip : str):
        self._delete_records_(dns_name=self._dns_name_proxied)
        self._delete_records_(dns_name=self._dns_name_not_proxied)
        self._create_record_(ip=ip, dns_name=self._dns_name_proxied, proxied=True)
        self._create_record_(ip=ip, dns_name=self._dns_name_not_proxied, proxied=False)
