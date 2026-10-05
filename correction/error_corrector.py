"""
Error Correction and Suggestion Module
Analyzes validation errors, generates human-readable explanations and suggestions,
and applies safe deterministic corrections (e.g., CLI keyword typos, spacing fixes).
Adheres strictly to the requirement of not silently modifying unsafe configurations.
"""

import os
import re
import sys
from typing import Dict, Any, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from knowledge_base.kb_manager import KnowledgeBaseManager


class ErrorCorrector:
    """Provides structured correction suggestions and safe automated fixes."""

    def __init__(self, kb_manager: Optional[KnowledgeBaseManager] = None):
        self.kb = kb_manager or KnowledgeBaseManager()

    def process_errors(
        self,
        config_text: str,
        validation_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze errors from validator and produce actionable recommendations
        and safe corrected configurations.
        """
        raw_lines = config_text.splitlines()
        errors = validation_report.get("errors", [])
        warnings = validation_report.get("warnings", [])

        correction_items = []
        modified_lines = list(raw_lines)
        applied_fixes_count = 0

        for err in errors:
            item = self._diagnose_error(err, raw_lines)
            correction_items.append(item)

            # If safe and auto-correctable, apply to modified_lines
            if item["auto_correctable"] and item["line_number"] is not None:
                idx = item["line_number"] - 1
                if 0 <= idx < len(modified_lines):
                    modified_lines[idx] = item["corrected_line"]
                    applied_fixes_count += 1

        corrected_config = "\n".join(modified_lines)

        return {
            "has_corrections": len(correction_items) > 0,
            "applied_fixes_count": applied_fixes_count,
            "corrections": correction_items,
            "original_config": config_text,
            "corrected_config": corrected_config,
            "is_fully_resolved": applied_fixes_count == len(errors) and len(errors) > 0
        }

    def _diagnose_error(self, error_msg: str, lines: List[str]) -> Dict[str, Any]:
        """
        Diagnose a specific error message and formulate advice.
        """
        line_num = None
        m_line = re.search(r'Line\s+([0-9]+):', error_msg)
        if m_line:
            line_num = int(m_line.group(1))

        current_line = lines[line_num - 1].strip() if line_num and 0 < line_num <= len(lines) else ""

        # Case 1: Detected typo
        m_typo = re.search(r"Detected typo '([^']+)' in command\. Did you mean '([^']+)'\?", error_msg)
        if m_typo:
            typo_word = m_typo.group(1)
            correct_word = m_typo.group(2)
            corrected_line = re.sub(r'\b' + re.escape(typo_word) + r'\b', correct_word, current_line, flags=re.I)
            return {
                "line_number": line_num,
                "error_type": "SYNTAX_TYPO",
                "detected": current_line,
                "reason": f"Keyword '{typo_word}' is misspelled in Cisco IOS CLI dictionary.",
                "suggestion": f"Change '{typo_word}' to '{correct_word}' in line {line_num}.",
                "corrected_line": corrected_line,
                "auto_correctable": True
            }

        # Case 2: Reserved VLAN
        m_vlan = re.search(r'Reserved or invalid VLAN ID\s+([0-9]+)', error_msg)
        if m_vlan:
            vid = m_vlan.group(1)
            return {
                "line_number": line_num,
                "error_type": "RESERVED_VLAN",
                "detected": current_line,
                "reason": f"VLAN {vid} is reserved by Cisco IOS architecture (e.g. 1 default, 1002-1005 fddi/token ring).",
                "suggestion": f"Select an unreserved user VLAN ID in the standard range 2-1001.",
                "corrected_line": current_line,
                "auto_correctable": False
            }

        # Case 3: Context Mismatch (switchport outside interface)
        if "outside interface context" in error_msg:
            return {
                "line_number": line_num,
                "error_type": "CONTEXT_HIERARCHY",
                "detected": current_line,
                "reason": "The 'switchport' command must be applied inside an interface configuration block.",
                "suggestion": "Precede this command with 'interface <name>' before executing switchport directives.",
                "corrected_line": current_line,
                "auto_correctable": False
            }

        # Case 4: Missing Intent
        if error_msg.startswith("Intent Error:"):
            return {
                "line_number": None,
                "error_type": "INTENT_UNFULFILLED",
                "detected": "(Omitted in configuration)",
                "reason": error_msg,
                "suggestion": "Update prompt or re-invoke configuration generator with explicit entity requirements.",
                "corrected_line": "",
                "auto_correctable": False
            }

        # Generic fallback
        return {
            "line_number": line_num,
            "error_type": "GENERAL_ERROR",
            "detected": current_line,
            "reason": error_msg,
            "suggestion": "Review Cisco command syntax and parameter requirements.",
            "corrected_line": current_line,
            "auto_correctable": False
        }


if __name__ == "__main__":
    from validation.validator import ConfigValidator
    v = ConfigValidator()
    c = ErrorCorrector()

    bad_config = """
    vlan 10
     name HR
    !
    interface FastEthernet0/1
     switchport mode acces
     switchport access vlan 10
     no shutdown
    """
    report = v.validate_configuration(bad_config)
    correction_result = c.process_errors(bad_config, report)
    print("Corrections Found:", len(correction_result["corrections"]))
    for item in correction_result["corrections"]:
        print(f"Error: {item['detected']} -> Suggested: {item['suggestion']}")
    print("\nCorrected Configuration:\n", correction_result["corrected_config"])
