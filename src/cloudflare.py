import CloudFlare

class CF:

    def __init__(self, token : str = None, zone_name : str = None, dns_name : str = None, proxied : bool = False):
        self._cf = CloudFlare.CloudFlare(token=token)
        self._zone_name = zone_name
        self._dns_name = dns_name
        self._zone_id = self._cf.zones.get(params={'name': zone_name})[0]['id']
        self._proxied = proxied
        
    def _delete_records_(self):
        dns_records = self._cf.zones.dns_records.get(self._zone_id, params={'name':self._dns_name + '.' + self._zone_name})
        for dns_record in dns_records:
            dns_record_id = dns_record['id']
            self._cf.zones.dns_records.delete(self._zone_id, dns_record_id)
        
    def _create_record_(self, ip : str):
        dns_record = {'name' : self._dns_name, 'type' : 'A', 'content' : ip, 'proxied': self._proxied}
        self._cf.zones.dns_records.post(self._zone_id, data=dns_record)
        
    def update_record(self, ip : str):
        self._delete_records_()
        self._create_record_(ip=ip)
