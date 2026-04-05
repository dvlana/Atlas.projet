import React, { useEffect, useRef, useState } from 'react';
import {
  useSessionContext,
  useSessionMessages,
} from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { AtlasUI } from '@/components/atlas/AtlasUI';

interface SessionViewProps {
  appConfig: AppConfig;
  onManualDisconnect?: () => void;
}

export const SessionView = ({
  appConfig,
  onManualDisconnect,
  ...props
}: React.ComponentProps<'section'> & SessionViewProps) => {
  const session = useSessionContext();
  const { messages } = useSessionMessages(session);

  const handleDisconnect = () => {
    if (onManualDisconnect) onManualDisconnect();
    try {
      if (session.end) session.end();
    } catch (e) {
      console.warn("Erro ao desconectar sessão:", e);
    }
  };

  return (
    <section
      className="relative flex h-svh w-svw flex-col bg-black overflow-hidden"
      {...props}
    >
      <AtlasUI 
        session={session}
        isConnected={session.isConnected} 
        onDisconnect={handleDisconnect} 
        messages={messages}
        appConfig={appConfig}
      />
    </section>
  );
};
