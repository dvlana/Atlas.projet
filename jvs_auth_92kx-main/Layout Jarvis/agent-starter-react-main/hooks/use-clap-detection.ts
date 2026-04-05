'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { toast } from 'sonner';
import { atlasLogger } from '@/lib/atlas/event-logger';

interface UseClapDetectionProps {
  onDoubleClap?: () => void;
  onTripleClap?: () => void;
  threshold?: number;
  debounceMs?: number;
}

export const useClapDetection = ({
  onDoubleClap,
  onTripleClap,
  threshold = 0.3,
  debounceMs = 250,
}: UseClapDetectionProps = {}) => {
  const [isActive, setIsActive] = useState(false);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const dataArrayRef = useRef<Float32Array<ArrayBuffer> | null>(null);
  const lastClapTimeRef = useRef<number>(0);
  const clapCountRef = useRef<number>(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const startListening = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const context = new AudioContext();
      const source = context.createMediaStreamSource(stream);
      const analyser = context.createAnalyser();
      
      analyser.fftSize = 512;
      source.connect(analyser);
      
      audioContextRef.current = context;
      analyserRef.current = analyser;
      dataArrayRef.current = new Float32Array(analyser.frequencyBinCount);
      
      setIsActive(true);
      atlasLogger.log('info', 'hardware', 'Sistema de detecção de som ativo (Clap Detector)');
      
      processAudio();
    } catch (err) {
      console.error('Erro ao acessar microfone para detecção de palmas:', err);
      toast.error('Erro ao acessar microfone para detecção de palmas.');
    }
  }, []);

  const stopListening = useCallback(() => {
    if (audioContextRef.current) {
        audioContextRef.current.close();
    }
    setIsActive(false);
    if (timerRef.current) clearTimeout(timerRef.current);
    atlasLogger.log('info', 'hardware', 'Detecção de palmas desativada.');
  }, []);

  const processAudio = useCallback(() => {
    if (!analyserRef.current || !dataArrayRef.current || !isActive) return;

    analyserRef.current.getFloatTimeDomainData(dataArrayRef.current);
    
    // Cálculo de Pico (Volume Máximo no Frame)
    let peak = 0;
    for (let i = 0; i < dataArrayRef.current.length; i++) {
        const val = Math.abs(dataArrayRef.current[i]);
        if (val > peak) peak = val;
    }

    const now = Date.now();

    if (peak > threshold) {
        // Debounce para evitar registrar múltiplos picos de uma mesma palma
        if (now - lastClapTimeRef.current > debounceMs) {
            lastClapTimeRef.current = now;
            clapCountRef.current += 1;
            
            // console.log(`Clap detected! Count: ${clapCountRef.current}`);

            // Resetar timer de reconhecimento de padrão
            if (timerRef.current) clearTimeout(timerRef.current);
            
            timerRef.current = setTimeout(() => {
                evaluatePattern(clapCountRef.current);
                clapCountRef.current = 0;
            }, 800); // Janela para completar a sequência
        }
    }

    if (isActive) {
        requestAnimationFrame(processAudio);
    }
  }, [isActive, threshold, debounceMs]);

  const evaluatePattern = (count: number) => {
    if (count === 2) {
        atlasLogger.log('success', 'hardware', 'Padrão detectado: Dupla Palma (Ação Neural Ativada)');
        toast.info('Padrão Detectado: 2 Palmas');
        if (onDoubleClap) onDoubleClap();
    } else if (count === 3) {
        atlasLogger.log('success', 'hardware', 'Padrão detectado: Tripla Palma (Modo Especial)');
        toast.info('Padrão Detectado: 3 Palmas');
        if (onTripleClap) onTripleClap();
    }
  };

  useEffect(() => {
    return () => {
        if (audioContextRef.current) audioContextRef.current.close();
        if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  return {
    isActive,
    startListening,
    stopListening
  };
};
