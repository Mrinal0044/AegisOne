import logging
from typing import Dict, Any, List
from app.services.copilot.interfaces import LLMProvider

logger = logging.getLogger("app.services.copilot.fallback_provider")


class FallbackProvider(LLMProvider):
    """Deterministic, rule-based expert SOC analyst fallback provider."""

    def _detect_scenario(self, alert_data: Dict[str, Any]) -> str:
        classification = (alert_data.get("anomaly_classification") or "").lower()
        if "impossible travel" in classification:
            return "impossible_travel"
        elif "device spoofing" in classification:
            return "device_spoofing"
        elif "credential stuffing" in classification:
            return "credential_stuffing"
        elif "low-and-slow" in classification:
            return "low_slow_exfil"
        elif "insider drift" in classification:
            return "insider_drift"

        title = alert_data.get("title", "").lower()
        desc = alert_data.get("description", "").lower()
        
        if "insider" in title or "rogue" in title or "insider" in desc:
            return "insider_threat"
        elif "usb" in title or "malware" in title or "usb" in desc:
            return "usb_malware"
        elif "plc" in title or "manipulation" in title or "override" in title or "manipulation" in desc:
            return "plc_manipulation"
        elif "brute" in title or "force" in title or "ssh" in desc:
            return "brute_force"
        elif "lateral" in title or "movement" in title or "pivot" in desc:
            return "lateral_movement"
        elif "remote" in title or "vpn" in title or "tor" in desc:
            return "remote_access"
        elif "exfil" in title or "export" in title or "leak" in desc:
            return "data_exfiltration"
        return "generic_anomaly"

    def explain(self, alert_data: Dict[str, Any], timeline_data: List[Dict[str, Any]]) -> str:
        scenario = self._detect_scenario(alert_data)
        entity_name = alert_data.get("asset", {}).get("name") if alert_data.get("asset") else \
                      alert_data.get("device", {}).get("hostname") if alert_data.get("device") else "Target Entity"

        explanations = {
            "insider_threat": (
                f"**What Happened**:\nAn authorized domain user logged in outside standard working hours, accessed the SCADA server, "
                f"downloaded PLC logic parameters, and attempted to overwrite industrial register constants on {entity_name}.\n\n"
                f"**Why It is Suspicious**:\nActive configurations were altered at an unusual hour. The session bypassed standard operator authorization logs.\n\n"
                f"**Behavioral Deviation**:\nThe unsupervised Isolation Forest model flagged the session time and command write rate as highly anomalous "
                f"(deviation > 85%) compared to the user's historical 30-day baseline.\n\n"
                f"**Business Impact**:\nUnauthorized logic modifications could cause process disruptions, thermal limits escalation, or physical damage to industrial assets."
            ),
            "usb_malware": (
                f"**What Happened**:\nAn engineering workstation registered a mass storage connection, launched an unsigned binary installer, "
                f"and initiated S7comm writes to upload modified logic to {entity_name}.\n\n"
                f"**Why It is Suspicious**:\nUnsigned executable execution from external USB drives violates plant cyber policies. S7comm handshakes "
                f"from this terminal were not previously seen on this segment.\n\n"
                f"**Behavioral Deviation**:\nWorkstation file hash execution patterns deviated heavily from standard system baselines.\n\n"
                f"**Business Impact**:\nPotential malware propagation or ransomware infection targeting the ICS network segment, disrupting plant operations."
            ),
            "plc_manipulation": (
                f"**What Happened**:\nUnauthorized Modbus TCP command overrides were transmitted to {entity_name}, changing critical pump/valve flows.\n\n"
                f"**Why It is Suspicious**:\nThe commands bypassed standard HMI control logic, coming directly from a utility network terminal.\n\n"
                f"**Behavioral Deviation**:\nHigh transaction frequency of holding register writes deviated from normal telemetry polling frequencies.\n\n"
                f"**Business Impact**:\nPotential industrial damage or safety hazard due to pump overrides, resulting in pressure/flow boundary violations."
            ),
            "brute_force": (
                f"**What Happened**:\nA rapid burst of failed SSH authentication attempts occurred, followed by a successful login and SQL command execution.\n\n"
                f"**Why It is Suspicious**:\nFailed attempts occurred at a rate of 45/minute, indicating automated credential scanning.\n\n"
                f"**Behavioral Deviation**:\nAuth failure frequency exceeded standard operations tolerances by 300%.\n\n"
                f"**Business Impact**:\nCompromised administrative credentials could lead to full network takeover or access to critical operational segments."
            ),
            "lateral_movement": (
                f"**What Happened**:\nAn operator terminal initiated remote execution calls (WMI/RDP) to pivot across internal IP subnets.\n\n"
                f"**Why It is Suspicious**:\nWorkstation-to-workstation connections are restricted and do not align with daily operator workflows.\n\n"
                f"**Behavioral Deviation**:\nNew internal network ports were mapped, deviating from static connection baselines.\n\n"
                f"**Business Impact**:\nAn attacker could expand compromise from corporate IT networks into the high-security OT control segments."
            ),
            "remote_access": (
                f"**What Happened**:\nA VPN connection was established from a known TOR exit node, executing diagnostic PLC commands.\n\n"
                f"**Why It is Suspicious**:\nThe external source IP originated from a Dutch TOR node, violating strict geo-location guidelines.\n\n"
                f"**Behavioral Deviation**:\nGeographic location coordinates shifted instantly, representing an impossible travel threshold.\n\n"
                f"**Business Impact**:\nExternal rogue entities could establish persistent backdoor access to core SCADA servers."
            ),
            "data_exfiltration": (
                f"**What Happened**:\nHistorian database logs were compressed into a tarball and uploaded to an external web repository.\n\n"
                f"**Why It is Suspicious**:\nInternal plant production numbers were sent to a foreign public destination IP.\n\n"
                f"**Behavioral Deviation**:\nOutbound data volume (exceeding 2.5 GB) deviated significantly from daily network upload baseline averages.\n\n"
                f"**Business Impact**:\nLoss of proprietary manufacturing metrics, intellectual property, or operational recipes."
            ),
            "impossible_travel": (
                f"**What Happened**:\nAn Impossible Travel alert was generated for the user session on {entity_name}.\n\n"
                f"**Why It is Suspicious**:\nLogons occurred from geographically separated locations at a speed exceeding speed thresholds, violating physical travel speed limits.\n\n"
                f"**Behavioral Deviation**:\nFirst-time login from new geographic coordinates coupled with a drastic timezone transition.\n\n"
                f"**Business Impact**:\nHigh probability of compromised session tokens or account credentials shared with a rogue external operator."
            ),
            "device_spoofing": (
                f"**What Happened**:\nA Device Spoofing alert was fired for device {entity_name}.\n\n"
                f"**Why It is Suspicious**:\nA known host connected using modified OS versions, browser user agents, MAC addresses, or TLS signatures, indicating fingerprint forgery.\n\n"
                f"**Behavioral Deviation**:\nDevice fingerprint drift ratio exceeded system configuration limits.\n\n"
                f"**Business Impact**:\nRogue engineering workstation attempting to impersonate trusted control room terminals."
            ),
            "credential_stuffing": (
                f"**What Happened**:\nHigh-frequency authentication failures targeting multiple operator accounts from a single IP address.\n\n"
                f"**Why It is Suspicious**:\nThe login attempts targeted distinct user accounts in rapid succession, concluding in a successful compromise.\n\n"
                f"**Behavioral Deviation**:\nMulti-account credential scan pattern deviates from standard operational credentials usage.\n\n"
                f"**Business Impact**:\nCritical threat. Credential stuffing compromise allows unauthorized access to plant historians and SCADA systems."
            ),
            "low_slow_exfil": (
                f"**What Happened**:\nLow-and-slow data exfiltration sequence detected on {entity_name}.\n\n"
                f"**Why It is Suspicious**:\nSmall, periodic off-shift database queries and uploads were executed over several days to bypass single-event volume thresholds.\n\n"
                f"**Behavioral Deviation**:\nLong-term rolling behavior feature analysis identified gradual abnormal growth in total outbound network bytes.\n\n"
                f"**Business Impact**:\nLoss of intellectual property, proprietary plant logs, and historical process data."
            ),
            "insider_drift": (
                f"**What Happened**:\nInsider drift simulation alert triggered on {entity_name}.\n\n"
                f"**Why It is Suspicious**:\nA trusted operator gradually expanded department access footprints, increased command diversity, and escalated PLC writes.\n\n"
                f"**Behavioral Deviation**:\nGradual behavioral drift over multiple days representing either suspicious privilege creeping or legitimate workload growth.\n\n"
                f"**Business Impact**:\nRisk of credential misuse, malicious insider drift, or unauthorized operational expansion."
            ),
            "generic_anomaly": (
                f"**What Happened**:\nThe AI Detection Engine flagged abnormal activities on {entity_name}.\n\n"
                f"**Why It is Suspicious**:\nTelemetry characteristics (frequency, protocol headers, or active hour) deviated from baseline profiles.\n\n"
                f"**Behavioral Deviation**:\nUnsupervised model distance metrics fell outside standard operational confidence boundaries.\n\n"
                f"**Business Impact**:\nPotential unauthorized access, system misconfiguration, or initial stage of cyber intrusion."
            )
        }
        return explanations[scenario]

    def recommend(self, alert_data: Dict[str, Any]) -> str:
        scenario = self._detect_scenario(alert_data)
        recommendations = {
            "insider_threat": (
                "- Temporarily isolate the operator session and disable user domain account.\n"
                "- Revoke all active network/VPN authentication tokens associated with the employee.\n"
                "- Audit plant SCADA logs to compile a delta of changed parameter registers.\n"
                "- Cross-reference shift logs to verify physical presence of employee on-site."
            ),
            "usb_malware": (
                "- Disconnect the target engineering workstation network interface card immediately.\n"
                "- Scan all workstation mounting paths for unauthorized USB mass storage devices.\n"
                "- Restore the PLC configuration parameters to the last known-good backup state.\n"
                "- Run deep malware scans on the local operating system to identify active payloads."
            ),
            "plc_manipulation": (
                "- Implement firewall restrictions blocking direct terminal connections to the PLC Modbus port.\n"
                "- Force process parameters back to standard operating baseline configurations via HMI.\n"
                "- Capture local network traffic (PCAPs) on the plant switch for detailed payload analysis.\n"
                "- Review Modbus authorization matrices to verify access constraints."
            ),
            "brute_force": (
                "- Block the source scanning IP address on the perimeter and segment firewalls.\n"
                "- Enforce immediate account password resets and configure multi-factor authentication (MFA).\n"
                "- Audit system authentication logs to identify any other targets of credential scanning.\n"
                "- Inspect SSH configuration to restrict root access permissions."
            ),
            "lateral_movement": (
                "- Quarantine the pivoting workstation terminal immediately to contain spread.\n"
                "- Disable lateral communication pathways (SMB, WMI, RDP) between local control subnet nodes.\n"
                "- Reset domain credentials for any accounts utilized during the pivot sequence.\n"
                "- Check system registry logs for evidence of tool compilation."
            ),
            "remote_access": (
                "- Terminate the active VPN connection session and disable the credentials used.\n"
                "- Update external firewall policies to block traffic originating from known TOR exit nodes.\n"
                "- Review VPN endpoint connection histories to identify other access attempts.\n"
                "- Force credential rotation for all remote-access users."
            ),
            "data_exfiltration": (
                "- Block the destination IP address on the border gateway firewall.\n"
                "- Audit historian database access logs to identify the user/service account queried.\n"
                "- Restrict outbound HTTPS/FTP connections from the OT subnet to verified white-listed domains.\n"
                "- Review database connection settings to restrict large data dumps."
            ),
            "impossible_travel": (
                "- Immediately lock the user account and terminate all active web/VPN sessions.\n"
                "- Require out-of-band identity verification (MFA/Phone) for the affected operator.\n"
                "- Enforce credential rotation for the target account."
            ),
            "device_spoofing": (
                "- Quarantine the affected host terminal at the switch level immediately.\n"
                "- Inspect the MAC address and network card characteristics of the workstation.\n"
                "- Verify if any network bridge or host spoofing software is running on the terminal."
            ),
            "credential_stuffing": (
                "- Blacklist the scanning source IP on the firewall gateway.\n"
                "- Temporarily lock all user accounts targeted by the failed login sweep.\n"
                "- Force credential rotation and enable multi-factor auth (MFA)."
            ),
            "low_slow_exfil": (
                "- Limit database query rates and block historian logs download permissions.\n"
                "- Block external uploads on the plant gateway firewall.\n"
                "- Enforce file transfer size restrictions on internal network interfaces."
            ),
            "insider_drift": (
                "- Perform an entitlement audit to verify the user's need-to-know access.\n"
                "- Restrict command authorization levels for the operator.\n"
                "- Tune baseline sensitivity thresholds if legitimate workload growth is confirmed."
            ),
            "generic_anomaly": (
                "- Review recent command logs on the affected device/asset.\n"
                "- Isolate the target network node if anomalous network traffic continues.\n"
                "- Check host performance metrics for signs of CPU/Memory utilization spikes.\n"
                "- Validate that configuration changes were approved via change management processes."
            )
        }
        return recommendations[scenario]

    def explain_timeline(self, timeline_data: List[Dict[str, Any]]) -> str:
        if not timeline_data:
            return "No recent sequence logs recorded. The system is operating within normal baseline boundaries."
        
        steps_summary = []
        for step in timeline_data:
            steps_summary.append(f"*{step.get('current_step', 'Operation')}* ({step.get('payload_summary', 'Normal execution')})")
            
        narrative = " -> ".join(steps_summary)
        return f"Chronological attack progression: {narrative}."

    def executive_summary(self, alert_data: Dict[str, Any], timeline_data: List[Dict[str, Any]]) -> str:
        scenario = self._detect_scenario(alert_data)
        severity = alert_data.get("severity", "Medium")
        entity_name = alert_data.get("asset", {}).get("name") if alert_data.get("asset") else \
                      alert_data.get("device", {}).get("hostname") if alert_data.get("device") else "Target Entity"

        summaries = {
            "insider_threat": (
                f"**Incident Overview**: High-risk out-of-hours operator activity identified on {entity_name}.\n"
                f"**Business Impact**: High. Direct modification of industrial parameters could interrupt production line flows.\n"
                f"**Current Status**: Account isolated. System validation underway.\n"
                f"**Recommended Action**: Audit changed registers and restore PLC configuration state."
            ),
            "usb_malware": (
                f"**Incident Overview**: Unsigned installer executed from a USB device on an engineering workstation.\n"
                f"**Business Impact**: Critical. Malware propagation risk inside high-security OT segments.\n"
                f"**Current Status**: Workstation quarantined. PLC integrity check in progress.\n"
                f"**Recommended Action**: Perform malware scan and restore PLC logic."
            ),
            "plc_manipulation": (
                f"**Incident Overview**: Direct Modbus override command burst sent to {entity_name}.\n"
                f"**Business Impact**: Critical. Bypassing HMI logic can cause hardware strain or physical safety risks.\n"
                f"**Current Status**: Direct Modbus ports blocked. HMI parameter verification active.\n"
                f"**Recommended Action**: Restrict network routing access rules to the PLC."
            ),
            "brute_force": (
                f"**Incident Overview**: SSH credential brute force attack followed by command execution.\n"
                f"**Business Impact**: High. Risk of credential compromise and administrative privilege takeover.\n"
                f"**Current Status**: Source IP blacklisted. Account credentials scheduled for rotation.\n"
                f"**Recommended Action**: Audit authentication rules and enforce password policies."
            ),
            "lateral_movement": (
                f"**Incident Overview**: Pivot attempts detected from internal workstation to control network nodes.\n"
                f"**Business Impact**: High. Attackers attempting to bridge IT networks into high-security OT subnets.\n"
                f"**Current Status**: Source node isolated. Internal RPC/SMB sessions closed.\n"
                f"**Recommended Action**: Restrict cross-subnet traffic on segment switch firewalls."
            ),
            "remote_access": (
                f"**Incident Overview**: VPN login from a TOR exit IP address executing PLC diagnostic checks.\n"
                f"**Business Impact**: High. Potential foreign intruder access to SCADA core databases.\n"
                f"**Current Status**: VPN session terminated. Remote authentication revoked.\n"
                f"**Recommended Action**: Update border firewall filters to drop TOR IPs."
            ),
            "data_exfiltration": (
                f"**Incident Overview**: Historian database export and external web transmission.\n"
                f"**Business Impact**: High. Compromise of proprietary plant recipes and execution metrics.\n"
                f"**Current Status**: Target external IP blocked. DB connection restricted.\n"
                f"**Recommended Action**: Limit external out-of-band communication pathways from OT subnets."
            ),
            "impossible_travel": (
                f"**Incident Overview**: Impossible travel detected for user logon on {entity_name}.\n"
                f"**Business Impact**: High. Access from suspicious geography indicates token or credential theft.\n"
                f"**Current Status**: Account locked. Out-of-band validation initiated.\n"
                f"**Recommended Action**: Terminate active connections and reset passwords."
            ),
            "device_spoofing": (
                f"**Incident Overview**: Device hardware spoofing detected on {entity_name}.\n"
                f"**Business Impact**: High. Trusted workstation impersonation indicates host forgery.\n"
                f"**Current Status**: Host quarantined. Network segment logs under inspection.\n"
                f"**Recommended Action**: Verify MAC table allocations and physical terminal settings."
            ),
            "credential_stuffing": (
                f"**Incident Overview**: Credential Stuffing auth failures and subsequent compromise.\n"
                f"**Business Impact**: Critical. Multi-account credential compromise risk.\n"
                f"**Current Status**: Scanning IP blocked. Targeted accounts locked.\n"
                f"**Recommended Action**: Audit authentication rules and enforce MFA."
            ),
            "low_slow_exfil": (
                f"**Incident Overview**: Off-hours low-and-slow exfiltration sequence identified on {entity_name}.\n"
                f"**Business Impact**: High. Data leakage threat of proprietary historian logs.\n"
                f"**Current Status**: Target external IP blocked. DB connection restricted.\n"
                f"**Recommended Action**: Limit external out-of-band communication pathways from OT subnets."
            ),
            "insider_drift": (
                f"**Incident Overview**: gradual privilege drift threat verified on {entity_name}.\n"
                f"**Business Impact**: Medium/High. Operator command creep or malicious insider drift.\n"
                f"**Current Status**: Privilege expansion audited. Command limits restricted.\n"
                f"**Recommended Action**: Re-verify baseline calibration templates."
            ),
            "generic_anomaly": (
                f"**Incident Overview**: AI Detection Engine identified behavioral baseline anomaly on {entity_name}.\n"
                f"**Business Impact**: Medium. Risk of unauthorized modifications or configuration drift.\n"
                f"**Current Status**: Monitoring logs for continuation metrics.\n"
                f"**Recommended Action**: Verify authorization logs for the anomaly timeframe."
            )
        }
        return summaries[scenario]

    def generate_report(self, alert_data: Dict[str, Any], timeline_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "explanation": self.explain(alert_data, timeline_data),
            "recommendations": self.recommend(alert_data),
            "timeline_summary": self.explain_timeline(timeline_data),
            "executive_summary": self.executive_summary(alert_data, timeline_data)
        }
