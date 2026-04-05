'use client';

import React, { useState, useEffect } from 'react';

interface AtlasClockProps {
    className?: string;
}

export const AtlasClock = ({ className }: AtlasClockProps) => {
    const [time, setTime] = useState(new Date());

    useEffect(() => {
        const timer = setInterval(() => setTime(new Date()), 1000);
        return () => clearInterval(timer);
    }, []);

    const formatTime = (date: Date) => {
        const h = date.getHours().toString().padStart(2, '0');
        const m = date.getMinutes().toString().padStart(2, '0');
        const s = date.getSeconds().toString().padStart(2, '0');
        return `${h}:${m}:${s}`;
    };

    const formatDate = (date: Date) => {
        const options: Intl.DateTimeFormatOptions = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        return date.toLocaleDateString('pt-BR', options);
    };

    return (
        <div className={className}>
            {formatTime(time)}
        </div>
    );
};
