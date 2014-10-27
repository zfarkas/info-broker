#
# Copyright (C) 2014 MTA SZTAKI
#
# Key-Value store abstraction for the OCCO InfoBroker
#

__all__ = ['KeyValueStore',
           'KeyValueStoreProvider',
           'DictKVStore']

import occo.infobroker as ib
import occo.util.factory as factory
import yaml
import logging

log = logging.getLogger('occo.infobroker.kvstore')

class KeyValueStore(factory.MultiBackend):
    def __init__(self, **kwargs):
        pass

    def query_item(self, key):
        raise NotImplementedError()
    def set_item(self, key, value):
        raise NotImplementedError()
    def has_key(self, key):
        raise NotImplementedError()

    def __getitem__(self, key):
        return self.query_item(key)
    def __setitem__(self, key, value):
        return self.set_item(key, value)
    def __contains__(self, key):
        return self.has_key(key)

@factory.register(KeyValueStore, 'dict')
class DictKVStore(KeyValueStore):
    def __init__(self, init_dict=None, **kwargs):
	self.backend = dict()
	if init_dict is not None:
	    self.backend.update(init_dict)

    def query_item(self, key):
        return self.backend[key]
    def set_item(self, key, value):
        self.backend[key] = value
    def has_key(self, key):
        return key in self.backend

@ib.provider
class KeyValueStoreProvider(ib.InfoProvider):
    def __init__(self, backend):
        self.backend = backend
    def get(self, key):
        if self._can_immediately_get(key):
            return self._immediate_get(key)
        else:
            return self.backend.query_item(key)
    def can_get(self, key):
        return self._can_immediately_get(key) or self.backend.has_key(key)
    @property
    def iterkeys(self):
        raise NotImplementedError()