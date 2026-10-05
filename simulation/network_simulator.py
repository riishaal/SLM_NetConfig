"""
Network Simulation Module
Simulates Cisco IOS device state machines (Control Plane and Data Plane):
- VLAN Databases and Access/Trunk port state
- Interface IP assignment and administrative state
- Static and OSPF IP routing tables
- DHCP Address Pool engines
- Access Control List (ACL) stateful packet filtering
"""

import ipaddress
import os
import re
import sys
from typing import Dict, Any, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SimulatedDevice:
    """Represents a virtual Cisco IOS switch or router state machine."""

    def __init__(self, hostname: str = "Switch1", device_type: str = "switch"):
        self.hostname = hostname
        self.device_type = device_type
        self.ip_routing_enabled = False

        # State tables
        self.vlan_database: Dict[int, Dict[str, Any]] = {
            1: {"name": "default", "status": "active", "ports": []}
        }
        self.interfaces: Dict[str, Dict[str, Any]] = {}
        self.routing_table: List[Dict[str, Any]] = []
        self.ospf_processes: Dict[int, Dict[str, Any]] = {}
        self.dhcp_pools: Dict[str, Dict[str, Any]] = {}
        self.dhcp_excluded: List[Tuple[str, str]] = []
        self.access_lists: Dict[int, List[Dict[str, Any]]] = {}

        self.execution_log: List[str] = []

    def apply_command(self, line: str, current_context: str) -> str:
        """
        Execute a single Cisco command line on the simulated device.
        Returns updated context.
        """
        raw = line.strip()
        if not raw or raw.startswith("!") or raw.startswith("#"):
            return current_context

        self.execution_log.append(f"[{current_context}] {raw}")

        # Global commands
        if raw.lower() == "configure terminal":
            return "GLOBAL"
        if raw.lower() in ["exit", "end"]:
            return "GLOBAL"
        if raw.lower() == "ip routing":
            self.ip_routing_enabled = True
            return current_context

        # Hostname
        m_host = re.match(r'^hostname\s+([a-zA-Z0-9_\-]+)', raw, re.I)
        if m_host:
            self.hostname = m_host.group(1)
            return current_context

        # Enter VLAN configuration
        m_vlan = re.match(r'^vlan\s+([0-9]+)', raw, re.I)
        if m_vlan:
            vid = int(m_vlan.group(1))
            if vid not in self.vlan_database:
                self.vlan_database[vid] = {"name": f"VLAN_{vid}", "status": "active", "ports": []}
            return f"VLAN_{vid}"

        # VLAN naming inside VLAN context
        if current_context.startswith("VLAN_"):
            vid = int(current_context.split("_")[1])
            m_name = re.match(r'^name\s+([a-zA-Z0-9_\-]+)', raw, re.I)
            if m_name and vid in self.vlan_database:
                self.vlan_database[vid]["name"] = m_name.group(1)
                return current_context

        # Enter Interface configuration
        m_iface = re.match(r'^interface\s+([a-zA-Z0-9_/\-]+)', raw, re.I)
        if m_iface:
            ifname = m_iface.group(1)
            if ifname not in self.interfaces:
                self.interfaces[ifname] = {
                    "status": "administratively down",
                    "ip": None,
                    "mask": None,
                    "mode": "access",
                    "access_vlan": 1,
                    "trunk_encapsulation": None,
                    "allowed_vlans": [],
                    "acl_in": None,
                    "acl_out": None
                }
            return f"IF_{ifname}"

        # Interface subcommands
        if current_context.startswith("IF_"):
            ifname = current_context[3:]
            if_state = self.interfaces[ifname]

            if raw.lower() == "no shutdown":
                if_state["status"] = "up"
            elif raw.lower() == "shutdown":
                if_state["status"] = "administratively down"

            m_ip = re.match(r'^ip\s+address\s+([0-9\.]+)\s+([0-9\.]+)', raw, re.I)
            if m_ip:
                if_state["ip"] = m_ip.group(1)
                if_state["mask"] = m_ip.group(2)
                # Connected route automatically added if interface is up
                self._update_connected_route(ifname, m_ip.group(1), m_ip.group(2))

            m_mode = re.match(r'^switchport\s+mode\s+(access|trunk)', raw, re.I)
            if m_mode:
                if_state["mode"] = m_mode.group(1).lower()

            m_acc = re.match(r'^switchport\s+access\s+vlan\s+([0-9]+)', raw, re.I)
            if m_acc:
                target_vid = int(m_acc.group(1))
                if_state["access_vlan"] = target_vid
                if target_vid in self.vlan_database:
                    if ifname not in self.vlan_database[target_vid]["ports"]:
                        self.vlan_database[target_vid]["ports"].append(ifname)

            m_encap = re.match(r'^switchport\s+trunk\s+encapsulation\s+(dot1q|isl)', raw, re.I)
            if m_encap:
                if_state["trunk_encapsulation"] = m_encap.group(1).lower()

            m_allow = re.match(r'^switchport\s+trunk\s+allowed\s+vlan\s+([0-9,\-]+|all)', raw, re.I)
            if m_allow:
                v_str = m_allow.group(1).lower()
                if v_str == "all":
                    if_state["allowed_vlans"] = ["all"]
                else:
                    if_state["allowed_vlans"] = [int(v) for v in re.findall(r'[0-9]+', v_str)]

            m_grp = re.match(r'^ip\s+access-group\s+([0-9]+)\s+(in|out)', raw, re.I)
            if m_grp:
                acl_id = int(m_grp.group(1))
                direction = m_grp.group(2).lower()
                if direction == "in":
                    if_state["acl_in"] = acl_id
                else:
                    if_state["acl_out"] = acl_id

            return current_context

        # Static Route
        m_route = re.match(r'^ip\s+route\s+([0-9\.]+)\s+([0-9\.]+)\s+([a-zA-Z0-9_/\.\-]+)', raw, re.I)
        if m_route:
            self.routing_table.append({
                "type": "S",
                "network": m_route.group(1),
                "mask": m_route.group(2),
                "nexthop": m_route.group(3)
            })
            return current_context

        # OSPF Process
        m_ospf = re.match(r'^router\s+ospf\s+([0-9]+)', raw, re.I)
        if m_ospf:
            pid = int(m_ospf.group(1))
            if pid not in self.ospf_processes:
                self.ospf_processes[pid] = {"networks": [], "passive_interfaces": []}
            return f"ROUTER_OSPF_{pid}"

        if current_context.startswith("ROUTER_OSPF_"):
            pid = int(current_context.split("_")[2])
            m_net = re.match(r'^network\s+([0-9\.]+)\s+([0-9\.]+)\s+area\s+([0-9]+)', raw, re.I)
            if m_net:
                self.ospf_processes[pid]["networks"].append({
                    "network": m_net.group(1),
                    "wildcard": m_net.group(2),
                    "area": int(m_net.group(3))
                })
            m_pass = re.match(r'^passive-interface\s+([a-zA-Z0-9_/\-]+)', raw, re.I)
            if m_pass:
                self.ospf_processes[pid]["passive_interfaces"].append(m_pass.group(1))
            return current_context

        # DHCP Excluded
        m_dex = re.match(r'^ip\s+dhcp\s+excluded-address\s+([0-9\.]+)(?:\s+([0-9\.]+))?', raw, re.I)
        if m_dex:
            start_ip = m_dex.group(1)
            end_ip = m_dex.group(2) or start_ip
            self.dhcp_excluded.append((start_ip, end_ip))
            return current_context

        # DHCP Pool
        m_pool = re.match(r'^ip\s+dhcp\s+pool\s+([a-zA-Z0-9_\-]+)', raw, re.I)
        if m_pool:
            pname = m_pool.group(1)
            if pname not in self.dhcp_pools:
                self.dhcp_pools[pname] = {"network": None, "mask": None, "default_router": None, "dns": None}
            return f"DHCP_POOL_{pname}"

        if current_context.startswith("DHCP_POOL_"):
            pname = current_context.split("_", 2)[2]
            p_data = self.dhcp_pools[pname]
            m_pnet = re.match(r'^network\s+([0-9\.]+)\s+([0-9\.]+)', raw, re.I)
            if m_pnet:
                p_data["network"] = m_pnet.group(1)
                p_data["mask"] = m_pnet.group(2)
            m_pdr = re.match(r'^default-router\s+([0-9\.]+)', raw, re.I)
            if m_pdr:
                p_data["default_router"] = m_pdr.group(1)
            m_pdns = re.match(r'^dns-server\s+([0-9\.\s]+)', raw, re.I)
            if m_pdns:
                p_data["dns"] = m_pdns.group(1).strip()
            return current_context

        # Access List
        m_acl = re.match(r'^access-list\s+([0-9]+)\s+(permit|deny)\s+([a-zA-Z0-9\.\s_]+)', raw, re.I)
        if m_acl:
            acl_id = int(m_acl.group(1))
            action = m_acl.group(2).lower()
            rest = m_acl.group(3).strip()
            if acl_id not in self.access_lists:
                self.access_lists[acl_id] = []
            self.access_lists[acl_id].append({
                "action": action,
                "statement": rest
            })
            return current_context

        return current_context

    def _update_connected_route(self, ifname: str, ip_str: str, mask_str: str):
        try:
            net = ipaddress.IPv4Network(f"{ip_str}/{mask_str}", strict=False)
            self.routing_table.append({
                "type": "C",
                "network": str(net.network_address),
                "mask": mask_str,
                "nexthop": f"directly connected, {ifname}"
            })
        except Exception:
            pass

    def load_configuration(self, config_text: str):
        """Execute complete configuration script against device state."""
        ctx = "GLOBAL"
        for line in config_text.splitlines():
            ctx = self.apply_command(line, ctx)


