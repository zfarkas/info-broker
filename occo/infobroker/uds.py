#
# Copyright (C) 2014 MTA SZTAKI
#

"""
User Data Store for the OCCO InfoBroker

.. moduleauthor:: Adam Visegradi <adam.visegradi@sztaki.mta.hu>

The UDS is the persistent data storage abstraction in OCCO. It implements data
querying and manipulation primitives based on a key-value store. (Cf.
:ref:`InfoBroker <infobroker>`, which implements dynamic
(run-time/on-demand/etc.) information querying.)
"""

__all__ = ['UDS']

import occo.util.factory as factory
import occo.infobroker as ib
from occo.infobroker.kvstore import KeyValueStore
import logging

log = logging.getLogger('occo.infobroker.uds')

@ib.provider
class UDS(ib.InfoProvider, factory.MultiBackend):
    """
    Implements stored data querying and manupulation primitives used in OCCO.

    It uses the :ref:`abstract factory <factory>` framework so backend-specific
    optimizations are possible.

    :param info_broker: Access to the Information Broker service.
    :type info_broker: :class:`occo.infobroker.provider.InfoProvider`
    :param ** backend_config: Any configuration required by the backend
        :class:`~occo.infobroker.kvstore.KeyValueStore`.

    The ``UDS`` will instantiate its backend upon construction, passing through
    parameters specified in ``backend_config``.

    .. todo:: Instantiating the backend here may not be the best option.
        Probably the caller should instantiate it as necessary, and specify
        only a reference to it.

        There is also information duplication: the protocol is specified for
        both the UDS and the backend kvstore. Maybe it would be possible to
        instantiate the correct UDS based on the *type* of the *backend*. Or
        something like this.
    """
    def __init__(self, info_broker, **backend_config):
        self.kvstore = KeyValueStore(**backend_config)
        self.ib = info_broker

    def infra_description_key(self, infra_id):
        """
        Creates a backend key referencing a specific infrastructure's static
        description.

        :param str infra_id: The internal key of the infrastructure.
        """
        return 'infra:{0!s}:description'.format(infra_id)

    def infra_state_key(self, infra_id):
        """
        Creates a backend key referencing a specific infrastructure's dynamic
        state.

        :param str infra_id: The internal key of the infrastructure.
        """
        return 'infra:{0!s}:state'.format(infra_id)

    def auth_data_key(self, backend_id, user_id):
        """
        Creates a backend key referencing a user's stored authentication
        data to a given OCCO backend (a.k.a.
        :class:`~occo.cloudhandler.cloudhandler.CloudHandler` instance).

        :param str backend_id: The name of the OCCO backend.
        :param str user_id: User id (duh).
        """
        return 'auth:{0!s}:{1!s}'.format(backend_id, user_id)

    def target_key(self, backend_id):
        """
        WTF

        .. todo:: No clue whay this does. See also :meth:`target`.
        """
        return 'backend:{0!s}'.format(backend_id)

    def node_def_key(self, node_type):
        """
        Creates a backend key referencing a node type's definition.

        :param str node_type: The identifier of the node's type (see
            :ref:`nodedescription`\ /``type``.
        """
        return 'node_def:{0!s}'.format(node_type)

    @ib.provides('node.definition.all')
    def all_nodedef(self, node_type):
        """
        .. ibkey::
            Queries all implementations associated with a given node type.

            :param str node_type: The identifier of the node's type (see
                :ref:`nodedescription`\ /``type``.
        """
        return self.kvstore.query_item(self.node_def_key(node_type))

    @ib.provides('node.definition')
    def nodedef(self, node_type, preselected_backend_id=None):
        """
        .. ibkey::
            Queries the implementations of a node type, and chooses exactly
            one of them.

            :param str node_type: The identifier of the node's type (see
                :ref:`nodedescription`\ /``type``.

        .. todo::
            This is not okay. This kind of "brokering" must be done by an
            external service, and should be initiated by the
            :ref:`InfraProcessor <IP>`. It has more information than this
            method.
        """
        return self.get_one_definition(node_type, preselected_backend_id)

    @ib.provides('backends.auth_data')
    def auth_data(self, backend_id, user_id):
        """
        .. ibkey::
             Queries a user's stored authentication data to a given OCCO
             backend (a.k.a.
             :class:`~occo.cloudhandler.cloudhandler.CloudHandler` instance).

            :param str backend_id: The name of the OCCO backend.
            :param str user_id: User id (duh).

        .. todo:: Sphinx structural problem: it cannot solve the class reference
            above. This seems to be a clue...

        """
        return self.kvstore.query_item(
            self.auth_data_key(backend_id, user_id))

    @ib.provides('backends')
    def target(self, backend_id):
        """ WTF

        .. todo:: No clue what this does. See also :meth:`target_key`.
        """
        return self.kvstore.query_item(
            self.target_key(backend_id))

    @ib.provides('infrastructure.static_description')
    def get_static_description(self, infra_id, **kwargs):
        """
        .. ibkey::
             Queries an infrastructure's static description. Used by the
             :ref:`Enactor <enactor>`.

            :param str infra_id: The identifier of the infrastructure.
        """
        return self.kvstore.query_item(
            self.infra_description_key(infra_id))

    @ib.provides('infrastructure.name')
    def infra_name(self, infra_id, **kwargs):
        """
        .. ibkey::
             Queries an infrastructure's name.

            :param str infra_id: The identifier of the infrastructure.
        """
        return self.get_static_description(infra_id).name

    @ib.provides('infrastructure.node_instances')
    def get_infrastructure_state(self, infra_id, **kwargs):
        """
        .. ibkey::
             Queries an infrastructure's dynamic state.

            :param str infra_id: The identifier of the infrastructure.
        """
        return self.kvstore.query_item(self.infra_state_key(infra_id), dict())

    def service_composer_key(self, sc_id):
        """
        Creates a backend key referencing a service composer's instance
        information.

        :param str sc_id: Identifier of the service composer instance.
        """
        return 'service_composer:{0}'.format(sc_id)

    @ib.provides('service_composer.aux_data')
    def get_service_composer_data(self, sc_id, **kwargs):
        """
        .. ibkey::
             Queries information about a service composer instance. The
             content of the information depends on the type of the
             service composer.

            :param str sc_id: The identifier of the service composer instance.
        """
        return self.kvstore.query_item(self.service_composer_key(sc_id), dict())

    def get_one_definition(self, node_type, preselected_backend_id):
        """
        Selects a single implementation from a node type's implementation set.

        .. todo:: Refactor: extract into service. (See :meth:`nodedef`)
        """
        all_definitions = self.all_nodedef(node_type)
        if preselected_backend_id:
            return next(i for i in all_definitions
                        if i['backend_id'] == preselected_backend_id)
        else:
            import random
            return random.choice(all_definitions)

    def add_infrastructure(self, static_description):
        """
        Overridden in a derived class, stores the static description of an
        infrastructure in the key-value store backend.
        """
        raise NotImplementedError()

    def remove_infrastructure(self, infra_id):
        """
        Overridden in a derived class, removes the static description of an
        infrastructure from the key-value store backend.
        """
        raise NotImplementedError()

    def register_started_node(self, infra_id, node_id, instance_data):
        """
        Overridden in a derived class, registers a started node instance in an
        infrastructure's dynamic description.
        """
        raise NotImplementedError()

    def remove_node(self, infra_id, node_name, instance_id):
        """
        Overridden in a derived class, removes a node instance from an
        infrastructure's dynamic description.
        """
        raise NotImplementedError()

