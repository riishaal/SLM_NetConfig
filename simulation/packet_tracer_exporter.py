"""
Cisco Packet Tracer Exporter Module
Bridges generated and verified configurations with Cisco Packet Tracer.
Exports clean CLI batch files (.ios / .txt) with terminal instructions
and generates topology startup scripts ready for viva presentation.
"""

import os
from typing import Dict, Any, Optional


class PacketTracerExporter:
    """Exports configurations for Cisco Packet Tracer and GNS3 environments."""

    def __init__(self, export_dir: Optional[str] = None):
        if export_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            export_dir = os.path.join(base_dir, "output", "PacketTracer_Exports")
        self.export_dir = export_dir
        os.makedirs(self.export_dir, exist_ok=True)

    def export_script(
        self,
        hostname: str,
        config_cli: str,
        scenario_name: str = "custom_scenario"
    ) -> Dict[str, str]:
        """
        Generate export files formatted for Packet Tracer CLI paste / TFTP load.
        """
        clean_cli = "\n".join([line for line in config_cli.splitlines() if not line.strip().startswith("!")])
        
        # 1. Direct CLI copy-paste script
        paste_content = (
            f"! ==========================================================\n"
            f"! CISCO PACKET TRACER AUTOMATION SCRIPT\n"
            f"! Target Device: {hostname}\n"
            f"! Scenario: {scenario_name}\n"
            f"! Instructions: Open Packet Tracer -> Click Device -> CLI -> Paste\n"
            f"! ==========================================================\n"
            f"enable\n"
            f"configure terminal\n"
            f"{clean_cli}\n"
            f"end\n"
            f"write memory\n"
            f"show running-config\n"
        )
        
        safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in scenario_name)
        txt_filename = f"{hostname}_{safe_name}_pt_script.txt"
        ios_filename = f"{hostname}_{safe_name}_config.ios"

        txt_path = os.path.join(self.export_dir, txt_filename)
        ios_path = os.path.join(self.export_dir, ios_filename)

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(paste_content)

        with open(ios_path, "w", encoding="utf-8") as f:
            f.write(paste_content)

        return {
            "txt_path": txt_path,
            "ios_path": ios_path,
            "instructions": (
                f"1. Open Cisco Packet Tracer.\n"
                f"2. Add a Cisco 2960 Switch or 2911/4331 Router named '{hostname}'.\n"
                f"3. Click on the device, go to the 'CLI' tab.\n"
                f"4. Copy and paste the contents of: {txt_path}\n"
                f"5. The device will be configured and verified immediately."
            )
        }


if __name__ == "__main__":
    exporter = PacketTracerExporter()
    res = exporter.export_script(
        hostname="Switch1",
        config_cli="vlan 10\n name HR\ninterface Fa0/1\n switchport access vlan 10",
        scenario_name="VLAN10_HR"
    )
    print("Exported files successfully:")
    print(" TXT:", res["txt_path"])
    print(" Instructions:\n", res["instructions"])
