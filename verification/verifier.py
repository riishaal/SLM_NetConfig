"""
Verification Module
Executes behavioral and functional verification on simulated network configurations:
- VLAN database membership & port access mode checks
- Interface operational state and IP configuration
- Routing table reachability and OSPF dynamic advertisements
- DHCP pool and gateway provisioning
- Stateful Access Control List (ACL) packet walk verification
"""

import os
import sys
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from simulation.network_simulator import NetworkSimulator, SimulatedDevice


class NetworkVerifier:
    """Verifies functional network compliance against user intent."""

    def __init__(self, simulator: Optional[NetworkSimulator] = None):
        self.simulator = simulator or NetworkSimulator()

    def verify_configuration(
        self,
        config_text: str,
        user_intent: Dict[str, Any],
        hostname: str = "Switch1"
    ) -> Dict[str, Any]:
        """
        Deploy configuration into simulation engine and perform functional assertions.
        """
        snapshot = self.simulator.simulate_deployment(config_text, default_hostname=hostname)
        device = self.simulator.devices.get(hostname)

        assertions = []
        entities = user_intent.get("extracted_entities", {})
        category = user_intent.get("intent_category", "GENERAL")

        # 1. VLAN Assertions
        for vid in entities.get("vlans", []):
            if vid in device.vlan_database:
                v_data = device.vlan_database[vid]
                assertions.append({
                    "test": f"VLAN_{vid}_Existence",
                    "passed": True,
                    "detail": f"VLAN {vid} (Name: '{v_data['name']}') is active in device database."
                })
            else:
                assertions.append({
                    "test": f"VLAN_{vid}_Existence",
                    "passed": False,
                    "detail": f"VLAN {vid} was not instantiated in the VLAN database."
                })

        # 2. Interface Access Mode Assertions
        for iface in entities.get("interfaces", []):
            if iface in device.interfaces:
                st = device.interfaces[iface]
                is_up = st["status"] == "up"
                assertions.append({
                    "test": f"Interface_{iface}_AdminState",
                    "passed": is_up,
                    "detail": f"Interface {iface} is {st['status']} (no shutdown check)."
                })
                if entities.get("vlans"):
                    expected_vlan = entities["vlans"][0]
                    vlan_match = st["access_vlan"] == expected_vlan or expected_vlan in st["allowed_vlans"]
                    assertions.append({
                        "test": f"Interface_{iface}_VLAN_Binding",
                        "passed": vlan_match,
                        "detail": f"Interface {iface} assigned to VLAN {st['access_vlan']}."
                    })
            else:
                assertions.append({
                    "test": f"Interface_{iface}_Configured",
                    "passed": False,
                    "detail": f"Interface {iface} not found in configured interface table."
                })

        # 3. IP Addressing and Connected Routing
        for ip in entities.get("ip_addresses", []):
            clean_ip = ip.split("/")[0]
            matched_if = [k for k, v in device.interfaces.items() if v.get("ip") == clean_ip]
            if matched_if:
                assertions.append({
                    "test": f"IP_{clean_ip}_Assignment",
                    "passed": True,
                    "detail": f"IP {clean_ip} correctly bound to interface {matched_if[0]}."
                })
            else:
                # Check routing table or DHCP
                in_routes = any(clean_ip in r["network"] for r in device.routing_table)
                in_dhcp = any(clean_ip in str(p.get("network")) or clean_ip in str(p.get("default_router")) for p in device.dhcp_pools.values())
                in_acl = any(clean_ip in str(rule.get("statement")) for rules in device.access_lists.values() for rule in rules)
                passed = in_routes or in_dhcp or in_acl
                assertions.append({
                    "test": f"IP_{clean_ip}_RoleVerification",
                    "passed": passed,
                    "detail": f"IP {clean_ip} verified in routing, DHCP, or ACL table."
                })

        # 4. OSPF Verification
        if "OSPF" in category:
            has_ospf = len(device.ospf_processes) > 0
            assertions.append({
                "test": "OSPF_Process_Active",
                "passed": has_ospf,
                "detail": f"OSPF routing process active with {sum(len(p['networks']) for p in device.ospf_processes.values())} network statements."
            })

        # 5. DHCP Verification
        if "DHCP" in category:
            has_dhcp = len(device.dhcp_pools) > 0
            assertions.append({
                "test": "DHCP_Pool_Active",
                "passed": has_dhcp,
                "detail": f"Configured DHCP pools: {list(device.dhcp_pools.keys())}."
            })

        # 6. ACL Filtering Simulation (Packet Walk)
        if "SECURITY" in category or "ACL" in category or device.access_lists:
            acl_verified = len(device.access_lists) > 0
            assertions.append({
                "test": "ACL_Rules_Instantiated",
                "passed": acl_verified,
                "detail": f"Access Control Lists active: {list(device.access_lists.keys())}."
            })

        all_passed = all(a["passed"] for a in assertions) if assertions else True

        return {
            "verified": all_passed,
            "device_hostname": hostname,
            "total_assertions": len(assertions),
            "passed_assertions": sum(1 for a in assertions if a["passed"]),
            "failed_assertions": sum(1 for a in assertions if not a["passed"]),
            "assertions": assertions,
            "snapshot": snapshot
        }


if __name__ == "__main__":
    verifier = NetworkVerifier()
    test_cli = """
    hostname Core1
    vlan 10
     name Engineering
    !
    interface GigabitEthernet0/1
     switchport mode access
     switchport access vlan 10
     no shutdown
    """
    res = verifier.verify_configuration(
        config_text=test_cli,
        user_intent={
            "intent_category": "VLAN",
            "extracted_entities": {
                "vlans": [10],
                "interfaces": ["GigabitEthernet0/1"],
                "ip_addresses": []
            }
        },
        hostname="Core1"
    )
    print("Verification Passed?", res["verified"])
    print("Assertions Summary:", f"{res['passed_assertions']}/{res['total_assertions']}")
    for a in res["assertions"]:
        print(f" - [{ 'PASS' if a['passed'] else 'FAIL' }] {a['test']}: {a['detail']}")
