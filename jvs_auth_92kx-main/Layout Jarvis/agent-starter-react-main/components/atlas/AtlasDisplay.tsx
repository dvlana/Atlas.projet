'use client';

import React, { Suspense, useRef, useMemo } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Float, MeshWobbleMaterial, MeshDistortMaterial, Sphere, ContactShadows } from '@react-three/drei';
import * as THREE from 'three';
import { useTrackVolume, useVoiceAssistant } from '@livekit/components-react';

const SceneManager = ({ children }: { children: React.ReactNode }) => {
  const { camera, mouse } = useThree();
  useFrame(() => {
    camera.position.x += (mouse.x * 1.5 - camera.position.x) * 0.05;
    camera.position.y += (mouse.y * 1.5 - camera.position.y) * 0.05;
    camera.lookAt(0, 0, 0);
  });
  return <>{children}</>;
};

const NeuralCore = ({ volume }: { volume: number }) => {
  const coreRef = useRef<THREE.Mesh>(null);
  const fluidRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    if (coreRef.current) {
      coreRef.current.rotation.y = time * 0.2;
      coreRef.current.rotation.z = time * 0.1;
      // Reagir ao volume
      const pulse = 1 + volume * 0.2;
      coreRef.current.scale.setScalar(pulse);
    }
    if (fluidRef.current) {
        fluidRef.current.rotation.x = -time * 0.15;
    }
  });

  return (
    <group>
      {/* Luzes Internas para Bioluminescência - Tons de Laranja e Fogo */}
      <pointLight position={[0, 0, 0]} color="#f97316" intensity={20} distance={5} />
      <pointLight position={[0.5, 0.5, 0.5]} color="#ea580c" intensity={15} distance={4} />

      {/* Camada Externa: Gelatina Translúcida com Tintura Laranja Suave */}
      <mesh ref={coreRef}>
        <Sphere args={[1.5, 128, 128]}>
          <MeshDistortMaterial
            color="#fff7ed"
            speed={2}
            distort={0.4 + volume * 0.5}
            radius={1}
            transmission={0.95}
            thickness={1.5}
            roughness={0.02}
            metalness={0.1}
            ior={1.2}
            clearcoat={1}
            clearcoatRoughness={0.1}
          />
        </Sphere>
      </mesh>

      {/* Núcleo Interno: Fluido Laranja Vibrante */}
      <mesh ref={fluidRef} scale={0.75}>
        <Sphere args={[1, 64, 64]}>
          <MeshWobbleMaterial
            color="#ea580c"
            speed={3}
            factor={0.5}
            roughness={0.1}
            emissive="#f97316"
            emissiveIntensity={1.5}
          />
        </Sphere>
      </mesh>

      {/* Bolhas Bioluminescentes */}
      <Bubbles count={15} volume={volume} />
    </group>
  );
};

const Bubbles = ({ count, volume }: { count: number, volume: number }) => {
    const bubbles = useMemo(() => {
        return Array.from({ length: count }).map(() => ({
            position: [
                (Math.random() - 0.5) * 1.5,
                (Math.random() - 0.5) * 1.5,
                (Math.random() - 0.5) * 1.5
            ] as [number, number, number],
            size: 0.05 + Math.random() * 0.1,
            color: Math.random() > 0.5 ? '#f97316' : '#ef4444', // Laranja ou Vermelho
            speed: 0.5 + Math.random() * 1
        }));
    }, [count]);

    return (
        <group>
            {bubbles.map((b, i) => (
                <Bubble key={i} {...b} volume={volume} />
            ))}
        </group>
    );
};

const Bubble = ({ position, size, color, speed, volume }: any) => {
    const ref = useRef<THREE.Mesh>(null);
    useFrame((state) => {
        if (ref.current) {
            const t = state.clock.getElapsedTime() * speed;
            ref.current.position.y += Math.sin(t) * 0.005;
            ref.current.position.x += Math.cos(t) * 0.005;
            const s = size * (1 + volume * 2);
            ref.current.scale.setScalar(s);
        }
    });

    return (
        <mesh position={position} ref={ref}>
            <Sphere args={[1, 16, 16]}>
                <meshStandardMaterial 
                    color={color} 
                    emissive={color} 
                    emissiveIntensity={4} 
                    transparent 
                    opacity={0.8} 
                />
            </Sphere>
        </mesh>
    );
};


export const AtlasDisplay = ({ theme = 'light' }: { mode?: string, theme?: string }) => {
  const { audioTrack } = useVoiceAssistant();
  const volume = useTrackVolume(audioTrack);

  return (
    <div className="w-full h-full relative">
      <Canvas camera={{ position: [0, 0, 6], fov: 45 }} dpr={[1, 2]}>
        {/* Iluminação Dramática */}
        <ambientLight intensity={0.5} />
        <spotLight position={[5, 10, 10]} angle={0.15} penumbra={1} intensity={150} color="#ffffff" castShadow />
        <spotLight position={[-10, -10, -10]} angle={0.15} penumbra={1} intensity={50} color="#dcfce7" /> {/* Verde Pálido */}
        <pointLight position={[10, 10, 10]} intensity={20} color="#ffffff" />
        
        <SceneManager>
            <Suspense fallback={null}>
                <NeuralCore volume={volume} />
                <ContactShadows position={[0, -3.5, 0]} opacity={0.15} scale={12} blur={2.5} far={4} />
            </Suspense>
        </SceneManager>
      </Canvas>
    </div>
  );
};
