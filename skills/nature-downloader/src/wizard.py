"""Configuration wizard module.

Seven-step interactive configuration flow for agent use.
Each step returns a prompt and validates the user's response.

Usage from an agent:
    from wizard import Wizard
    w = Wizard()
    # Step 1
    prompt = w.start()                # Prompt to present to the user
    # After the user responds
    result = w.handle_step1(user_input)
    # result = {"next": "step2"|"retry"|"done", "prompt": str, "data": dict}

The distribution contains no institution presets; users supply institution names and entry points at runtime.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from config import save_config, backup_config, delete_config, CONFIG_FILE
from schools_loader import match_school, list_school_names
from validators import (
    KNOWN_DATABASES,
    validate_carsi_entry,
    validate_ezproxy_url,
    validate_libraries,
    validate_school_name,
    validate_sso_domain,
)


def infer_access_from_url(url: str) -> dict[str, Any]:
    """Infer the likely library access route from a user-provided resource URL."""
    raw_url = url.strip()
    parsed = urlparse(raw_url if "://" in raw_url else f"https://{raw_url}")
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    query = parse_qs(parsed.query)
    service = query.get("service", [""])[0]
    service_host = urlparse(service).netloc.lower() if service else ""

    result: dict[str, Any] = {
        "resource_entry": raw_url,
        "entry_host": host,
        "entry_type": "resource_entry",
        "auth_type": "custom",
        "sso_domain": host,
        "service_host": service_host or None,
        "institution_hint": None,
        "notes": "",
    }

    if "metaersp" in host or "metaauth" in host:
        result.update(
            {
                "entry_type": "resource_portal",
                "auth_type": "cas",
                "sso_domain": host,
                "institution_hint": host.split(".", 1)[0] if "." in host else None,
                "notes": "Aggregated resource portal; enter here first and follow SSO redirects when required.",
            }
        )
    elif "/authserver/login" in path or host.startswith("cas."):
        hint = None
        if service_host:
            service_parts = urlparse(service).path.strip("/").split("/")
            if len(service_parts) >= 2:
                hint = service_parts[1]
        result.update(
            {
                "entry_type": "cas_login",
                "auth_type": "cas",
                "sso_domain": host,
                "institution_hint": hint,
                "notes": "CAS login entry; if service points to a resource portal, return to that portal to enter the database.",
            }
        )
    elif "ezproxy" in host or "libproxy" in host:
        result.update({"entry_type": "ezproxy", "auth_type": "custom", "notes": "Library remote-access proxy entry."})
    elif "webvpn" in host or "vpn" in host:
        result.update({"entry_type": "webvpn", "auth_type": "custom", "notes": "WebVPN entry."})
    elif "shibboleth" in path or "carsi" in host:
        result.update({"entry_type": "carsi", "auth_type": "sso", "notes": "CARSI/Shibboleth institutional authentication entry."})

    return result


class Wizard:
    """Configuration wizard state machine.

    State transitions:
        step1 (Institution name) ->
            Preset found -> step4 (Confirm databases) -> step6 (self-check) -> step7 (save)
            No match -> step2 (CARSI check) -> step3 (SSO domain) -> step4 -> step6 -> step7
                                                   or step5 (EZproxy) -> step6 -> step7
    """

    def __init__(self) -> None:
        self.state: str = "step1"
        self.data: dict[str, Any] = {}
        self.matched_preset: Optional[dict[str, Any]] = None

    # ===== Step 1: Ask for the institution name =====
    def start(self) -> str:
        """Return the initial prompt."""
        self.state = "step1"
        return (
            "Hello! Before downloading literature, configure your library resource entry once.\n\n"
            "Provide the link you normally use for library electronic resources or databases.\n"
            "This can be a resource portal, database list, Web of Science entry, database details page, "
            "or a login link redirecting to single sign-on.\n\n"
            "The link will identify the CAS, CARSI, EZproxy, WebVPN, or portal authorization route; "
            "the distribution contains no built-in institution names or authentication URLs."
        )

    def handle_step1(self, user_input: str) -> dict[str, Any]:
        """Handle a resource entry URL; fall back to legacy institution-name presets for non-URL input."""
        value = user_input.strip()
        if not value:
            return {"next": "retry", "prompt": "Input must not be empty; paste a library resource or database entry URL: "}

        if "://" in value or "." in value:
            inferred = infer_access_from_url(value)
            self.data.update(inferred)
            self.data["school_name"] = inferred.get("institution_hint") or inferred["entry_host"]
            self.data["source"] = "resource_url"
            self.data["auth_type"] = inferred["auth_type"]
            self.data["sso_domain"] = inferred["sso_domain"]
            self.data["carsi_entry"] = inferred["resource_entry"]
            self.data["libraries"] = ["Web of Science", "ScienceDirect", "Springer", "IEEE Xplore", "知网", "ACS"]
            self.data["notes"] = inferred.get("notes", "")
            self.data["discovery"] = {"resource_entry_url": inferred["resource_entry"]}
            if inferred["entry_type"] == "resource_portal":
                self.data["discovery"]["resource_portal_url"] = inferred["resource_entry"]
            if inferred.get("service_host"):
                self.data["discovery"]["auth_service_host"] = inferred["service_host"]

            self.state = "step4"
            return {
                "next": "step4",
                "prompt": (
                    "Identified authorization route from the resource URL:\n"
                    f"  Entry type: {inferred['entry_type']}\n"
                    f"  Authentication type: {inferred['auth_type']}\n"
                    f"  SSO domain: {inferred['sso_domain']}\n"
                    f"  Resource entry: {inferred['resource_entry']}\n\n"
                    "Use this configuration initially?\n"
                    "  1. Confirm and continue to the self-check\n"
                    "  2. Adjust the database list\n"
                    "  3. Use manual configuration"
                ),
                "data": {"inferred": inferred},
            }

        name = value

        ok, msg = validate_school_name(name)
        if not ok:
            return {"next": "retry", "prompt": f"{msg}; enter the resource URL or institution name again: "}

        # Look up institution presets
        preset = match_school(name)
        if preset:
            self.matched_preset = preset
            self.data["school_name"] = preset["name"]
            self.data["source"] = "preset"

            # Prefill configuration from the preset
            auth = preset.get("auth", {})
            self.data["auth_type"] = auth.get("type", "cas")
            self.data["sso_domain"] = auth.get("sso_domain", "")
            self.data["carsi_entry"] = auth.get("carsi_entry", "")
            self.data["libraries"] = preset.get("libraries", [])
            self.data["notes"] = preset.get("notes", "")

            self.state = "step4"
            return {
                "next": "step4",
                "prompt": (
                    f"Matched institution preset: {preset['name']}\n"
                    f"  Authentication type: {auth.get('type', 'unknown')}\n"
                    f"  SSO domain: {auth.get('sso_domain', 'unknown')}\n"
                    f"  CARSI entry: {auth.get('carsi_entry', 'not configured')}\n"
                    f"  Preset databases: {', '.join(preset.get('libraries', []))}\n\n"
                    "Use the configuration above?\n"
                    "  1. Confirm and finish configuration\n"
                    "  2. Adjust the database list\n"
                    "  3. This is not my institution; enter it again"
                ),
                "data": {"matched": preset["name"]},
            }

        # No matchpreset; proceed to manual input
        self.data["school_name"] = name
        self.data["source"] = "manual"
        self.state = "step2"
        return {
            "next": "step2",
            "prompt": (
                f"No preset matched for '{name}'; starting the manual configuration wizard.\n\n"
                "Step 2: Does your institution use CARSI federated authentication?\n"
                "(CARSI is a university identity federation: https://www.carsi.edu.cn/)\n\n"
                "  1. Yes, CARSI is available\n"
                "  2. No or unsure; use library remote access (EZproxy)\n"
                "  3. Neither; connect to the campus network through a VPN"
            ),
        }

    # ===== Step 2: CARSI self-check =====
    def handle_step2(self, user_input: str) -> dict[str, Any]:
        """Handle CARSI selection."""
        choice = user_input.strip()
        if choice == "1":
            self.data["use_carsi"] = True
            self.state = "step2b"
            return {
                "next": "step2b",
                "prompt": (
                    "Paste your institution's CARSI entry URL.\n"
                    "(Find it in the member institution list at https://www.carsi.edu.cn/, "
                    "e.g. https://login.university.example/idp/shibboleth; use your actual institution entry.)\n\n"
                    "If unavailable, enter 'skip' and add it manually later."
                ),
            }
        elif choice == "2":
            self.data["use_carsi"] = False
            self.state = "step3"
            return {
                "next": "step3",
                "prompt": (
                    "You selected library remote access (EZproxy).\n\n"
                    "Step 3: Enter your institution's single sign-on domain.\n"
                    "(e.g. login.university.example; use the domain on your institution's actual page.)"
                ),
            }
        elif choice == "3":
            self.data["use_carsi"] = False
            self.data["use_vpn"] = True
            self.state = "step3"
            return {
                "next": "step3",
                "prompt": (
                    "Using the VPN route.\n"
                    "Connect to your campus VPN, then enter the institutional SSO domain.\n"
                    "(e.g. login.university.example; use your actual institutional domain.)"
                ),
            }
        return {"next": "retry", "prompt": "Enter 1, 2, or 3: "}

    # ===== Step 2b: CARSI entry URL =====
    def handle_step2b(self, user_input: str) -> dict[str, Any]:
        """Handle the CARSI entry URL."""
        url = user_input.strip()
        if url in ("跳过", "skip", ""):
            self.data["carsi_entry"] = ""
            self.state = "step3"
            return {
                "next": "step3",
                "prompt": (
                    "Skipped the CARSI entry; it can be added later.\n\n"
                    "Step 3: Enter your institution's single sign-on domain.\n"
                    "(e.g. login.university.example; use your actual institutional domain.)"
                ),
            }

        # Validate
        ok, msg = validate_carsi_entry(url)
        if not ok:
            return {
                "next": "retry",
                "prompt": f"{msg}\n\nEnter the CARSI entry URL again, or 'skip' to leave it blank: ",
            }

        self.data["carsi_entry"] = url
        self.state = "step3"
        return {
            "next": "step3",
            "prompt": (
                f"CARSI entry validation passed.\n\n"
                "Step 3: Enter your institution's single sign-on domain.\n"
                "(e.g. login.university.example; use your actual institutional domain.)"
            ),
        }

    # ===== Step 3: SSO domain =====
    def handle_step3(self, user_input: str) -> dict[str, Any]:
        """Handle the SSO domain input."""
        domain = user_input.strip()
        if not domain:
            return {"next": "retry", "prompt": "Domain must not be empty; enter it again: "}

        ok, msg = validate_sso_domain(domain)
        if not ok:
            return {
                "next": "retry",
                "prompt": f"{msg}\n\nEnter your institution's SSO domain again (e.g. login.university.example): ",
            }

        self.data["sso_domain"] = domain.split("://")[-1].split("/")[0]
        # Default auth_type to cas if not yet set
        if "auth_type" not in self.data:
            self.data["auth_type"] = "cas"

        # If using the EZproxy route
        if not self.data.get("use_carsi", True) and not self.data.get("use_vpn"):
            self.state = "step5"
            return {
                "next": "step5",
                "prompt": (
                    f"SSO domain validation passed: {msg}\n\n"
                    "Step 5: Enter your library's EZproxy login URL.\n"
                    "(Note: EZproxy often requires enabling remote-access permission on the library website first.)\n\n"
                    "If unsure, enter 'skip' and add it later."
                ),
            }

        self.state = "step4"
        return {
            "next": "step4",
            "prompt": (
                f"SSO domain validation passed: {msg}\n\n"
                "Step 4: Which databases do you normally download from?\n"
                f"Options: {', '.join(KNOWN_DATABASES[:10])} ...\n\n"
                "Enter database names separated by commas or spaces: "
            ),
        }

    # ===== Step 4: Select databases =====
    def handle_step4(self, user_input: str) -> dict[str, Any]:
        """Handle database selection."""
        if user_input.strip() in ("确认", "1", "ok", "yes", "好"):
            # Institution preset confirmation flow
            if not self.data.get("libraries"):
                return {"next": "retry", "prompt": "Enter database names: "}
        else:
            # Parse input
            libs = [s.strip() for s in user_input.replace(",", " ").split() if s.strip()]
            if libs:
                self.data["libraries"] = libs

        ok, msg = validate_libraries(self.data.get("libraries", []))
        if not ok:
            return {"next": "retry", "prompt": f"{msg}; enter it again: "}

        self.state = "step6"
        return {
            "next": "step6",
            "prompt": (
                f"Recorded {len(self.data['libraries'])} databases。\n\n"
                "Step 6: Running connectivity checks..."
            ),
        }

    # ===== Step 5: EZproxy URL =====
    def handle_step5(self, user_input: str) -> dict[str, Any]:
        """Handle the EZproxy URL."""
        url = user_input.strip()
        if url in ("跳过", "skip", ""):
            self.data["ezproxy_url"] = None
            self.state = "step4"
            return {
                "next": "step4",
                "prompt": (
                    "Skipped EZproxy.\n\n"
                    "Step 4: Which databases do you normally download from?\n"
                    "Enter database names separated by commas or spaces: "
                ),
            }

        ok, msg = validate_ezproxy_url(url)
        if not ok:
            return {
                "next": "retry",
                "prompt": f"{msg}\n\nEnter the EZproxy URL again, or 'skip': ",
            }

        self.data["ezproxy_url"] = url
        self.state = "step4"
        return {
            "next": "step4",
            "prompt": (
                f"EZproxy validation passed: {msg}\n\n"
                "Step 4: Which databases do you normally download from?\n"
                "Enter database names separated by commas or spaces: "
            ),
        }

    # ===== Step 6: Connectivity self-check =====
    def handle_step6(self, user_input: str = "") -> dict[str, Any]:
        """Run connectivity checks."""
        # Import lazily to avoid circular dependencies
        from health_check import health_check, clear_cache

        # Save temporary configuration before the self-check
        try:
            temp_config = self._build_config()
        except ValueError as e:
            return {"next": "retry", "prompt": f"Failed to construct configuration: {e}"}

        # Save temporarily for the self-check
        clear_cache()
        save_config(temp_config)
        result = health_check(force=True)

        self.state = "step7"
        details_text = "\n".join(f"  {d}" for d in result.get("details", []))
        if result["ok"]:
            return {
                "next": "step7",
                "prompt": (
                    f"Connectivity checks passed: \n{details_text}\n\n"
                    "Step 7: Save the configuration?\n  1. Confirm saving\n  2. Reconfigure"
                ),
            }
        else:
            suggestions = "\n".join(f"  {s}" for s in result.get("suggestions", []))
            return {
                "next": "step7",
                "prompt": (
                    f"Not all connectivity checks passed: \n{details_text}\n\n"
                    f"{suggestions}\n\n"
                    "Step 7: How would you like to proceed?\n"
                    "  1. Save anyway (can be corrected later)\n"
                    "  2. Reconfigure"
                ),
                "data": {"warnings": result.get("details", [])},
            }

    # ===== Step 7: Persistence =====
    def handle_step7(self, user_input: str) -> dict[str, Any]:
        """Handle the final save confirmation."""
        choice = user_input.strip()
        if choice in ("2", "重新配置", "重新"):
            delete_config()
            self.__init__()
            return {"next": "step1", "prompt": self.start()}

        # Save
        try:
            config = self._build_config()
            # Append warnings if present
            if self.data.get("warnings"):
                config["_warnings"] = self.data["warnings"]
            path = save_config(config)
            return {
                "next": "done",
                "prompt": (
                    f"Configured '{self.data['school_name']}' successfully!\n"
                    f"Configuration file: {path}\n\n"
                    "You can now download literature. To switch institutions, request reconfiguration or use /reconfig."
                ),
                "data": {"school": self.data["school_name"], "path": str(path)},
            }
        except ValueError as e:
            return {"next": "retry", "prompt": f"Save failed: {e}\nCheck the problem and retry: "}

    # ===== Dispatch entry point =====
    def handle(self, user_input: str) -> dict[str, Any]:
        """Dispatch to the handler for the current state."""
        handlers = {
            "step1": self.handle_step1,
            "step2": self.handle_step2,
            "step2b": self.handle_step2b,
            "step3": self.handle_step3,
            "step4": self.handle_step4,
            "step5": self.handle_step5,
            "step6": self.handle_step6,
            "step7": self.handle_step7,
        }
        handler = handlers.get(self.state)
        if handler is None:
            self.state = "step1"
            return {"next": "step1", "prompt": self.start()}
        return handler(user_input)

    # ===== Noninteractive configuration from an institution preset =====
    def configure_from_preset(self, school_name: str) -> dict[str, Any]:
        """Configure from an institution preset noninteractively.

        Return saved configuration on success; raise ValueError on failure.
        """
        preset = match_school(school_name)
        if not preset:
            raise ValueError(f"No institution preset found for '{school_name}」")

        auth = preset.get("auth", {})
        config = {
            "version": 1,
            "school": {
                "name": preset["name"],
                "code": preset.get("aliases", [""])[0] if preset.get("aliases") else None,
                "configured_at": datetime.now().isoformat(),
                "source": "preset",
            },
            "auth": {
                "type": auth.get("type", "cas"),
                "sso_domain": auth.get("sso_domain", ""),
                "carsi_entry": auth.get("carsi_entry") or None,
                "carsi_sp_entity_id": None,
            },
            "proxy": {
                "type": None,
                "ezproxy_url": None,
            },
            "libraries": preset.get("libraries", []),
            "discovery": preset.get("discovery", {}),
            "notes": preset.get("notes", ""),
        }

        path = save_config(config)
        return {"config": config, "path": str(path)}

    # ===== Noninteractive configuration from a resource entry URL =====
    def configure_from_resource_url(self, resource_url: str) -> dict[str, Any]:
        """Configure from a library resource portal or authentication URL."""
        inferred = infer_access_from_url(resource_url)
        self.data.update(inferred)
        self.data["school_name"] = inferred.get("institution_hint") or inferred["entry_host"]
        self.data["source"] = "resource_url"
        self.data["auth_type"] = inferred["auth_type"]
        self.data["sso_domain"] = inferred["sso_domain"]
        self.data["carsi_entry"] = inferred["resource_entry"]
        self.data["libraries"] = ["Web of Science", "ScienceDirect", "Springer", "IEEE Xplore", "知网", "ACS"]
        self.data["notes"] = inferred.get("notes", "")
        self.data["discovery"] = {"resource_entry_url": inferred["resource_entry"]}
        if inferred["entry_type"] == "resource_portal":
            self.data["discovery"]["resource_portal_url"] = inferred["resource_entry"]
        if inferred.get("service_host"):
            self.data["discovery"]["auth_service_host"] = inferred["service_host"]

        config = self._build_config()
        path = save_config(config)
        return {"config": config, "path": str(path), "inferred": inferred}

    # ===== Internal: construct the configuration dictionary =====
    def _build_config(self) -> dict[str, Any]:
        """Construct configuration from the collected wizard data."""
        if not self.data.get("school_name"):
            raise ValueError("Institution name is not set")
        if not self.data.get("sso_domain"):
            raise ValueError("SSO domain is not set")
        if not self.data.get("libraries"):
            raise ValueError("Database list is not set")

        return {
            "version": 1,
            "school": {
                "name": self.data["school_name"],
                "code": None,
                "configured_at": datetime.now().isoformat(),
                "source": self.data.get("source", "manual"),
            },
            "auth": {
                "type": self.data.get("auth_type", "cas"),
                "sso_domain": self.data["sso_domain"],
                "carsi_entry": self.data.get("carsi_entry") or None,
                "carsi_sp_entity_id": None,
            },
            "proxy": {
                "type": "ezproxy" if self.data.get("ezproxy_url") else None,
                "ezproxy_url": self.data.get("ezproxy_url") or None,
            },
            "libraries": self.data["libraries"],
            "discovery": self.data.get("discovery", {}),
            "notes": self.data.get("notes", ""),
        }


if __name__ == "__main__":
    # Noninteractive configuration example
    w = Wizard()
    try:
        result = w.configure_from_preset("交大")
        print(f"Configuration succeeded: {result['config']['school']['name']}")
        print(f"Configuration file: {result['path']}")
    except ValueError as e:
        print(f"Configuration failed: {e}")
        print(f"Configuration file path:{CONFIG_FILE}")
