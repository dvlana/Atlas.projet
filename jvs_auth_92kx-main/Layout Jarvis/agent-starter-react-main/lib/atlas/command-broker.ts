import { DeviceAction, Protocol } from './types';
import { atlasLogger } from './event-logger';

export interface BrokerHandlers {
  onBluetoothCommand: (svc: string, char: string, data: Uint8Array) => Promise<any>;
  onWiFiCommand: (ip: string, endpoint: string, data: any) => Promise<any>;
  onCloudCommand: (provider: string, action: string, data: any) => Promise<any>;
  onWiFiScan?: () => Promise<void>;
  onStatusReport?: (report: string) => void;
  connectedDevices: {
      bluetooth: boolean;
      wifi: boolean;
      cloud: boolean;
      deviceName?: string;
  };
  services?: any[];
}

export class CommandBroker {
  private static handlers: BrokerHandlers | null = null;
  private static customRegistry: Record<string, DeviceAction[]> = {};
  private static lastStatusStr: string = "";

  public static setHandlers(handlers: BrokerHandlers) {
    this.handlers = handlers;
    
    const { bluetooth, wifi, cloud } = handlers.connectedDevices;
    const statusStr = [
        bluetooth ? 'BLE ✓' : 'BLE ✗',
        wifi ? 'WiFi ✓' : 'WiFi ✗',
        cloud ? 'Cloud ✓' : 'Cloud ✗'
    ].join(' | ');

    // Silently update the status tracker without logging to the UI
    if (statusStr !== this.lastStatusStr) {
        this.lastStatusStr = statusStr;
    }
    
    // Carregar custom commands do storage
    try {
        const saved = localStorage.getItem('atlas_custom_commands');
        if (saved) this.customRegistry = JSON.parse(saved);
    } catch (e) {}
  }

  public static async execute(action: DeviceAction): Promise<boolean> {
    if (!this.handlers) {
        atlasLogger.log('warn', 'broker', 'Tentativa de execução sem handlers registrados');
        return false;
    }

    atlasLogger.log('info', 'broker', `Interpretando intenção: ${action.action} em ${action.target}`);

    try {
        switch (action.action) {
            case 'custom_command_create':
                if (action.value && action.subActions) {
                    this.customRegistry[action.value.toLowerCase()] = action.subActions;
                    localStorage.setItem('atlas_custom_commands', JSON.stringify(this.customRegistry));
                    atlasLogger.log('success', 'broker', `Novo comando criado: ${action.value}`);
                    return true;
                }
                return false;

            case 'custom_command_execute':
                if (action.subActions) {
                    atlasLogger.log('info', 'broker', `Executando Macro Customizada com ${action.subActions.length} ações`);
                    for (const sub of action.subActions) {
                        await this.execute(sub); // Recursão para executar passos da macro
                    }
                    return true;
                }
                return false;

            case 'network_scan':
                atlasLogger.log('info', 'wifi', 'AI solicitou escaneamento autônomo de rede.');
                // @ts-ignore (We'll add scan WiFi to handlers next)
                if (this.handlers.onWiFiScan) await this.handlers.onWiFiScan();
                return true;

            case 'status_report':
                const report = `[AUTO_STATUS_REPORT] 
BLE: ${this.handlers.connectedDevices.bluetooth ? 'Conectado em ' + this.handlers.connectedDevices.deviceName : 'Offline'}. 
Wi-Fi: ${this.handlers.connectedDevices.wifi ? 'Dispositivos detectados' : 'Nenhum ativo'}. 
Cloud (ThinQ): ${this.handlers.connectedDevices.cloud ? 'Sincronizado' : 'Offline'}.`;
                atlasLogger.log('info', 'broker', 'Relatório de status gerado para o Agente.');
                // @ts-ignore (We'll add status callback next)
                if (this.handlers.onStatusReport) this.handlers.onStatusReport(report);
                return true;
        }

        switch (action.protocol) {
            case 'bluetooth':
                if (!this.handlers.connectedDevices.bluetooth) throw new Error('Bluetooth offline');
                
                // Buscar dinamicamente um canal de escrita nos serviços reais do dispositivo
                const bleServices = (this.handlers as any).services || [];
                const writeChar = bleServices.flatMap((s: any) => 
                    s.characteristics.map((c: any) => ({ svc: s.uuid, char: c.uuid, props: c.properties }))
                ).find((c: any) => c.props.write || c.props.writeWithoutResponse);

                if (!writeChar) throw new Error('Dispositivo BLE sem canal de comando');

                const data = action.action.includes('power') ? 
                    new Uint8Array([action.action === 'power_on' ? 1 : 0]) : 
                    new Uint8Array([action.value || 0x01]);
                
                await this.handlers.onBluetoothCommand(writeChar.svc, writeChar.char, data);
                return true;

            case 'wifi':
                if (!this.handlers.connectedDevices.wifi) throw new Error('Network offline');
                await this.handlers.onWiFiCommand('192.168.1.50', '/api/v1/control', { action: action.action, value: action.value });
                return true;

            case 'cloud':
                await this.handlers.onCloudCommand('lg_thinq', action.action, action.value);
                return true;

            default:
                throw new Error('Protocolo de rede indefinido');
        }
    } catch (err: any) {
        atlasLogger.log('error', action.protocol as any || 'broker', `Fail: ${err.message}`);
        return false;
    }
  }