@factory.register(UDS, 'dict')
class DictUDS(UDS):
    def add_infrastructure(self, static_description):
        """
        Stores the static description of an infrastructure in the key-value
        store backend.
        """
        self.kvstore.set_item(
            self.infra_description_key(static_description.infra_id),
            static_description)
    def remove_infrastructure(self, infra_id):
        """
        Removes the static description of an infrastructure from the key-value
        store backend.

        .. todo:: Implement.
        """
        raise NotImplementedError()

    def register_started_node(self, infra_id, node_name, instance_data):
        """
        Registers a started node instance in an infrastructure's dynamic
        description.
        """
        node_id = instance_data['node_id']
        infra_key = self.infra_state_key(infra_id)
        infra_state = self.get_infrastructure_state(infra_id)
        node_list = infra_state.setdefault(node_name, dict())
        node_list[node_id] = instance_data
        self.kvstore.set_item(infra_key, infra_state)

    def remove_node(self, infra_id, node_name, instance_id):
        """
        Removes a node instance from an infrastructure's dynamic description.
        """
        raise NotImplementedError()

@factory.register(UDS, 'redis')
class RedisUDS(UDS):
    def get_one_definition(self, node_type, preselected_backend_id):
        # TODO implement exploiting redis features
        # TODO call super() instead of passing until implemented properly
        pass

    def add_infrastructure(self, static_description):
        """
        Stores the static description of an infrastructure in the key-value
        store backend.
        """
        self.kvstore.set_item(
            self.infra_description_key(static_description.infra_id),
            static_description)

    def remove_infrastructure(self, infra_id):
        """
        Removes the static description of an infrastructure from the key-value
        store backend.

        .. todo:: Implement.
        """
        raise NotImplementedError()

    def register_started_node(self, infra_id, node_name, instance_data):
        """
        Registers a started node instance in an infrastructure's dynamic
        description.
        """
        node_id = instance_data['node_id']
        infra_key = self.infra_key(infra_id, True)
        infra_state = self.infra_state(infra_id)
        node_list = infra_state.setdefault(node_name, dict())
        node_list[node_id] = instance_data
        self.kvstore.set_item(infra_key, infra_state)

    def remove_node(self, infra_id, node_name, instance_id):
        """
        Removes a node instance from an infrastructure's dynamic description.
        """
        raise NotImplementedError()
