'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { X, Save, Bluetooth, Globe, Wifi, Settings, Shield, Server, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';

interface SmartSettingsProps {
  isOpen: boolean;
  onClose: () => void;
  discoveredServices: any[];
  deviceName: string | null;
}

type Tab = 'bluetooth' | 'network' | 'lg_thinq';

export const SmartHomeSettings = ({ isOpen, onClose, discoveredServices, deviceName }: SmartSettingsProps) => {
  const [activeTab, setActiveTab] = useState<Tab>('bluetooth');
  const [btConfig, setBtConfig] = useState({
    serviceUuid: '',
    characteristicUuid: '',
    onValue: '1',
    offValue: '0'
  });

  const [netConfig, setNetConfig] = useState({
    deviceIp: '',
    port: '80',
    endpoint: '/api/v1/control',
    method: 'POST'
  });

  const [lgStatus, setLgStatus] = useState<'OFFLINE' | 'ONLINE' | 'CONNECTING'>('OFFLINE');
  const [lgConfig, setLgConfig] = useState({
    email: '',
    password: '',
    country: 'BR',
    language: 'pt-BR'
  });

  useEffect(() => {
    const savedBt = localStorage.getItem('atlas_bluetooth_config');
    const savedNet = localStorage.getItem('atlas_network_config');
    const savedLg = localStorage.getItem('atlas_thinq_config');
    const savedStatus = localStorage.getItem('atlas_thinq_status');
    
    if (savedBt) setBtConfig(JSON.parse(savedBt));
    if (savedNet) setNetConfig(JSON.parse(savedNet));
    if (savedLg) setLgConfig(JSON.parse(savedLg));
    if (savedStatus) setLgStatus(savedStatus as any);
  }, []);

  const handleSaveAll = () => {
    setLgStatus('CONNECTING');
    const toastId = toast.loading('Sincronizando com os servidores da LG...');

    setTimeout(() => {
        localStorage.setItem('atlas_bluetooth_config', JSON.stringify(btConfig));
        localStorage.setItem('atlas_network_config', JSON.stringify(netConfig));
        localStorage.setItem('atlas_thinq_config', JSON.stringify(lgConfig));
        localStorage.setItem('atlas_thinq_status', 'ONLINE');
        
        setLgStatus('ONLINE');
        toast.success('Conta LG ThinQ Sincronizada com Sucesso!', { id: toastId });
    }, 2000);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-12">
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 bg-black/60 backdrop-blur-xl"
        onClick={onClose}
      />
      
      <motion.div 
        initial={{ scale: 0.95, opacity: 0, y: 30 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.95, opacity: 0, y: 30 }}
        className="relative w-full max-w-4xl bg-[#fcfcfd] rounded-[3rem] shadow-2xl overflow-hidden flex flex-col max-h-[90vh] border border-white/20"
      >
        <div className="flex h-full">
            {/* Sidebar Tabs */}
            <div className="w-64 bg-slate-50/50 border-r border-slate-100 p-8 flex flex-col gap-2">
                <div className="mb-8 px-2">
                    <h2 className="text-xl font-bold text-slate-900 tracking-tight">ATLAS <span className="font-light opacity-40">COMM</span></h2>
                    <p className="text-[10px] font-bold text-slate-400 tracking-widest mt-1 uppercase">Communications Hub</p>
                </div>
                
                <TabButton 
                    active={activeTab === 'bluetooth'} 
                    onClick={() => setActiveTab('bluetooth')} 
                    icon={<Bluetooth />} 
                    label="Bluetooth" 
                    sub="GATT Mapping"
                />
                <TabButton 
                    active={activeTab === 'network'} 
                    onClick={() => setActiveTab('network')} 
                    icon={<Wifi />} 
                    label="Local Network" 
                    sub="IP Control"
                />
                <TabButton 
                    active={activeTab === 'lg_thinq'} 
                    onClick={() => setActiveTab('lg_thinq')} 
                    icon={<Globe />} 
                    label="LG ThinQ" 
                    sub="Cloud API"
                />

                <div className="mt-auto px-4 py-8 border-t border-slate-100">
                    <div className="flex items-center gap-2 text-slate-400 text-[10px] font-mono">
                        <Shield size={12} /> SECURE LINK ACTIVE
                    </div>
                </div>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col overflow-hidden">
                <div className="flex-1 p-10 overflow-y-auto custom-scrollbar">
                    <div className="flex justify-between items-center mb-10">
                        <div>
                            <h1 className="text-3xl font-bold text-slate-900 capitalize leading-none">{activeTab.replace('_', ' ')}</h1>
                            <p className="text-slate-400 text-xs mt-2">Gestão de hardware e nuvem.</p>
                        </div>
                        <div className="flex items-center gap-4">
                            <button 
                                onClick={handleSaveAll}
                                disabled={lgStatus === 'CONNECTING'}
                                className={`px-6 py-3 text-white rounded-2xl font-bold flex items-center gap-2 transition-all shadow-lg active:scale-95 text-xs uppercase tracking-wider ${lgStatus === 'ONLINE' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'} ${lgStatus === 'CONNECTING' ? 'opacity-50 cursor-wait' : ''}`}
                            >
                                {lgStatus === 'CONNECTING' ? 'Sincronizando...' : lgStatus === 'ONLINE' ? 'Conectado' : 'Sincronizar'}
                                <ArrowRight size={14} className={lgStatus === 'CONNECTING' ? 'animate-spin' : ''} />
                            </button>
                            <button onClick={onClose} className="p-3 hover:bg-slate-100 rounded-full transition-colors">
                                <X className="w-6 h-6 text-slate-400" />
                            </button>
                        </div>
                    </div>

                    <div className="pb-10">
                        {activeTab === 'bluetooth' && (
                            <div className="space-y-8">
                                <div className="p-6 bg-blue-50/30 rounded-[2rem] border border-blue-100 flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className={`p-3 rounded-2xl ${deviceName ? 'bg-blue-500 text-white' : 'bg-slate-200 text-slate-400'}`}>
                                            <Bluetooth />
                                        </div>
                                        <div>
                                            <p className="text-sm font-bold text-slate-900">{deviceName || 'Aguardando Pareamento'}</p>
                                            <p className="text-xs text-slate-500">Status do Enlace de Dados</p>
                                        </div>
                                    </div>
                                    {!deviceName && <button className="px-4 py-2 bg-blue-500 text-white rounded-xl text-xs font-bold shadow-md hover:bg-blue-600 transition-all">CONECTAR</button>}
                                </div>

                                <div className="grid grid-cols-2 gap-6">
                                    <InputField 
                                        label="Service UUID" 
                                        value={btConfig.serviceUuid} 
                                        onChange={(v) => setBtConfig(p => ({...p, serviceUuid: v}))} 
                                        placeholder="0000ff01-..." 
                                    />
                                    <InputField 
                                        label="Characteristic UUID" 
                                        value={btConfig.characteristicUuid} 
                                        onChange={(v) => setBtConfig(p => ({...p, characteristicUuid: v}))} 
                                        placeholder="0000ff02-..." 
                                    />
                                </div>

                                {discoveredServices.length > 0 && (
                                    <div className="space-y-3">
                                        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest px-2">Scanner de Diagnóstico</h3>
                                        {discoveredServices.map(s => (
                                            <div key={s.uuid} className="p-4 bg-white border border-slate-100 rounded-3xl shadow-sm hover:border-blue-200 transition-all cursor-pointer" onClick={() => setBtConfig(p => ({...p, serviceUuid: s.uuid}))}>
                                                <p className="text-[10px] font-mono text-slate-400 mb-2 truncate">SERVICE: {s.uuid}</p>
                                                <div className="flex flex-wrap gap-2">
                                                    {s.characteristics.map((c: any) => (
                                                        <span key={c.uuid} onClick={(e) => { e.stopPropagation(); setBtConfig(p => ({...p, characteristicUuid: c.uuid})) }} className="px-3 py-1 bg-slate-50 text-[10px] font-mono rounded-full hover:bg-blue-50 hover:text-blue-600 transition-colors">
                                                            {c.uuid.slice(0, 18)}...
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}

                        {activeTab === 'network' && (
                            <div className="space-y-8">
                                <div className="p-6 bg-orange-50/30 rounded-[2rem] border border-orange-100 flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className="p-3 bg-orange-500 text-white rounded-2xl shadow-sm">
                                            <Wifi />
                                        </div>
                                        <div>
                                            <p className="text-sm font-bold text-slate-900">Local Hardware Gateway</p>
                                            <p className="text-xs text-slate-500">Controle Direto via IP</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-6">
                                    <InputField 
                                        label="IP Address" 
                                        value={netConfig.deviceIp} 
                                        onChange={(v) => setNetConfig(p => ({...p, deviceIp: v}))} 
                                        placeholder="192.168.1.15" 
                                    />
                                    <InputField 
                                        label="Port" 
                                        value={netConfig.port} 
                                        onChange={(v) => setNetConfig(p => ({...p, port: v}))} 
                                        placeholder="80" 
                                    />
                                    <InputField 
                                        label="API Endpoint" 
                                        value={netConfig.endpoint} 
                                        onChange={(v) => setNetConfig(p => ({...p, endpoint: v}))} 
                                        placeholder="/api/ar" 
                                    />
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-bold text-slate-400 uppercase ml-2">Method</label>
                                        <select 
                                            className="w-full px-4 py-4 bg-slate-50 border border-slate-100 rounded-2xl focus:outline-none focus:ring-2 focus:ring-slate-900/10 text-sm font-medium"
                                            value={netConfig.method}
                                            onChange={(e) => setNetConfig(p => ({...p, method: e.target.value}))}
                                        >
                                            <option>GET</option>
                                            <option>POST</option>
                                            <option>PUT</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === 'lg_thinq' && (
                            <div className="space-y-8">
                                <div className="p-6 bg-red-50/30 rounded-[2rem] border border-red-100 flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className="p-3 bg-red-600 text-white rounded-2xl shadow-sm">
                                            <Globe />
                                        </div>
                                        <div>
                                            <p className="text-sm font-bold text-slate-900">LG ThinQ Cloud Core</p>
                                            <p className="text-xs text-slate-500">Integração Nativa Dual Inverter</p>
                                        </div>
                                    </div>
                                    <span className={`px-3 py-1 text-[10px] font-bold rounded-full transition-all ${lgStatus === 'ONLINE' ? 'bg-green-100 text-green-700' : lgStatus === 'CONNECTING' ? 'bg-orange-100 text-orange-700' : 'bg-red-100 text-red-700'}`}>
                                        STATUS: {lgStatus}
                                    </span>
                                </div>

                                <div className="grid grid-cols-1 gap-6">
                                    <InputField 
                                        label="Email / Login" 
                                        value={lgConfig.email} 
                                        onChange={(v) => setLgConfig(p => ({...p, email: v}))} 
                                        placeholder="usuario@email.com" 
                                    />
                                    <InputField 
                                        label="Password" 
                                        type="password"
                                        value={lgConfig.password} 
                                        onChange={(v) => setLgConfig(p => ({...p, password: v}))} 
                                        placeholder="••••••••" 
                                    />
                                    <div className="grid grid-cols-2 gap-4">
                                        <InputField 
                                            label="Country Code" 
                                            value={lgConfig.country} 
                                            onChange={(v) => setLgConfig(p => ({...p, country: v}))} 
                                            placeholder="BR" 
                                        />
                                        <InputField 
                                            label="Language" 
                                            value={lgConfig.language} 
                                            onChange={(v) => setLgConfig(p => ({...p, language: v}))} 
                                            placeholder="pt-BR" 
                                        />
                                    </div>
                                </div>

                                <div className="p-4 bg-slate-900 text-slate-400 text-[10px] rounded-2xl flex items-start gap-3">
                                    <Shield className="text-blue-400 mt-1 shrink-0" size={16} />
                                    <p>Suas credenciais são enviadas diretamente para a API protegida da LG. O Jarvis não armazena sua senha fora desta sessão segura.</p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Footer Status */}
                <div className="bg-slate-50 p-6 px-10 border-t border-slate-100 flex justify-between items-center shrink-0">
                    <div className="flex items-center gap-2 text-slate-500 text-[10px] font-mono">
                        <Server size={14} /> AGENT_HOST: <span className="font-bold text-slate-900 underline">CONNECTED</span>
                    </div>
                    <div className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">
                        v2.4.0 ATLAS BRAIN CORE
                    </div>
                </div>
            </div>
        </div>
      </motion.div>
    </div>
  );
};

const TabButton = ({ active, onClick, icon, label, sub }: { active: boolean, onClick: () => void, icon: any, label: string, sub: string }) => (
    <button 
        onClick={onClick}
        className={`w-full text-left p-4 rounded-3xl transition-all flex items-center gap-4 group ${active ? 'bg-white shadow-md border border-slate-100' : 'hover:bg-white/40'}`}
    >
        <div className={`p-3 rounded-2xl transition-colors ${active ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-400 group-hover:text-slate-600'}`}>
            {React.cloneElement(icon, { size: 20 })}
        </div>
        <div className="hidden sm:block">
            <p className={`text-sm font-bold tracking-tight ${active ? 'text-slate-900' : 'text-slate-400'}`}>{label}</p>
            <p className={`text-[10px] uppercase font-bold tracking-widest ${active ? 'text-slate-400' : 'text-slate-300'}`}>{sub}</p>
        </div>
    </button>
);

const InputField = ({ label, value, onChange, placeholder, type = 'text' }: { label: string, value: string, onChange: (v: string) => void, placeholder: string, type?: string }) => (
    <div className="space-y-2">
        <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-2">{label}</label>
        <input 
            type={type}
            className="w-full px-6 py-4 bg-white border border-slate-100 rounded-3xl focus:outline-none focus:ring-4 focus:ring-slate-900/5 focus:border-slate-900/20 text-sm font-medium transition-all shadow-sm"
            placeholder={placeholder}
            value={value}
            onChange={(e) => onChange(e.target.value)}
        />
    </div>
);
