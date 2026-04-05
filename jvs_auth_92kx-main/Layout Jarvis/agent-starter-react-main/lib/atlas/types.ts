export type Protocol = 'bluetooth' | 'wifi' | 'cloud' | 'local_http' | 'mqtt';

export interface DeviceAction {
  target: string; // 'ar_condicionado', 'lampada', 'speaker', etc
  action: 'power_on' | 'power_off' | 'volume_up' | 'volume_down' | 'temperature_set' | 'toggle' | 'brightness_set' | 'status_report' | 'network_scan' | 'custom_command_create' | 'custom_command_execute';
  value?: any;
  protocol?: Protocol;
  deviceId?: string;
  subActions?: DeviceAction[]; // Para macros/prompts customizados
}

export interface AtlasDevice {
  id: string;
  name: string;
  type: 'light' | 'ac' | 'speaker' | 'sensor' | 'generic';
  protocol: Protocol;
  isConnected: boolean;
  lastSeen: Date;
  metadata?: Record<string, any>;
}

export interface AtlasEvent {
  timestamp: Date;
  level: 'info' | 'warn' | 'error' | 'success';
  source: 'ble' | 'wifi' | 'cloud' | 'broker' | 'hardware';
  message: string;
  data?: any;
}