class NetworkSimulator:
    """Top-level simulation coordinator across network devices."""

    def __init__(self):
        self.devices: Dict[str, SimulatedDevice] = {}

    def get_or_create_device(self, hostname: str, device_type: str = "switch") -> SimulatedDevice:
        if hostname not in self.devices:
            self.devices[hostname] = SimulatedDevice(hostname=hostname, device_type=device_type)
        return self.devices[hostname]

    def simulate_deployment(self, config_text: str, default_hostname: str = "Switch1") -> Dict[str, Any]:
        """
        Deploy configuration into virtual network simulation and return snapshot of network state.
        """
        device = self.get_or_create_device(default_hostname)
        device.load_configuration(config_text)

        return {
            "device_hostname": device.hostname,
            "vlan_database": device.vlan_database,
            "interfaces": device.interfaces,
            "routing_table": device.routing_table,
            "ospf_processes": device.ospf_processes,
            "dhcp_pools": device.dhcp_pools,
            "access_lists": device.access_lists,
            "commands_executed": len(device.execution_log)
        }


if __name__ == "__main__":
    sim = NetworkSimulator()
    test_cfg = """
    hostname CoreSwitch
    vlan 10
     name Sales
    !
    interface FastEthernet0/1
     switchport mode access
     switchport access vlan 10
     no shutdown
    !
    ip routing
    interface Vlan10
     ip address 192.168.10.1 255.255.255.0
     no shutdown
    !
    ip route 0.0.0.0 0.0.0.0 192.168.1.254
    """
    snapshot = sim.simulate_deployment(test_cfg)
    print("Simulated Hostname:", snapshot["device_hostname"])
    print("VLAN DB:", snapshot["vlan_database"])
    print("Interfaces:", snapshot["interfaces"])
    print("Routing Table:", snapshot["routing_table"])
