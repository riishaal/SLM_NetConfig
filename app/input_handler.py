"""
Input Handler Module
Receives, sanitizes, and normalizes natural-language network requirements
or question queries from users. Extracts entity candidates (VLANs, IPs, interfaces).
"""

import re
from typing import Dict, Any, List, Optional


class InputHandler:
    """Processes natural language user requests for network configuration."""

    def __init__(self):
        # Regular expressions for entity extraction
        self.vlan_pattern = re.compile(r'\bvlan\s*([0-9]{1,4})\b', re.IGNORECASE)
        self.ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?:/[0-9]{1,2})?\b')
        self.interface_pattern = re.compile(
            r'\b(?:fa(?:stethernet)?|gi(?:gabitethernet)?|eth(?:ernet)?|lo(?:opback)?|se(?:rial)?)\s*[0-9]+(?:/[0-9]+)*\b|\binterface\s+vlan\s*[0-9]+\b',
            re.IGNORECASE
        )
        self.named_vlan_pattern = re.compile(
            r'\bvlan\s*([0-9]{1,4})\s*(?:named|for|name)\s*([a-zA-Z0-9_\-]+)',
            re.IGNORECASE
        )

    def process_input(self, raw_text: str) -> Dict[str, Any]:
        """
        Clean, sanitize, and parse raw input text into structured metadata.
        """
        if not raw_text or not raw_text.strip():
            return {
                "valid": False,
                "error": "Input requirement cannot be empty.",
                "raw_text": "",
                "clean_text": "",
                "input_format": "unknown",
                "extracted_entities": {}
            }

        clean = raw_text.strip()
        # Remove multiple consecutive spaces
        clean = re.sub(r'\s+', ' ', clean)

        # Detect question vs declarative statement
        is_question = clean.endswith("?") or clean.lower().startswith(
            ("how", "what", "can you", "could you", "where")
        )
        input_format = "question" if is_question else "requirement"

        # Entity Extraction
        extracted_vlans = [int(v) for v in self.vlan_pattern.findall(clean)]
        all_ips = self.ip_pattern.findall(clean)
        extracted_masks = [ip for ip in all_ips if ip.startswith("255.")]
        extracted_ips = [ip for ip in all_ips if not ip.startswith("255.")]
        extracted_interfaces = self.interface_pattern.findall(clean)

        named_matches = self.named_vlan_pattern.findall(clean)
        vlan_names = {int(v[0]): v[1] for v in named_matches}

        # If VLAN name specified without explicit ID (e.g. 'VLAN for HR')
        if not vlan_names:
            unnum_match = re.search(r'\bvlan\s+(?:for|named|called)\s+([a-zA-Z0-9_\-]+)', clean, re.I)
            if unnum_match:
                name_found = unnum_match.group(1)
                default_vid = extracted_vlans[0] if extracted_vlans else 10
                vlan_names[default_vid] = name_found
                if not extracted_vlans:
                    extracted_vlans.append(default_vid)

        # Intent classification heuristics (pre-SLM classification)
        intent_category = self._detect_preliminary_intent(clean)

        return {
            "valid": True,
            "error": None,
            "raw_text": raw_text,
            "clean_text": clean,
            "input_format": input_format,
            "intent_category": intent_category,
            "extracted_entities": {
                "vlans": list(set(extracted_vlans)),
                "vlan_names": vlan_names,
                "ip_addresses": extracted_ips,
                "subnet_masks": extracted_masks,
                "interfaces": [self._normalize_interface(i) for i in extracted_interfaces]
            }
        }

    def _normalize_interface(self, iface_str: str) -> str:
        """Standardize interface names (e.g. fa0/1 -> FastEthernet0/1, gi0/1 -> GigabitEthernet0/1)."""
        s = iface_str.strip()
        m = re.match(r'^([a-zA-Z]+)\s*([0-9]+(?:/[0-9]+)*)$', s)
        if not m:
            return s
        prefix, num = m.group(1).lower(), m.group(2)
        if prefix.startswith("fa"):
            return f"FastEthernet{num}"
        elif prefix.startswith("gi"):
            return f"GigabitEthernet{num}"
        elif prefix.startswith("lo"):
            return f"Loopback{num}"
        elif prefix.startswith("vl"):
            return f"Vlan{num}"
        return f"{prefix.capitalize()}{num}"

    def _detect_preliminary_intent(self, text: str) -> str:
        """Fast preliminary categorization."""
        t = text.lower()
        if "ospf" in t:
            return "ROUTING_OSPF"
        if "dhcp" in t:
            return "DHCP"
        if "acl" in t or "access-list" in t or "deny" in t or "permit" in t or "filter" in t or "block" in t:
            return "SECURITY_ACL"
        if "trunk" in t:
            return "VLAN_TRUNK"
        if "vlan" in t and ("route" in t or "svi" in t or "gateway" in t):
            return "ROUTING"
        if "vlan" in t:
            return "VLAN"
        if "ip address" in t or "assign ip" in t:
            return "IP_ADDRESSING"
        if "route" in t or "gateway" in t:
            return "ROUTING_STATIC"
        return "GENERAL_CONFIGURATION"


if __name__ == "__main__":
    handler = InputHandler()
    res1 = handler.process_input("Create VLAN 10 named HR and VLAN 20 for Accounts and set fa0/1 to VLAN 10.")
    print("Result 1:", res1)
    res2 = handler.process_input("How do I configure OSPF process 1 on 192.168.1.0/24 area 0?")
    print("Result 2:", res2)
