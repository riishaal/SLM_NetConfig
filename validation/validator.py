"""
Configuration Validation Module
Implements 3-tier validation matching IEEE OJCOMS 2026 specifications:
1. Syntax Validation: Batfish-style command grammar parsing (PASSED, PARTIALLY_UNRECOGNIZED, FAILED).
2. Semantic Validation: Domain logic consistency (VLAN ID bounds, subnet mask validity, mode context).
3. Intent Validation: Verifies that generated commands fulfill all extracted user intent goals.
"""

import ipaddress
import os
import re
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List, Optional, Tuple
from knowledge_base.kb_manager import KnowledgeBaseManager


class ConfigValidator:
    """Multi-tier configuration validation engine."""

    def __init__(self, kb_manager: Optional[KnowledgeBaseManager] = None):
        self.kb = kb_manager or KnowledgeBaseManager()

        # Known Cisco IOS valid command patterns
        self.grammar_patterns = [
            (re.compile(r'^!\s*'), "comment"),
            (re.compile(r'^configure\s+terminal\s*$', re.I), "exec_config"),
            (re.compile(r'^end\s*$', re.I), "exec_end"),
            (re.compile(r'^exit\s*$', re.I), "exec_exit"),
            (re.compile(r'^hostname\s+[a-zA-Z0-9_\-]+\s*$', re.I), "hostname"),
            (re.compile(r'^ip\s+routing\s*$', re.I), "ip_routing"),
            (re.compile(r'^vlan\s+([0-9]+)\s*$', re.I), "vlan_declare"),
            (re.compile(r'^name\s+[a-zA-Z0-9_\-]+\s*$', re.I), "vlan_name"),
            (re.compile(r'^interface\s+([a-zA-Z0-9_/\-]+)\s*$', re.I), "interface_enter"),
            (re.compile(r'^ip\s+address\s+([0-9\.]+)\s+([0-9\.]+)\s*$', re.I), "ip_address"),
            (re.compile(r'^no\s+shutdown\s*$', re.I), "no_shutdown"),
            (re.compile(r'^shutdown\s*$', re.I), "shutdown"),
            (re.compile(r'^switchport\s+mode\s+(access|trunk|dynamic\s+desirable|dynamic\s+auto)\s*$', re.I), "switchport_mode"),
            (re.compile(r'^switchport\s+access\s+vlan\s+([0-9]+)\s*$', re.I), "switchport_access_vlan"),
            (re.compile(r'^switchport\s+trunk\s+encapsulation\s+(dot1q|isl)\s*$', re.I), "trunk_encap"),
            (re.compile(r'^switchport\s+trunk\s+allowed\s+vlan\s+([0-9,\-]+|all|none|add\s+[0-9,\-]+)\s*$', re.I), "trunk_allowed_vlan"),
            (re.compile(r'^ip\s+route\s+([0-9\.]+)\s+([0-9\.]+)\s+([a-zA-Z0-9_/\.\-]+)\s*$', re.I), "static_route"),
            (re.compile(r'^router\s+ospf\s+([0-9]+)\s*$', re.I), "router_ospf"),
            (re.compile(r'^network\s+([0-9\.]+)\s+([0-9\.]+)\s+area\s+([0-9]+)\s*$', re.I), "ospf_network"),
            (re.compile(r'^passive-interface\s+([a-zA-Z0-9_/\-]+)\s*$', re.I), "passive_interface"),
            (re.compile(r'^ip\s+dhcp\s+pool\s+([a-zA-Z0-9_\-]+)\s*$', re.I), "dhcp_pool"),
            (re.compile(r'^network\s+([0-9\.]+)\s+([0-9\.]+)\s*$', re.I), "dhcp_network"),
            (re.compile(r'^default-router\s+([0-9\.]+)\s*$', re.I), "default_router"),
            (re.compile(r'^dns-server\s+([0-9\.\s]+)\s*$', re.I), "dns_server"),
            (re.compile(r'^ip\s+dhcp\s+excluded-address\s+([0-9\.]+)(?:\s+([0-9\.]+))?\s*$', re.I), "dhcp_excluded"),
            (re.compile(r'^access-list\s+([0-9]+)\s+(permit|deny)\s+([a-zA-Z0-9\.\s_]+)\s*$', re.I), "access_list"),
            (re.compile(r'^ip\s+access-group\s+([0-9]+)\s+(in|out)\s*$', re.I), "ip_access_group"),
            (re.compile(r'^write(\s+memory)?\s*$', re.I), "exec_write"),
            (re.compile(r'^copy\s+running-config\s+startup-config\s*$', re.I), "exec_copy")
        ]

    def validate_configuration(
        self,
        config_text: str,
        user_intent: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute full 3-tier validation on configuration text.
        """
        lines = [line.strip() for line in config_text.splitlines() if line.strip()]

        # Tier 1: Syntax Validation
        syntax_res = self._validate_syntax(lines)

        # Tier 2: Semantic Validation
        semantic_res = self._validate_semantics(lines)

        # Tier 3: Intent Validation
        intent_res = self._validate_intent(lines, user_intent) if user_intent else {"valid": True, "score": 1.0, "details": []}

        # Overall Status
        all_errors = syntax_res["errors"] + semantic_res["errors"] + intent_res.get("errors", [])
        all_warnings = syntax_res["warnings"] + semantic_res["warnings"]

        if syntax_res["parse_status"] == "FAILED" or len(syntax_res["errors"]) > 0:
            final_status = "FAILED"
        elif syntax_res["parse_status"] == "PARTIALLY_UNRECOGNIZED" or len(all_errors) > 0:
            final_status = "PARTIALLY_CORRECT"
        else:
            final_status = "PASSED"

        # Calculate Goal Accuracy (Eq 4 from paper): 1 (full), 0 (partial), -1 (failed)
        if intent_res.get("valid", True) and final_status == "PASSED":
            goal_score = 1
        elif final_status == "PARTIALLY_CORRECT" or (intent_res.get("score", 0) > 0):
            goal_score = 0
        else:
            goal_score = -1

        # Calculate Syntax Accuracy (Eq 2 & 3 from paper): 1, 0, -1
        if syntax_res["parse_status"] == "PASSED" and not syntax_res["errors"]:
            syntax_score = 1
        elif syntax_res["parse_status"] == "PARTIALLY_UNRECOGNIZED":
            syntax_score = 0
        else:
            syntax_score = -1

        return {
            "status": final_status,
            "syntax_status": syntax_res["parse_status"],
            "syntax_score": syntax_score,
            "goal_score": goal_score,
            "line_count": len(lines),
            "errors": all_errors,
            "warnings": all_warnings,
            "syntax_details": syntax_res,
            "semantic_details": semantic_res,
            "intent_details": intent_res
        }

    def _validate_syntax(self, lines: List[str]) -> Dict[str, Any]:
        """
        Verify Cisco IOS grammar for each command line.
        """
        passed_lines = 0
        unrecognized_lines = []
        errors = []
        warnings = []

        for line_num, line in enumerate(lines, 1):
            if line.startswith("!") or line.startswith("#"):
                passed_lines += 1
                continue

            matched = False
            for pattern, pattern_type in self.grammar_patterns:
                if pattern.match(line):
                    matched = True
                    break

            if matched:
                passed_lines += 1
            else:
                # Check if it has a typo
                is_valid, typo_msg = self.kb.validate_command_line(line)
                if not is_valid:
                    errors.append(f"Line {line_num}: {typo_msg}")
                    unrecognized_lines.append((line_num, line, typo_msg))
                else:
                    warnings.append(f"Line {line_num}: Unrecognized syntax: '{line}'")
                    unrecognized_lines.append((line_num, line, "Unrecognized command structure"))

        if len(errors) > 0 and len(unrecognized_lines) > len(lines) / 2:
            parse_status = "FAILED"
        elif len(unrecognized_lines) > 0 or len(errors) > 0:
            parse_status = "PARTIALLY_UNRECOGNIZED"
        else:
            parse_status = "PASSED"

        return {
            "parse_status": parse_status,
            "passed_lines": passed_lines,
            "total_lines": len(lines),
            "errors": errors,
            "warnings": warnings,
            "unrecognized": unrecognized_lines
        }

    def _validate_semantics(self, lines: List[str]) -> Dict[str, Any]:
        """
        Verify logical coherence: IP validity, subnet masks, VLAN IDs, and context blocks.
        """
        errors = []
        warnings = []
        current_mode = "GLOBAL"
        configured_vlans = set()
        configured_svis = set()

        for line_num, line in enumerate(lines, 1):
            # Track block mode context
            if re.match(r'^interface\s+([a-zA-Z0-9_/\-]+)', line, re.I):
                current_mode = "INTERFACE"
                if_match = re.match(r'^interface\s+vlan\s*([0-9]+)', line, re.I)
                if if_match:
                    configured_svis.add(int(if_match.group(1)))
            elif re.match(r'^vlan\s+([0-9]+)', line, re.I):
                current_mode = "VLAN"
                vid_val = int(re.match(r'^vlan\s+([0-9]+)', line, re.I).group(1))
                is_res, res_msg = self.kb.is_reserved_vlan(vid_val)
                if is_res:
                    errors.append(f"Line {line_num}: Reserved or invalid VLAN ID {vid_val}. {res_msg}")
                else:
                    configured_vlans.add(vid_val)
            elif line.lower() in ["exit", "end"]:
                current_mode = "GLOBAL"

            # Check context appropriateness
            if line.lower().startswith("switchport") and current_mode != "INTERFACE":
                errors.append(f"Line {line_num}: 'switchport' command used outside interface context (current mode: {current_mode})")

            # Check IP and subnet mask validity
            ip_match = re.match(r'^ip\s+address\s+([0-9\.]+)\s+([0-9\.]+)', line, re.I)
            if ip_match:
                ip_str, mask_str = ip_match.group(1), ip_match.group(2)
                try:
                    ip_obj = ipaddress.IPv4Address(ip_str)
                    if ip_obj.is_loopback:
                        errors.append(f"Line {line_num}: Interface IP {ip_str} cannot be in loopback range 127.0.0.0/8")
                    if ip_obj.is_multicast:
                        errors.append(f"Line {line_num}: Interface IP {ip_str} cannot be a multicast address")
                except ValueError:
                    errors.append(f"Line {line_num}: Invalid IPv4 address format '{ip_str}'")

                try:
                    ipaddress.IPv4Network(f"0.0.0.0/{mask_str}")
                except ValueError:
                    errors.append(f"Line {line_num}: Invalid IPv4 subnet mask '{mask_str}'")

            # Check OSPF wildcard mask validity
            ospf_net_match = re.match(r'^network\s+([0-9\.]+)\s+([0-9\.]+)\s+area\s+([0-9]+)', line, re.I)
            if ospf_net_match:
                wc = ospf_net_match.group(2)
                # Wildcards usually have inverted bits, check that octets are valid
                octets = wc.split(".")
                if len(octets) != 4 or any(not oct.isdigit() or int(oct) not in [0, 1, 3, 7, 15, 31, 63, 127, 255] for oct in octets):
                    warnings.append(f"Line {line_num}: Unusual OSPF wildcard mask '{wc}'. Verify inverse mask format.")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "configured_vlans": list(configured_vlans),
            "configured_svis": list(configured_svis)
        }

    def _validate_intent(self, lines: List[str], user_intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify that user's requested entities are fulfilled in the configuration.
        """
        errors = []
        fulfilled_goals = []
        config_blob = "\n".join(lines).lower()

        entities = user_intent.get("extracted_entities", {})

        # Check requested VLANs
        for vid in entities.get("vlans", []):
            if f"vlan {vid}" in config_blob or f"access vlan {vid}" in config_blob:
                fulfilled_goals.append(f"VLAN {vid} presence verified")
            else:
                errors.append(f"Intent Error: Requested VLAN {vid} not found in generated configuration.")

        # Check requested IP addresses
        for ip in entities.get("ip_addresses", []):
            clean_ip = ip.split("/")[0]
            if clean_ip in config_blob:
                fulfilled_goals.append(f"IP {clean_ip} configuration verified")
            else:
                errors.append(f"Intent Error: Requested IP {clean_ip} not found in generated configuration.")

        # Check requested interfaces
        for iface in entities.get("interfaces", []):
            if iface.lower() in config_blob:
                fulfilled_goals.append(f"Interface {iface} presence verified")
            else:
                errors.append(f"Intent Error: Requested interface {iface} not configured.")

        total_checks = len(entities.get("vlans", [])) + len(entities.get("ip_addresses", [])) + len(entities.get("interfaces", []))
        score = len(fulfilled_goals) / total_checks if total_checks > 0 else 1.0

        return {
            "valid": len(errors) == 0,
            "score": score,
            "errors": errors,
            "fulfilled_goals": fulfilled_goals
        }


if __name__ == "__main__":
    validator = ConfigValidator()
    sample_cfg = """
    vlan 10
     name HR
    !
    interface FastEthernet0/1
     switchport mode acces
     switchport access vlan 10
     no shutdown
    """
    res = validator.validate_configuration(sample_cfg, {
        "extracted_entities": {"vlans": [10], "interfaces": ["FastEthernet0/1"], "ip_addresses": []}
    })
    print("Validation Result Status:", res["status"])
    print("Syntax Errors:", res["errors"])
