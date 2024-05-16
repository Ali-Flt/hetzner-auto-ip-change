from redis import Redis
import pickle

parameters = ['used_ips']
my_db = None
prefix = 'hetzner_'
cache_parameters = {}

def singleton():
    global my_db
    if my_db is None:
        my_db = Redis(host='127.0.0.1', port=6379)
    return my_db

def get_default(key):
    if key == 'used_ips':
        return []
    return None

def get_parameter(key):
    if key in parameters:
        my_db = singleton()
        data = my_db.get(prefix + key)
        if data is None:
            data = get_default(key)
            my_db.set(prefix + key, pickle.dumps(data))
            return data
        return pickle.loads(data)
    else:
        return None

def set_parameter(key, value):
    if key in parameters:
        singleton().set(prefix + key, pickle.dumps(value))
        return value
    else:
        return None

def reset_parameters(keys=None):
    if keys is None:
        keys = parameters
    for key in keys:
        set_parameter(key, get_default(key))
        
def shutdown():
    my_db = singleton()
    my_db.shutdown()
