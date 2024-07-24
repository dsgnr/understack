import json
import logging
from pprint import pprint
import typing
import uuid

import neutron_lib.api.definitions.portbindings as portbindings
from neutron_lib.plugins.ml2.api import MechanismDriver
from neutron_lib.plugins.ml2.api import NetworkContext
from neutron_lib.plugins.ml2.api import PortContext
from neutron_lib.plugins.ml2.api import SubnetContext
from neutron_understack.argo.workflows import ArgoClient
from oslo_config import cfg

LOG = logging.getLogger(__name__)

def setup_conf():
    grp = cfg.OptGroup("ml2_type_understack")
    opts = [
        cfg.StrOpt(
            "provisioning_network",
            help="provisioning_network ID as configured in ironic.conf",
        ),
        cfg.StrOpt(
            "argo_workflow_sa",
            default="workflow",
            help="ServiceAccount to submit Workflow as",
        ),
        cfg.StrOpt(
            "argo_api_url",
            default="https://argo-server.argo.svc.cluster.local:2746",
            help="URL of the Argo Server API",
        ),
        cfg.StrOpt(
            "argo_namespace",
            default="argo-events",
            help="Namespace to submit the Workflows to",
        ),
        cfg.IntOpt(
            "argo_max_attempts",
            default=15,
            help="Number of tries to retrieve the Workflow run result. Sleeps 5 seconds between attempts.",
        ),
        cfg.BoolOpt(
            "argo_dry_run", default=True, help="Call Undersync with dry-run mode"
        ),
        cfg.BoolOpt("argo_force", default=False, help="Call Undersync with force mode"),
    ]
    cfg.CONF.register_group(grp)
    cfg.CONF.register_opts(opts, group=grp)


setup_conf()

argo_token = None
with open("/run/secrets/kubernetes.io/serviceaccount/token") as token_file:
    argo_token = token_file.read()

argo_client = ArgoClient(
    argo_token,
    logger=LOG,
    api_url=cfg.CONF.ml2_type_understack.argo_api_url,
    namespace=cfg.CONF.ml2_type_understack.argo_namespace,
)


def dump_context(
    context: typing.Union[NetworkContext, SubnetContext, PortContext],
) -> dict:
    # RESOURCE_ATTRIBUTE_MAP
    # from neutron_lib.api.definitions import network, subnet, port, portbindings
    # The properties of a NetworkContext.current are defined in
    #   network.RESOURCE_ATTRIBUTE_MAP
    # The properties of a SubnetContext.current are defined in
    #   subnet.RESOURCE_ATTRIBUTE_MAP
    # The properties of a PortContext.current are defined in
    #   port.RESOURCE_ATTRIBUTE_MAP
    attr_map = {
        NetworkContext: ("current", "original", "network_segments"),
        SubnetContext: ("current", "original"),
        PortContext: (
            "current",
            "original",
            "status",
            "original_status",
            "network",
            "binding_levels",
            "original_binding_levels",
            "top_bound_segment",
            "original_top_bound_segment",
            "bottom_bound_segment",
            "original_bottom_bound_segment",
            "host",
            "original_host",
            "vif_type",
            "original_vif_type",
            "vif_details",
            "original_vif_details",
            "segments_to_bind",
        ),
    }
    retval = {"errors": [], "other_attrs": []}
    if isinstance(context, NetworkContext):
        attrs_to_dump = attr_map[NetworkContext]
    elif isinstance(context, SubnetContext):
        attrs_to_dump = attr_map[SubnetContext]
    elif isinstance(context, PortContext):
        attrs_to_dump = attr_map[PortContext]
    else:
        retval["errors"].append(f"Error: unknown object type {type(context)}")
        return retval

    attrs = vars(context)
    for attr in attrs:
        if attr in attrs_to_dump:
            try:
                val = getattr(context, attr)
                retval.update({attr: val})
            except Exception as e:
                retval["errors"].append(f"Error dumping {attr}: {str(e)}")
        else:
            retval["other_attrs"].append(attr)
    return retval


