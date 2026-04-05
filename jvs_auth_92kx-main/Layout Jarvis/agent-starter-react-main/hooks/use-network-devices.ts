'use client';

import { useState, useCallback, useEffect } from 'react';
import { toast } from 'sonner';
import { atlasLogger } from '../lib/atlas/event-logger';
import { AtlasDevice } from '../lib/atlas/types';

export const useNetworkDevices = () => {
  const [devices, setDevices] = useState<AtlasDevice[]>([]);
  const [isScanning, setIsScanning] = useState(false);

  const scan = useCallback(async () => {
    setIsScanning(true);
    atlasLogger.log('info', 'wifi', 'Iniciando escaneamento de rede local (Direct IP Scan)');
    
    // Simulação de descoberta na rede local
    setTimeout(() => {
        const discovered: AtlasDevice[] = [
            { 
                id: '192.168.1.44', 
                name: 'AC Master Hub', 
                type: 'ac', 
                protocol: 'wifi', 
                isConnected: true, 
                lastSeen: new Date() 
            },
            { 
                id: '192.168.1.50', 
                name: 'Main Light Controller', 
                type: 'light', 
                protocol: 'wifi', 
                isConnected: false, 
                lastSeen: new Date() 
            }
        ];
        setDevices(discovered);
        setIsScanning(false);
        atlasLogger.log('success', 'wifi', `Escaneamento concluído: ${discovered.length} dispositivos encontrados.`);
        toast.info(`Descobertos ${discovered.length} dispositivos Wi-Fi.`);
    }, 2000);
  }, []);

  const sendCommand = useCallback(async (ip: string, endpoint: string, payload: any) => {
    atlasLogger.log('info', 'wifi', `Transmitindo para ${ip}${endpoint}`, payload);
    
    try {
        // Mock de execução via HTTP local
        // const response = await fetch(`http://${ip}${endpoint}`, { method: 'POST', body: JSON.stringify(payload) });
        
        toast.promise(
            new Promise((resolve) => setTimeout(resolve, 800)),
            {
                loading: `Sinalizando hardware em ${ip}...`,
                success: `Resposta ACK recebida de ${ip}`,
                error: `Pacote perdido na rede local ${ip}`
            }
        );
        return true;
    } catch (err: any) {
        atlasLogger.log('error', 'wifi', `Erro de socket em ${ip}: ${err.message}`);
        return false;
    }
  }, []);

  return {
    devices,
    isScanning,
    scan,
    sendCommand
  };
};
