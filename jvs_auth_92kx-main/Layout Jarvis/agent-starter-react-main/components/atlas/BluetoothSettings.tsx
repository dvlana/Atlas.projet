'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { X, Save, Bluetooth, Search, CheckCircle2, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

interface BluetoothSettingsProps {
  isOpen: boolean;
  onClose: () => void;
  discoveredServices: any[];
  deviceName: string | null;
}

export const BluetoothSettings = ({ isOpen, onClose, discoveredServices, deviceName }: BluetoothSettingsProps) => {
  const [activeConfig, setActiveConfig] = useState({
    serviceUuid: '',
    characteristicUuid: '',
    onValue: '1',
    offValue: '0'
  });

  useEffect(() => {
    const saved = localStorage.getItem('atlas_bluetooth_config');
    if (saved) {
      setActiveConfig(JSON.parse(saved));
    }
  }, []);

  const handleSave = () => {
    localStorage.setItem('atlas_bluetooth_config', JSON.stringify(activeConfig));
    toast.success('Configuração Bluetooth salva com sucesso!');
    onClose();
  };

  const selectCharacteristic = (sUuid: string, cUuid: string) => {
    setActiveConfig(prev => ({ ...prev, serviceUuid: sUuid, characteristicUuid: cUuid }));
    toast.info(`Selecionado: ${cUuid.slice(0, 8)}...`);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 sm:p-12">
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 bg-black/40 backdrop-blur-md"
        onClick={onClose}
      />
      
      <motion.div 
        initial={{ scale: 0.9, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.9, opacity: 0, y: 20 }}
        className="relative w-full max-w-2xl bg-white rounded-[2.5rem] shadow-2xl overflow-hidden flex flex-col max-h-[85vh] border border-white/50"
      >
        {/* Header */}
        <div className="p-8 pb-4 flex justify-between items-center border-b border-slate-100">
           <div>
              <h2 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
                <Bluetooth className="text-blue-500" /> Mapeamento Inteligente
              </h2>
              <p className="text-sm text-slate-400 mt-1">Configure o controle do seu hardware</p>
           </div>
           <button onClick={onClose} className="p-2 hover:bg-slate-100 rounded-full transition-colors">
              <X className="w-6 h-6 text-slate-400" />
           </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-8 space-y-8">
            
            {/* Status Section */}
            <div className="p-4 rounded-3xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${deviceName ? 'bg-green-500' : 'bg-slate-300'}`}></div>
                    <span className="font-medium text-slate-700">{deviceName || 'Nenhum dispositivo conectado'}</span>
                </div>
                {!deviceName && <p className="text-xs text-slate-400 italic">Conecte via Bluetooth primeiro</p>}
            </div>

            {/* Config Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                    <label className="text-xs font-bold uppercase tracking-wider text-slate-400 ml-1">Service UUID</label>
                    <input 
                        className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-sm font-mono"
                        placeholder="Ex: 0000ff01-0000-..."
                        value={activeConfig.serviceUuid}
                        onChange={(e) => setActiveConfig(prev => ({ ...prev, serviceUuid: e.target.value }))}
                    />
                </div>
                <div className="space-y-2">
                    <label className="text-xs font-bold uppercase tracking-wider text-slate-400 ml-1">Characteristic UUID</label>
                    <input 
                        className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-sm font-mono"
                        placeholder="Ex: 0000ff02-0000-..."
                        value={activeConfig.characteristicUuid}
                        onChange={(e) => setActiveConfig(prev => ({ ...prev, characteristicUuid: e.target.value }))}
                    />
                </div>
            </div>

            {/* Discovered Services List */}
            {discoveredServices.length > 0 && (
                <div className="space-y-4">
                    <h3 className="text-sm font-bold text-slate-900 border-b pb-2">Serviços Detectados (Selecione um)</h3>
                    <div className="space-y-3">
                        {discoveredServices.map((service) => (
                            <div key={service.uuid} className="bg-slate-50 rounded-2xl overflow-hidden border border-slate-100">
                                <div className="px-4 py-2 bg-slate-100/50 text-[10px] font-mono text-slate-500 border-b border-slate-100">
                                    Service: {service.uuid}
                                </div>
                                <div className="p-2 space-y-1">
                                    {service.characteristics.map((char: any) => (
                                        <button 
                                            key={char.uuid}
                                            onClick={() => selectCharacteristic(service.uuid, char.uuid)}
                                            className="w-full text-left px-4 py-2 hover:bg-white hover:shadow-sm rounded-xl transition-all flex items-center justify-between group"
                                        >
                                            <span className="text-xs text-slate-600 font-mono">{char.uuid}</span>
                                            <Search className="w-3 h-3 text-slate-300 group-hover:text-blue-500 transition-colors" />
                                        </button>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>

        {/* Footer */}
        <div className="p-8 pt-4 bg-slate-50/50 border-t border-slate-100 flex justify-end gap-3">
            <button onClick={onClose} className="px-6 py-3 text-slate-500 font-medium hover:text-slate-700 transition-colors">Cancelar</button>
            <button 
                onClick={handleSave}
                className="px-8 py-3 bg-slate-900 text-white rounded-2xl font-bold flex items-center gap-2 hover:bg-slate-800 transition-all shadow-lg active:scale-95"
            >
                <Save className="w-4 h-4" /> Salvar Configuração
            </button>
        </div>
      </motion.div>
    </div>
  );
};
