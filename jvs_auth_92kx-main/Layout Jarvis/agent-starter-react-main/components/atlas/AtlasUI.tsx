'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { AtlasClock } from './AtlasClock';
import { Monitor, Shield, Copy, Grid, Power, Info } from 'lucide-react';
import { cn } from '@/lib/shadcn/utils';
import { useTrackVolume, useVoiceAssistant } from '@livekit/components-react';
import { AgentControlBar, type AgentControlBarControls } from '@/components/agents-ui/agent-control-bar';
import { toast } from 'sonner';
import { useBluetooth } from '@/hooks/use-bluetooth';
import { useNetworkDevices } from '@/hooks/use-network-devices';
import { CommandBroker } from '@/lib/atlas/command-broker';
import { SmartHomeSettings } from './SmartHomeSettings';
import { atlasLogger } from '@/lib/atlas/event-logger';
import { AtlasEvent } from '@/lib/atlas/types';

interface AtlasUIProps {
  session?: any;
  isConnected: boolean;
  onDisconnect?: () => void;
  messages?: any[];
  appConfig: any;
}

export const AtlasUI = ({ session, isConnected, onDisconnect, messages, appConfig }: AtlasUIProps) => {
  const { audioTrack } = useVoiceAssistant();
  const volume = useTrackVolume(audioTrack);
  const [isChatOpen, setIsChatOpen] = useState(false);
  
  const { connected, deviceName, services, sendCommand: sendBLECommand } = useBluetooth();
  const { devices: wifiDevices, sendCommand: sendWiFiCommand, scan: scanWiFi } = useNetworkDevices();

  const [lgOnline, setLgOnline] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [atlasEvents, setAtlasEvents] = useState<AtlasEvent[]>([]);
  // OTIMIZADO: leitura de localStorage fora do render (useEffect) — evita bloqueio síncrono
  const [networkConfigured, setNetworkConfigured] = useState(false);

  // Data dinâmica gerada uma única vez na montagem do componente
  const headerDate = React.useMemo(() => {
    const now = new Date();
    const dias = ['DOMINGO', 'SEGUNDA', 'TERÇA', 'QUARTA', 'QUINTA', 'SEXTA', 'SÁBADO'];
    const meses = ['JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL', 'MAIO', 'JUNHO', 'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO'];
    return `${dias[now.getDay()]}, ${now.getDate()} DE ${meses[now.getMonth()]} DE ${now.getFullYear()}`;
  }, []);

  // OTIMIZADO: localStorage lido apenas no mount via useEffect — não bloqueia render
  const refreshSyncStates = () => {
    const savedStatus = localStorage.getItem('atlas_thinq_status');
    setLgOnline(savedStatus === 'ONLINE');
    setNetworkConfigured(!!localStorage.getItem('atlas_network_config'));
  };

  useEffect(() => {
    refreshSyncStates();
  }, []);

  // Monitorar logs do barramento para o fluxo neural
  useEffect(() => {
    const unsub = atlasLogger.subscribe((event) => {
        setAtlasEvents(prev => [event, ...prev].slice(0, 15));
    });
    return () => unsub();
  }, []);

  // Processador Neural Autônomo (Inerpretador de Intenções)
  useEffect(() => {
    if (!messages || messages.length === 0) return;
    const lastMessage = messages[messages.length - 1];
    
    // Só processamos mensagens que vêm do Assistente (vinda do agent)
    if (lastMessage.from === 'agent' && lastMessage.message) {
        const intent = CommandBroker.parseIntent(lastMessage.message);
        if (intent) {
            atlasLogger.log('info', 'broker', `Decodificando comando neural: ${intent.action}`);
            CommandBroker.execute(intent).then(success => {
                if (success) toast.success(`Executado: ${intent.action.replace('_', ' ').toUpperCase()}`);
            });
        }
    }
  }, [messages]);

  const connectedDevices = React.useMemo(() => ({
    bluetooth: connected,
    wifi: wifiDevices.length > 0 || !!localStorage.getItem('atlas_network_config'),
    cloud: lgOnline,
    deviceName: deviceName || undefined
  }), [connected, wifiDevices.length, lgOnline, deviceName]);

  useEffect(() => {
    CommandBroker.setHandlers({
        onBluetoothCommand: sendBLECommand,
        onWiFiCommand: async (ip, endpoint, data) => {
            const savedNet = localStorage.getItem('atlas_network_config');
            const config = savedNet ? JSON.parse(savedNet) : null;
            const targetIp = config?.deviceIp || ip;
            return sendWiFiCommand(targetIp, endpoint, data);
        },
        onCloudCommand: async (p, a, d) => {
            if (p === 'lg_thinq') {
                if (a === 'status_check') {
                    const savedStatus = localStorage.getItem('atlas_thinq_status');
                    const isOnline = savedStatus === 'ONLINE';
                    if (isOnline) setLgOnline(true);
                    return { status: isOnline ? 'online' : 'offline', device: 'LG Dual Inverter' };
                }
                const savedStatus = localStorage.getItem('atlas_thinq_status');
                if (savedStatus !== 'ONLINE') throw new Error('Cloud LG não sincronizado.');
                atlasLogger.log('success', 'cloud', `LG ThinQ: Comando [${a.toUpperCase()}] transmitido.`);
                return { success: true };
            }
        },
        onWiFiScan: async () => { await scanWiFi(); },
        onStatusReport: (report: string) => {
            if (session?.sendChat) session.sendChat(`${report} \n[ACESSO]: ROOT ATIVO.`);
        },
        connectedDevices,
        services 
    });
  }, [connectedDevices, services, sendBLECommand, sendWiFiCommand, scanWiFi, session]);

  const systemMetrics = React.useMemo(() => [
    { label: 'OTIMIZAÇÃO', value: '98.5%', color: 'text-[#D94F00]', hasBar: true, progress: 0.985 },
    { label: 'LATÊNCIA', value: '12ms', color: 'text-[#2B6CB0]', hasBar: true, progress: 0.18, barColor: 'bg-gradient-to-r from-[#2B6CB0] to-[#63B3ED]' },
    { label: 'CAMADA CORE', value: (connected || wifiDevices.length > 0 || lgOnline) ? 'SYNC' : 'BUSCANDO', color: 'text-[#D94F00]', animate: !(connected || wifiDevices.length > 0 || lgOnline) },
    // OTIMIZADO: usa estado 'networkConfigured' em vez de localStorage direto no render
    { label: 'HUB WI-FI', value: wifiDevices.length > 0 ? `${wifiDevices.length} ATIVOS` : (networkConfigured ? 'CONFIGURADO' : 'BUSCANDO'), color: 'text-[#D94F00]', animate: wifiDevices.length === 0 },
    { label: 'SESSÃO', value: isConnected ? 'ONLINE' : 'CONNECTING', color: 'text-[#2E8B57]' },
    { label: 'NÚCLEOS', value: '16 / 16', color: 'text-[#D94F00]' },
    { label: 'MEMÓRIA', value: '87.2 GB', color: 'text-[#2B6CB0]' },
  ], [connected, wifiDevices.length, lgOnline, isConnected, networkConfigured]);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success("Copiado!");
  };

  const controls: AgentControlBarControls = {
    camera: appConfig.supportsVideoInput,
    microphone: true,
    screenShare: appConfig.supportsScreenShare,
    chat: appConfig.supportsChatInput,
    leave: false,
  };

  return (
    <>
      <div className="relative w-full h-full text-[#1A1714] bg-[#F0EDE8] overflow-hidden flex flex-col font-sans select-none grain-overlay">
        <style jsx>{`
          .bg-center-grid::before {
              content: '';
              position: absolute;
              inset: 0;
              background-image: linear-gradient(rgba(217,79,0,0.05) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(217,79,0,0.05) 1px, transparent 1px);
              background-size: 48px 48px;
              mask-image: radial-gradient(ellipse 75% 75% at 50% 50%, black, transparent);
          }
        `}</style>

        <style jsx global>{`
          .animate-spin-slow-ccw { animation: spin 22s linear infinite reverse; }
          .animate-spin-slow-cw { animation: spin 16s linear infinite; }
          @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        `}</style>

        {/* Ambient Warmth Gradients */}
        <div className="absolute inset-0 pointer-events-none z-0">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_55%_55%_at_50%_50%,_rgba(217,79,0,0.05)_0%,_transparent_70%)]" />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_30%_40%_at_85%_15%,_rgba(217,79,0,0.04)_0%,_transparent_60%)]" />
        </div>

        {/* HEADER */}
        <header className="h-16 w-full px-6 flex items-center justify-between border-b border-black/10 z-40 bg-[#F0EDE8]/85 backdrop-blur-md relative">
          <div className="flex items-center gap-4">
            <div className="w-9 h-9 bg-[#D94F00] rounded-[9px] flex items-center justify-center text-white font-mono font-bold text-lg shadow-[0_2px_12px_rgba(217,79,0,0.25)]">Ω</div>
            <h1 className="font-mono font-bold text-[17px] tracking-[0.28em] text-[#1A1714]">ATLAS</h1>
            <div className="px-2 py-0.5 border border-[#D94F00]/35 rounded-full text-[8px] font-mono text-[#D94F00] tracking-[0.12em] bg-[#D94F00]/10 uppercase">
               ACESSO_ROOT
            </div>
          </div>

          <div className="text-[8px] font-mono tracking-[0.22em] text-[#1A1714]/35 absolute left-1/2 -translate-x-1/2 uppercase">
              SESSÃO_RECON_ATIVA
          </div>

          <div className="flex items-center gap-6">
              <div className="flex flex-col items-end">
                  <AtlasClock className="text-[22px] font-mono text-[#1A1714] leading-none" />
                   <span className="text-[7.5px] font-mono text-[#1A1714]/35 tracking-[0.14em] uppercase mt-1">{headerDate}</span>
              </div>
              <div 
                  onClick={() => setIsSettingsOpen(true)}
                  className="w-[30px] h-[30px] border border-black/10 rounded-[7px] bg-white/55 flex items-center justify-center cursor-pointer hover:border-[#D94F00]/35 hover:text-[#D94F00] text-[#1A1714]/35 transition-all shadow-sm hover:shadow-md"
              >
                  <Grid size={13} />
              </div>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#D94F00]/55 to-transparent" />
        </header>

        <main className="flex-1 flex overflow-hidden relative z-10">
          {/* LEFT SIDEBAR */}
          <aside className="w-[210px] border-r border-black/10 p-6 flex flex-col gap-0 bg-[#F0EDE8]/50 overflow-y-auto custom-scrollbar">
              <div className="text-[7.5px] font-mono text-[#1A1714]/35 tracking-[0.22em] uppercase mb-5">SESSÃO_RECON_ATIVA</div>
              
              <div className="bg-white/55 border border-white/80 rounded-[10px] p-3.5 mb-4 shadow-[0_1px_4px_rgba(0,0,0,0.08)]">
                  <div className="text-[7px] font-mono text-[#1A1714]/35 tracking-[0.18em] mb-1 uppercase">ACESSO</div>
                  <div className="text-[11px] font-mono font-bold text-[#D94F00] tracking-[0.08em]">ROOT / OVERRIDE</div>
              </div>


              <div className="flex flex-col">
                  {systemMetrics.map((metric) => (
                      <div key={metric.label} className="py-2.5 border-b border-black/5 flex flex-col">
                          <div className="flex justify-between items-center">
                              <span className="text-[7.5px] font-mono text-[#1A1714]/35 tracking-[0.16em] uppercase">{metric.label}</span>
                              <span className={cn("text-[12px] font-bold tracking-[0.04em]", metric.color, metric.animate && "animate-pulse")}>{metric.value}</span>
                          </div>
                          {metric.hasBar && (
                              <div className="h-[2px] w-full bg-black/5 rounded-full mt-1 overflow-hidden">
                                  <motion.div 
                                      initial={{ width: 0 }}
                                      animate={{ width: `${metric.progress * 100}%` }}
                                      className={cn("h-full", metric.barColor || "bg-gradient-to-r from-[#D94F00] to-[#FF8C4A] shadow-[0_0_6px_rgba(217,79,0,0.25)]")}
                                  />
                              </div>
                          )}
                      </div>
                  ))}
              </div>
          </aside>

          {/* CENTRAL AREA */}
          <div className="flex-1 relative flex items-center justify-center p-8 overflow-hidden bg-center-grid">
              {/* Corner Brackets */}
              <div className="absolute inset-0 m-12 pointer-events-none">
                  <div className="absolute top-0 left-0 w-4.5 h-4.5 border-t-2 border-l-2 border-[#D94F00]" />
                  <div className="absolute top-0 right-0 w-4.5 h-4.5 border-t-2 border-r-2 border-[#D94F00]" />
                  <div className="absolute bottom-0 left-0 w-4.5 h-4.5 border-b-2 border-l-2 border-[#D94F00]" />
                  <div className="absolute bottom-0 right-0 w-4.5 h-4.5 border-b-2 border-r-2 border-[#D94F00]" />
                  
                  {/* Blips */}
                  <div className="absolute top-[14%] right-[7%] w-1.25 h-1.25 bg-[#D94F00] rounded-full shadow-[0_0_8px_#D94F00] animate-pulse" />
                  <div className="absolute bottom-[18%] left-[5%] w-1.25 h-1.25 bg-[#D94F00] rounded-full shadow-[0_0_8px_#D94F00] animate-pulse delay-700" />
              </div>

              <div className="relative w-[440px] h-[440px]">
                  {/* Aura & Rings */}
                  <div className="absolute -inset-[50px] rounded-full bg-[radial-gradient(circle,_rgba(217,79,0,0.1)_0%,_transparent_65%)] animate-aura" />
                  <div className="absolute -inset-[28px] border border-[#D94F00]/20 rounded-full animate-spin-slow-ccw">
                      <div className="absolute top-[-3px] left-1/2 -translate-x-1/2 w-1.25 h-1.25 bg-[#D94F00] rounded-full shadow-[0_0_10px_#D94F00]" />
                  </div>
                  <div className="absolute -inset-[14px] border border-[#D94F00]/10 rounded-full animate-spin-slow-cw" />

                  {/* Main Orb */}
                  <div className="relative w-full h-full rounded-full border border-white/70 bg-[radial-gradient(circle_at_35%_32%,_#F2EDE6_0%,_#E8E2DA_55%,_#DDD7CE_100%)] shadow-[inset_0_2px_0_rgba(255,255,255,0.9),inset_0_-2px_10px_rgba(0,0,0,0.06),0_8px_60px_rgba(0,0,0,0.12),0_0_40px_rgba(217,79,0,0.1)] overflow-hidden">
                      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#D94F00]/5 to-transparent animate-scan" />
                      <img 
                          src="/atlas-jellyfish.png" 
                          alt="Neural Core" 
                          className="absolute inset-0 w-full h-full object-contain p-2 scale-105 brightness-[1.05] contrast-[1.05] saturate-[0.85] drop-shadow-[0_10px_30px_rgba(0,0,0,0.18)] animate-float mix-blend-screen"
                          style={{ objectPosition: 'center 40%' }}
                      />
                      <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_40%_at_35%_28%,_rgba(255,255,255,0.55)_0%,_transparent_60%)] pointer-events-none" />
                  </div>
              </div>
          </div>

          {/* RIGHT SIDEBAR */}
          <aside className="w-[290px] border-l border-black/10 p-6 flex flex-col gap-3.5 bg-[#F0EDE8]/50 overflow-y-auto custom-scrollbar">
              <div className="flex items-center gap-2 mb-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#D94F00] shadow-[0_0_7px_#D94F00] animate-pulse" />
                  <span className="text-[8.5px] font-mono tracking-[0.2em] text-[#D94F00] uppercase">FLUXO_NEURAL</span>
              </div>

              <div className="flex flex-col gap-3.5">
                  <AnimatePresence initial={false}>
                      {/* Combine messages and system events for the neural core feed */}
                      {(() => {
                          // Extrair e formatar mensagens
                          const msgItems = (messages || []).filter(m => m.message).map((m, i) => ({ 
                              type: 'msg', 
                              content: m.message, 
                              id: m.id || `msg-${i}`,
                              time: (m.timestamp && !isNaN(new Date(m.timestamp).getTime())) ? new Date(m.timestamp).getTime() : Date.now() - ((messages?.length || 0) - i) * 1000
                          }));
                          
                          // OTIMIZADO: usa timestamp real do evento em vez de Date.now() no render
                          const eventItems = atlasEvents.map((e, idx) => ({ 
                              type: 'event', 
                              content: e.message, 
                              level: e.level, 
                              id: `event-${e.source}-${e.message.slice(0, 12).replace(/\s+/g, '_')}-${idx}`,
                              time: e.timestamp instanceof Date ? e.timestamp.getTime() : Date.now() - (idx * 500)
                          }));

                          // Unificar e filtrar: Ocultar logs que não sejam explicitamente sucessos ou avisos relevantes
                          const combined = [...msgItems, ...eventItems]
                              .filter(item => {
                                  if (item.type === 'msg') return true;
                                  // Mostrar apenas sucessos de comandos (cloud/wifi) ou erros reais, ocultar 'info' do broker
                                  return (item as any).level === 'success' || (item as any).level === 'error';
                              })
                              .sort((a, b) => (b.time as number) - (a.time as number))
                              .slice(0, 7);

                          return combined.map((item, idx) => (
                          <motion.div 
                              key={item.id}
                              initial={{ opacity: 0, x: 20 }}
                              animate={{ opacity: 1, x: 0 }}
                              className={cn(
                                  "bg-white/55 border border-white/80 rounded-xl p-4 shadow-[0_1px_6px_rgba(0,0,0,0.08)] relative overflow-hidden group transition-all",
                                  item.type === 'event' && "border-l-4 border-l-[#D94F00]/40 bg-[#D94F00]/5"
                              )}
                          >
                              <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/90 to-transparent" />
                              <div className="text-[7.5px] font-mono text-[#1A1714]/35 tracking-[0.15em] mb-2.5 uppercase">
                                  {item.type === 'msg' ? `DADO_NEURAL_0${idx + 1}` : `LOG_SISTEMA_0${idx + 1}`}
                              </div>
                              <p className={cn(
                                  "text-[12.5px] leading-[1.75] font-normal",
                                  item.type === 'msg' ? "text-[#1A1714]/55" : "text-[#D94F00] font-mono text-[10px]"
                              )}>
                                  {item.type === 'msg' ? `"${item.content}"` : item.content}
                              </p>
                              {item.type === 'msg' && (
                                  <button onClick={() => copyToClipboard(item.content as string)} className="absolute top-[11px] right-[11px] w-5.5 h-5.5 border border-black/10 bg-white/60 text-[#1A1714]/35 rounded-[6px] flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all hover:border-[#D94F00]/35 hover:text-[#D94F00]">
                                      <Copy size={11} />
                                  </button>
                              )}
                          </motion.div>
                      ))})()}
                  </AnimatePresence>
              </div>
          </aside>
        </main>

        {/* FOOTER */}
        <footer className="h-[84px] w-full border-t border-black/10 flex items-center justify-center z-40 bg-[#F0EDE8]/88 backdrop-blur-md relative">
            <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#D94F00]/55 to-transparent" />
            
            <div className="flex items-center gap-1.5 p-2 px-3.5 bg-white/60 border border-[#D94F00]/18 rounded-full shadow-[0_2px_20px_rgba(0,0,0,0.07),inset_0_1px_0_rgba(255,255,255,0.9)]">
                <AgentControlBar
                  variant="livekit"
                  controls={controls}
                  isChatOpen={isChatOpen}
                  isConnected={isConnected}
                  onDisconnect={onDisconnect}
                  onIsChatOpenChange={setIsChatOpen}
                  className="bg-transparent border-none p-0 gap-1.5 [&_button]:bg-white/55 [&_button]:border-black/8 [&_button]:text-[#1A1714]/55 [&_button]:w-[38px] [&_button]:h-[38px] [&_button:hover]:bg-[#D94F00]/10 [&_button:hover]:border-[#D94F00]/35 [&_button:hover]:text-[#D94F00] [&_button:hover]:shadow-[0_0_12_#D94F00/25]"
                />
                <div className="w-px h-[22px] bg-black/8 mx-1" />
                <button
                  onClick={onDisconnect}
                  disabled={!isConnected}
                  className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-br from-[#D94F00] to-[#C23A00] text-white rounded-full font-mono font-bold text-[9.5px] tracking-[0.16em] uppercase shadow-[0_3px_18px_rgba(217,79,0,0.35),inset_0_1px_0_rgba(255,255,255,0.15)] hover:shadow-[0_4px_28px_rgba(217,79,0,0.55)] hover:-translate-y-px transition-all"
                >
                    <Power size={12} />
                    <span>ENCERRAR CHAMADA</span>
                </button>
            </div>

            <div className="absolute bottom-6 left-6 w-[34px] h-[34px] rounded-full bg-gradient-to-br from-[#d8d2c8] to-[#c8c2b8] border border-black/10 flex items-center justify-center font-mono font-bold text-xs text-[#1A1714]/55 shadow-[0_2px_8px_rgba(0,0,0,0.08)]">N</div>
        </footer>
      </div>

      <AnimatePresence>
        {isSettingsOpen && (
          <SmartHomeSettings 
            isOpen={isSettingsOpen} 
            onClose={() => {
              setIsSettingsOpen(false);
              refreshSyncStates();
            }} 
            deviceName={deviceName || null}
            discoveredServices={services}
          />
        )}
      </AnimatePresence>
    </>
  );
};
