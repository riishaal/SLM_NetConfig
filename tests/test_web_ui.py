"""
Unit & Integration Tests for Web UI and Server API
Tests the four core requirements through the web backend handler.
"""

import json
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controller.agent import NetworkConfigAgent


@pytest.fixture(scope="module")
def agent():
    return NetworkConfigAgent(load_model_weights=False)


def test_ui_requirement_1_vlan(agent):
    query = "Create VLAN 20 named Accounts."
    res = agent.process_request(query, device_name="Switch1")

    assert res.get("success", True) is True
    assert res["detected_category"] == "VLAN"
    assert res["verified"] is True
    assert "vlan 20" in res["final_config"]
    assert "name Accounts" in res["final_config"]
    assert res.get("saved_in_repo") is not None
    assert res.get("packet_tracer_export", {}).get("txt_path") is not None


def test_ui_requirement_2_interface_ip(agent):
    query = "Configure GigabitEthernet0/1 with IP address 192.168.20.1 and subnet mask 255.255.255.0."
    res = agent.process_request(query, device_name="Switch1")

    assert res.get("success", True) is True
    assert res["detected_category"] == "IP_ADDRESSING"
    assert res["verified"] is True
    assert "interface GigabitEthernet0/1" in res["final_config"]
    assert "ip address 192.168.20.1 255.255.255.0" in res["final_config"]


def test_ui_requirement_3_trunk(agent):
    query = "Configure GigabitEthernet0/1 as a trunk port and allow VLANs 10 and 20."
    res = agent.process_request(query, device_name="Switch1")

    assert res.get("success", True) is True
    assert res["detected_category"] == "VLAN_TRUNK"
    assert res["verified"] is True
    assert "switchport mode trunk" in res["final_config"]


def test_ui_requirement_4_ospf(agent):
    query = "Configure OSPF routing using network 192.168.1.0/24 in area 0."
    res = agent.process_request(query, device_name="Switch1")

    assert res.get("success", True) is True
    assert res["detected_category"] == "ROUTING_OSPF"
    assert res["verified"] is True
    assert "router ospf 1" in res["final_config"]
    assert "network 192.168.1.0 0.0.0.255 area 0" in res["final_config"]
