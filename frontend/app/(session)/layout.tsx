'use client';

import { LiveKitProvider } from '@/hooks/useLiveKit';
import React from 'react';

export default function SessionLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <LiveKitProvider>{children}</LiveKitProvider>;
}
