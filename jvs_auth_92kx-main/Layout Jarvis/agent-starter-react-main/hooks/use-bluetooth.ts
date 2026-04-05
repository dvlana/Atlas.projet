'use client';

import { useState, useCallback } from 'react';
import { toast } from 'sonner';

interface BluetoothDeviceState {
  connected: boolean;
  deviceName: string | null;
  device: any | null;
  services: any[];
}

export const useBluetooth = () => {
  const [state, setState] = useState<BluetoothDeviceState>({
    connected: false,
    deviceName: null,
    device: null,
    services: [],
  });

  const connect = useCallback(async () => {
    const nav = navigator as any;
    if (!nav.bluetooth) {
      toast.error('Bluetooth não suportado neste navegador.');
      return;
    }

    try {
      const nav = navigator as any;
      const device = await nav.bluetooth.requestDevice({
        acceptAllDevices: true,
        // É OBRIGATÓRIO listar os serviços que você quer acessar depois, mesmo com acceptAllDevices
        optionalServices: [
            '00001800-0000-1000-8000-00805f9b34fb', // Generic Access
            '00001801-0000-1000-8000-00805f9b34fb', // Generic Attribute
            '0000180a-0000-1000-8000-00805f9b34fb', // Device Information
            '0000ff01-0000-1000-8000-00805f9b34fb', // Common Custom
            '0000ff02-0000-1000-8000-00805f9b34fb', // Common Custom
            '0000fee7-0000-1000-8000-00805f9b34fb', // Milight
            '0000ffe0-0000-1000-8000-00805f9b34fb', // Generic Serial
        ]
      });

      const server = await device.gatt?.connect();
      
      setState({
        connected: true,
        deviceName: device.name || 'Dispositivo Desconhecido',
        device: device,
        services: [],
      });

      toast.success(`Conectado ao ${device.name || 'Dispositivo'}`);

      device.addEventListener('gattserverdisconnected', () => {
        setState({ connected: false, deviceName: null, device: null, services: [] });
        toast.info('Bluetooth desconectado.');
      });

      // Discover Initial services
      const services = await server.getPrimaryServices();
      const discoveredServices: any[] = [];
      for (const service of services) {
        try {
          const characteristics = await service.getCharacteristics();
          discoveredServices.push({
            uuid: service.uuid,
            characteristics: characteristics.map((c: any) => ({
              uuid: c.uuid,
              properties: c.properties
            }))
          });
        } catch (e) {
          console.warn(`Could not get characteristics for service ${service.uuid}`, e);
        }
      }
      
      setState(prev => ({ ...prev, services: discoveredServices }));

    } catch (error) {
      console.error('Erro Bluetooth:', error);
      toast.error('Falha ao conectar via Bluetooth.');
    }
  }, []);

  const disconnect = useCallback(() => {
    if (state.device && state.device.gatt?.connected) {
      state.device.gatt.disconnect();
    }
    setState({ connected: false, deviceName: null, device: null, services: [] });
  }, [state.device]);

  const sendCommand = useCallback(async (serviceUuid: string, characteristicUuid: string, data: Uint8Array) => {
    if (!state.device || !state.device.gatt?.connected) {
      toast.warning('Dispositivo não conectado.');
      return;
    }

    try {
      const server = await state.device.gatt.connect();
      const service = await server.getPrimaryService(serviceUuid);
      const characteristic = await service.getCharacteristic(characteristicUuid);
      await characteristic.writeValue(data);
      console.log('Comando enviado com sucesso!');
    } catch (error) {
      console.error('Erro ao enviar comando:', error);
      toast.error('Erro ao enviar comando para o dispositivo.');
    }
  }, [state.device]);

  return {
    ...state,
    connect,
    disconnect,
    sendCommand,
  };
};
