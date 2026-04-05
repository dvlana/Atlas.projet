import { AtlasEvent } from './types';

// Limite máximo de logs mantidos na memória — previne memory leak em sessões longas
const MAX_LOGS = 100;

class EventLogger {
  private static instance: EventLogger;
  private logs: AtlasEvent[] = [];
  private listeners: ((event: AtlasEvent) => void)[] = [];

  private constructor() {}

  public static getInstance(): EventLogger {
    if (!EventLogger.instance) {
      EventLogger.instance = new EventLogger();
    }
    return EventLogger.instance;
  }

  public log(level: AtlasEvent['level'], source: AtlasEvent['source'], message: string, data?: any) {
    const event: AtlasEvent = {
        timestamp: new Date(),
        level,
        source,
        message,
        data
    };
    
    // OTIMIZADO: Mantém no máximo MAX_LOGS entradas — previne crescimento infinito de RAM
    this.logs.push(event);
    if (this.logs.length > MAX_LOGS) {
        this.logs.shift(); // Remove o mais antigo
    }

    // OTIMIZADO: console.debug em vez de console.log — silencioso em produção
    // Só aparece quando o devtools está com "Verbose" habilitado
    if (level === 'error') {
        console.error(`[ATLAS][${source.toUpperCase()}] ${message}`, data || '');
    } else {
        console.debug(`[ATLAS][${source.toUpperCase()}][${level.toUpperCase()}] ${message}`, data || '');
    }
    
    this.listeners.forEach(fn => fn(event));
  }

  public subscribe(fn: (event: AtlasEvent) => void) {
    this.listeners.push(fn);
    return () => {
        this.listeners = this.listeners.filter(l => l !== fn);
    };
  }

  public getHistory() {
    return [...this.logs];
  }

  // Limpa histórico manualmente (ex: ao desconectar sessão)
  public clearHistory() {
    this.logs = [];
  }
}

export const atlasLogger = EventLogger.getInstance();
