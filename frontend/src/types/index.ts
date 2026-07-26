export interface Department {
  id: string;
  name: string;
  code: string;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  department_id?: string;
  department?: Department;
  created_at: string;
  updated_at: string;
}

export interface UserMinimal {
  id: string;
  username: string;
  full_name: string;
  role: string;
}

export interface IndustrialAsset {
  id: string;
  name: string;
  ip_address: string;
  mac_address: string;
  vendor: string;
  model: string;
  asset_type: string;
  location: string;
  criticality: 'Critical' | 'High' | 'Medium' | 'Low';
  status: 'Operational' | 'Maintenance' | 'Offline';
  created_at: string;
  updated_at: string;
}

export interface Device {
  id: string;
  hostname: string;
  ip_address: string;
  mac_address: string;
  os_version: string;
  device_type: string;
  status: 'Authorized' | 'Quarantined' | 'Unknown';
  last_seen: string;
  created_at: string;
  updated_at: string;
}

export interface Event {
  id: string;
  timestamp: string;
  source_ip: string;
  destination_ip: string;
  protocol: string;
  event_type: string;
  payload_summary?: string;
  severity: 'Info' | 'Warning' | 'Critical';
  device_id?: string;
  asset_id?: string;
  user_id?: string;
  device?: Device;
  asset?: IndustrialAsset;
  user?: UserMinimal;
  created_at: string;
}

export interface Alert {
  id: string;
  title: string;
  description: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  status: 'New' | 'Investigating' | 'Resolved' | 'False Positive';
  category: string;
  asset_id?: string;
  device_id?: string;
  user_id?: string;
  asset?: IndustrialAsset;
  device?: Device;
  user?: UserMinimal;
  created_at: string;
  updated_at: string;
}

export interface RiskScore {
  id: string;
  score: number;
  entity_type: 'Asset' | 'Device' | 'User';
  entity_id: string;
  factors: Record<string, any>;
  last_calculated: string;
  created_at: string;
  updated_at: string;
}

export interface AuditLog {
  id: string;
  timestamp: string;
  action: string;
  ip_address: string;
  details: string;
  user_id?: string;
  user?: UserMinimal;
  created_at: string;
}

export interface BehaviorProfile {
  id: string;
  name: string;
  entity_type: string;
  working_schedule: { shift: string };
  login_time: string;
  logout_time: string;
  avg_event_volume: number;
  normal_devices: { hostnames: string[] };
  typical_apps: { apps: string[] };
  command_patterns: { actions: string[] };
  created_at?: string;
  updated_at?: string;
}
