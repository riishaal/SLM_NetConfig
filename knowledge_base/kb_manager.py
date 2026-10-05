"""
Knowledge Base Manager Module
Coordinates network command dictionaries, syntax validation rules,
CIDR/wildcard conversions, and prompt grounding templates.
"""

import json
import os
import re
from typing import Dict, Any, List, Optional, Tuple


class KnowledgeBaseManager:
    """Central manager for network domain knowledge."""

    def __init__(self, kb_dir: Optional[str] = None):
        if kb_dir is None:
            kb_dir = os.path.dirname(os.path.abspath(__file__))
        self.kb_dir = kb_dir

        self.commands_file = os.path.join(kb_dir, "cisco_ios_commands.json")
        self.rules_file = os.path.join(kb_dir, "networking_rules.json")
        self.patterns_file = os.path.join(kb_dir, "config_patterns.json")

        self.commands_data: Dict[str, Any] = self._load_json(self.commands_file)
        self.rules_data: Dict[str, Any] = self._load_json(self.rules_file)
        self.patterns_data: Dict[str, Any] = self._load_json(self.patterns_file)

    def _load_json(self, filepath: str) -> Dict[str, Any]:
        """Safely load JSON file from disk."""
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def get_supported_categories(self) -> List[str]:
        """Return list of supported configuration categories."""
        categories = set()
        for cmd in self.commands_data.get("commands", []):
            cat = cmd.get("category")
            if cat:
                categories.add(cat)
        return sorted(list(categories))

    def get_pattern(self, pattern_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve configuration pattern template."""
        return self.patterns_data.get("patterns", {}).get(pattern_name)

    def is_reserved_vlan(self, vlan_id: int) -> Tuple[bool, str]:
        """Check if VLAN ID is reserved."""
        reserved = self.rules_data.get("vlan_rules", {}).get("reserved_vlans", {})
        vid_str = str(vlan_id)
        if vid_str in reserved:
            return True, reserved[vid_str]
        vlan_min = self.rules_data.get("vlan_rules", {}).get("min_id", 1)
        vlan_max = self.rules_data.get("vlan_rules", {}).get("max_id", 4094)
        if not (vlan_min <= vlan_id <= vlan_max):
            return True, f"VLAN ID {vlan_id} out of valid range ({vlan_min}-{vlan_max})"
        return False, ""

    def cidr_to_mask(self, cidr_bits: int) -> Optional[Dict[str, str]]:
        """Convert CIDR prefix length (e.g. 24) to subnet mask and wildcard."""
        return self.rules_data.get("cidr_to_masks", {}).get(str(cidr_bits))

    def mask_to_wildcard(self, mask: str) -> Optional[str]:
        """Convert a dotted-decimal subnet mask to a wildcard mask."""
        octets = mask.strip().split(".")
        if len(octets) != 4:
            return None
        try:
            wildcard_octets = [str(255 - int(oct)) for oct in octets]
            return ".".join(wildcard_octets)
        except ValueError:
            return None

    def get_typo_correction(self, token: str) -> Optional[str]:
        """Check if token is a known CLI typo and return corrected keyword."""
        return self.rules_data.get("typo_dictionary", {}).get(token.lower().strip())

    def get_prompt_context(self, intent_type: str) -> str:
        """
        Generate contextual knowledge grounding snippet for the SLM prompt
        based on the detected intent type.
        """
        intent = intent_type.lower()
        context_parts = []

        if "vlan" in intent:
            context_parts.append(
                "Knowledge Context [VLAN]: Valid IDs are 2-1001 (1 is default, 1002-1005 reserved). "
                "Cisco IOS standard commands: 'vlan <id>', 'name <name>', 'switchport mode access', "
                "'switchport access vlan <id>'."
            )
        if "trunk" in intent:
            context_parts.append(
                "Knowledge Context [TRUNK]: Requires 'switchport trunk encapsulation dot1q' "
                "followed by 'switchport mode trunk', 'switchport trunk allowed vlan <list>'."
            )
        if "ospf" in intent or "routing" in intent:
            context_parts.append(
                "Knowledge Context [ROUTING]: For OSPF, use 'router ospf <pid>' and "
                "'network <ip> <wildcard_mask> area <area_id>'. Note: OSPF uses inverse wildcard masks (e.g., 0.0.0.255 for /24)."
            )
        if "dhcp" in intent:
            context_parts.append(
                "Knowledge Context [DHCP]: Use 'ip dhcp pool <name>', 'network <net> <mask>', "
                "'default-router <ip>', and 'dns-server <ip>'. Use 'ip dhcp excluded-address' in global mode."
            )
        if "acl" in intent or "security" in intent:
            context_parts.append(
                "Knowledge Context [ACL]: Standard ACL: 1-99; Extended ACL: 100-199. "
                "Format: 'access-list <id> {permit|deny} {ip|tcp|udp} <src> <src_wildcard> <dst> <dst_wildcard> eq <port>'."
            )

        if not context_parts:
            context_parts.append(
                "Knowledge Context: Generate strictly valid Cisco IOS commands. Use appropriate mode hierarchy."
            )

        return "\n".join(context_parts)

    def validate_command_line(self, line: str) -> Tuple[bool, Optional[str]]:
        """
        Basic deterministic check against known Cisco commands.
        Returns (is_valid, error_reason).
        """
        stripped = line.strip()
        if not stripped or stripped.startswith("!") or stripped.startswith("#"):
            return True, None

        tokens = stripped.split()
        first_token = tokens[0].lower()

        # Check all tokens for known typos
        for token in tokens:
            clean_token = token.lower().strip(",;")
            typo_fix = self.get_typo_correction(clean_token)
            if typo_fix:
                return False, f"Detected typo '{token}' in command. Did you mean '{typo_fix}'?"

        # Valid global/interface command starters
        valid_starters = {
            "vlan", "name", "interface", "ip", "switchport", "router",
            "network", "passive-interface", "access-list", "default-router",
            "dns-server", "domain-name", "no", "shutdown", "exit", "end",
            "hostname", "line", "enable", "configure", "write", "copy"
        }

        if first_token not in valid_starters:
            return False, f"Unrecognized or unsupported Cisco command token: '{first_token}'"

        return True, None


if __name__ == "__main__":
    # Self-test KB Manager
    kb = KnowledgeBaseManager()
    print("KB Categories:", kb.get_supported_categories())
    print("VLAN 10 reserved?", kb.is_reserved_vlan(10))
    print("VLAN 1002 reserved?", kb.is_reserved_vlan(1002))
    print("CIDR /24:", kb.cidr_to_mask(24))
    print("Typo 'acces' ->", kb.get_typo_correction("acces"))
    print("Command line 'switchport mode acces':", kb.validate_command_line("switchport mode acces"))