def log_call(
    method: str, context: typing.Union[NetworkContext, SubnetContext, PortContext]
    method: str, context: NetworkContext | SubnetContext | PortContext
) -> None:
    data = dump_context(context)
    data.update({"method": method})
    try:
        jsondata = json.dumps(data)
    except Exception as e:
        LOG.error(
            "failed to dump %s object to JSON on %s call: %s",
            str(context),
            method,
            str(e),
        )
        return
    LOG.info("%s method called with data: %s", method, jsondata)
    LOG.debug("%s method executed with context:", method)
    # for chunk in chunked(str(context.current), 750):
    pprint(context.current)


def chunked(inputstr, length):
    return (inputstr[0 + i : length + i] for i in range(0, len(inputstr), length))


class UnderstackDriver(MechanismDriver):
    # See MechanismDriver docs for resource_provider_uuid5_namespace
    resource_provider_uuid5_namespace = uuid.UUID(
        "6eae3046-4072-11ef-9bcf-d6be6370a162"
    )

    def initialize(self):
        pass

    def create_network_precommit(self, context):
        log_call("create_network_precommit", context)

    def create_network_postcommit(self, context):
        log_call("create_network_postcommit", context)

    def update_network_precommit(self, context):
        log_call("update_network_precommit", context)

    def update_network_postcommit(self, context):
        log_call("update_network_postcommit", context)

    def delete_network_precommit(self, context):
        log_call("delete_network_precommit", context)

    def delete_network_postcommit(self, context):
        log_call("delete_network_postcommit", context)

    def create_subnet_precommit(self, context):
        log_call("create_subnet_precommit", context)

    def create_subnet_postcommit(self, context):
        log_call("create_subnet_postcommit", context)

    def update_subnet_precommit(self, context):
        log_call("update_subnet_precommit", context)

    def update_subnet_postcommit(self, context):
        log_call("update_subnet_postcommit", context)

    def delete_subnet_precommit(self, context):
        log_call("delete_subnet_precommit", context)

    def delete_subnet_postcommit(self, context):
        log_call("delete_subnet_postcommit", context)

    def create_port_precommit(self, context):
        log_call("create_port_precommit", context)

    def create_port_postcommit(self, context):
        log_call("create_port_postcommit", context)

    def update_port_precommit(self, context):
        log_call("update_port_precommit", context)

    def update_port_postcommit(self, context):
        log_call("update_port_postcommit", context)

    def delete_port_precommit(self, context):
        log_call("delete_port_precommit", context)

    def delete_port_postcommit(self, context):
        log_call("delete_port_postcommit", context)

    def bind_port(self, context):
        self._move_to_network(context)
        log_call("bind_port", context)

    def check_vlan_transparency(self, context):
        log_call("check_vlan_transparency", context)

    def __network_name(self, network_id: str):
        if network_id == cfg.CONF.ml2_type_understack.provisioning_network:
            return "provisioning"
        else:
            return "tenant"

    def _move_to_network(self, context):
        device_uuid = context.current["binding:host_id"]
        network_name = self.__network_name(context.current["network_id"])
        LOG.debug(f"Selected {network_name=} for {device_uuid=}")

        result = argo_client.submit_wait(
            template_name="undersync-device",
            entrypoint="trigger-undersync",
            parameters={
                "device_uuid": device_uuid,
                "network_name": network_name,
                "dry_run": cfg.CONF.ml2_type_understack.argo_dry_run,
                "force": cfg.CONF.ml2_type_understack.argo_force,
            },
            service_account=cfg.CONF.ml2_type_understack.argo_workflow_sa,
            max_attempts=cfg.CONF.ml2_type_understack.argo_max_attempts,
        )
        LOG.info(f"Binding workflow {result}")
        if result == "Succeeded":
            context.current["bind:vif_type"] = portbindings.VIF_TYPE_OTHER
        else:
            context.current["bind:vif_type"] = portbindings.VIF_TYPE_BINDING_FAILED

        return context
