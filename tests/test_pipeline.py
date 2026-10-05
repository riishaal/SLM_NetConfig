"""
Automated Test Suite
Implements the 12 required test scenarios from the project specification:
Test 1:  Single VLAN
Test 2:  Multiple VLANs
Test 3:  Interface Assignment
Test 4:  IP Configuration
Test 5:  Routing (Static)
Test 6:  OSPF Routing
Test 7:  DHCP Server Pool
Test 8:  ACL / Security Traffic Filter
Test 9:  Invalid Configuration Detection (Typo)
Test 10: Missing Parameter Handling
Test 11: Unsupported Request Handling
Test 12: Conflicting Requirement Detection (Reserved VLAN)
"""

import os
import sys
import pytest

# Ensure root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controller.agent import NetworkConfigAgent
from validation.validator import ConfigValidator
from correction.error_corrector import ErrorCorrector


@pytest.fixture(scope="module")
def agent():
    return NetworkConfigAgent(load_model_weights=False)


@pytest.fixture(scope="module")
def validator():
    return ConfigValidator()


@pytest.fixture(scope="module")
def corrector():
    return ErrorCorrector()


def test_01_single_vlan(agent):
    """Test 1: Single VLAN creation."""
    query = "Create VLAN 10 named HR on Switch1."
    res = agent.process_request(query)
    assert res["detected_category"] == "VLAN"
    assert "vlan 10" in res["final_config"]
    assert "name HR" in res["final_config"]
    assert res["verified"] is True


def test_02_multiple_vlans(agent):
    """Test 2: Multiple VLANs in single request."""
    query = "Create VLAN 10 named HR and VLAN 20 named Accounts on Switch1."
    res = agent.process_request(query)
    assert "vlan 10" in res["final_config"]
    assert "vlan 20" in res["final_config"]
    assert res["verified"] is True


def test_03_interface_assignment(agent):
    """Test 3: Access port interface assignment to VLAN."""
    query = "Configure FastEthernet0/1 to access VLAN 10 and bring it up."
    res = agent.process_request(query)
    assert "interface FastEthernet0/1" in res["final_config"]
    assert "switchport mode access" in res["final_config"]
    assert "switchport access vlan 10" in res["final_config"]
    assert "no shutdown" in res["final_config"]
    assert res["verified"] is True


def test_04_ip_configuration(agent):
    """Test 4: Interface IP address and subnet mask assignment."""
    query = "Assign IP address 192.168.1.1 255.255.255.0 to interface GigabitEthernet0/1."
    res = agent.process_request(query)
    assert "interface GigabitEthernet0/1" in res["final_config"]
    assert "ip address 192.168.1.1 255.255.255.0" in res["final_config"]
    assert res["verified"] is True


def test_05_static_routing(agent):
    """Test 5: Static routing configuration."""
    query = "Configure a static route to network 10.1.0.0 255.255.0.0 via next-hop 192.168.1.254."
    res = agent.process_request(query)
    assert "ip route 10.1.0.0 255.255.0.0 192.168.1.254" in res["final_config"]
    assert res["verified"] is True


def test_06_ospf_routing(agent):
    """Test 6: OSPF dynamic routing process."""
    query = "Enable OSPF process 1 and advertise network 192.168.10.0 0.0.0.255 in area 0."
    res = agent.process_request(query)
    assert "router ospf 1" in res["final_config"]
    assert "network 192.168.10.0 0.0.0.255 area 0" in res["final_config"]
    assert res["verified"] is True


def test_07_dhcp_pool(agent):
    """Test 7: DHCP Server address pool."""
    query = "Configure DHCP pool SALES_POOL for network 192.168.20.0 255.255.255.0 with default-router 192.168.20.1."
    res = agent.process_request(query)
    assert "ip dhcp pool SALES_POOL" in res["final_config"]
    assert "network 192.168.20.0 255.255.255.0" in res["final_config"]
    assert "default-router 192.168.20.1" in res["final_config"]
    assert res["verified"] is True


def test_08_acl_security(agent):
    """Test 8: Access Control List port 80 traffic filter."""
    query = "Create an access list to deny HTTP traffic on port 80 from 192.168.10.0/24 and apply in on Gi0/1."
    res = agent.process_request(query)
    assert "access-list 101 deny tcp" in res["final_config"]
    assert "eq 80" in res["final_config"]
    assert "ip access-group 101 in" in res["final_config"]
    assert res["verified"] is True


def test_09_invalid_configuration_detection(validator, corrector):
    """Test 9: Invalid command with typo ('switchport mode acces')."""
    bad_cfg = "interface FastEthernet0/1\n switchport mode acces\n switchport access vlan 10"
    val_report = validator.validate_configuration(bad_cfg)
    assert val_report["status"] in ["FAILED", "PARTIALLY_CORRECT"]
    assert any("acces" in err for err in val_report["errors"])

    # Verify auto-correction suggestion
    corr_report = corrector.process_errors(bad_cfg, val_report)
    assert corr_report["has_corrections"] is True
    assert corr_report["corrections"][0]["suggestion"] == "Change 'acces' to 'access' in line 2."
    assert "switchport mode access" in corr_report["corrected_config"]


def test_10_missing_parameter(agent):
    """Test 10: Missing parameter handling (e.g. VLAN without ID falls back gracefully)."""
    query = "Create VLAN for HR department."
    res = agent.process_request(query)
    assert res["detected_category"] == "VLAN"
    assert "vlan" in res["final_config"]
    assert "HR" in res["final_config"]


def test_11_unsupported_request(agent):
    """Test 11: Unsupported request handling."""
    query = "Configure quantum encryption satellite uplink protocol on Switch1."
    res = agent.process_request(query)
    # Pipeline gracefully confines output to valid Cisco IOS constructs without crashing
    assert res is not None
    assert "Switch1" in res["final_config"]


def test_12_conflicting_requirement_reserved_vlan(validator):
    """Test 12: Conflicting requirement (attempting to create reserved VLAN 1002)."""
    bad_cfg = "vlan 1002\n name CustomVLAN"
    val_report = validator.validate_configuration(bad_cfg)
    assert val_report["status"] in ["FAILED", "PARTIALLY_CORRECT"]
    assert any("Reserved or invalid VLAN ID 1002" in err for err in val_report["errors"])


if __name__ == "__main__":
    pytest.main(["-v", __file__])