  // Melhora a interpretação de frases naturais para o sistema de comandos
  public static parseIntent(text: string): DeviceAction | null {
    const msg = text.toLowerCase();
    
    // 0. Reconhecimento de Comandos Customizados (Prioridade Root)
    for (const [name, actions] of Object.entries(this.customRegistry)) {
        if (msg.includes(name)) {
            return { target: 'custom', action: 'custom_command_execute', subActions: actions };
        }
    }

    // 1. Reconhecimento de CRIAÇÃO de comandos (Ex: "Atlas, crie um comando chamado 'cinema' que ligue o ar")
    if (msg.includes("crie um comando") || msg.includes("comando chamado") || msg.includes("atribua um prompt")) {
        const namePart = msg.match(/chamado '(.+?)'/)?.[1] || msg.match(/chamado (.+?) que/)?.[1];
        if (namePart) {
            // Tentar extrair a ação destino (recursivo)
            const subIntent = this.parseIntent(msg.split("que")[1] || msg);
            if (subIntent) {
                return { target: 'meta', action: 'custom_command_create', value: namePart, subActions: [subIntent] };
            }
        }
    }

    // 2. Intents Padrão
    if (msg.includes("quais dispositivos") || msg.includes("status do sistema") || msg.includes("o que encontrou") || msg.includes("relatório") || msg.includes("status do dia")) {
        return { target: 'all', action: 'status_report' };
    }

    // Reconhecimento de SCAN
    if (msg.includes("escanear") || msg.includes("procurar dispositivos") || msg.includes("atualizar rede")) {
        return { target: 'network', action: 'network_scan' };
    }

    // Reconhecimento de AR CONDICIONADO
    if (msg.includes("ar condicionado") || msg.includes("gelar") || msg.includes("turn on ac") || msg.includes("desligar ar")) {
        return {
            target: 'ac',
            action: msg.includes("desligar") ? 'power_off' : 'power_on',
            protocol: 'cloud'
        };
    }

    // Reconhecimento de LUZ / LAMPADA
    if (msg.includes("luz") || msg.includes("lampada") || msg.includes("led") || msg.includes("iluminação")) {
        return {
            target: 'light',
            action: msg.includes("desligar") || msg.includes("apagar") ? 'power_off' : 'power_on',
            protocol: 'bluetooth'
        };
    }

    // Reconhecimento de VOLUME / SPEAKER
    if (msg.includes("volume") || msg.includes("caixa") || msg.includes("som")) {
        return {
            target: 'speaker',
            action: msg.includes("aumentar") || msg.includes("up") ? 'volume_up' : 'volume_down',
            value: 10,
            protocol: 'bluetooth'
        };
    }

    return null;
  }
}
