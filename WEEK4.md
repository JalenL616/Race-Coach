# Week 4: Frontend + Polish

**Goal:** Build a polished React frontend with streaming AI responses, PDF export, shareable links, and deploy to Vercel. Create demo video and documentation for your portfolio.

**Time Budget:** ~30 hours
- Learning: 4-6 hours
- Building: 24-26 hours

---

## Prerequisites

Before starting, ensure you have:
- Week 3 complete with deployed Railway backend
- Vercel account from https://vercel.com
- Node.js 18+ installed
- Your Railway backend URL (e.g., `https://race-coach-api.railway.app`)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Vercel (Frontend)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Next.js App                                                     │
│  ├── / (Landing)                                                 │
│  ├── /dashboard (Main app after login)                          │
│  ├── /strategy/[id] (View/share strategy)                       │
│  └── /api/... (Next.js API routes for OAuth callback)           │
│                                                                  │
│  Components:                                                     │
│  ├── ElevationChart (2D Recharts visualization)                 │
│  ├── StrategyDisplay (Markdown rendering + streaming)           │
│  ├── GPXUploader (Drag & drop file upload)                      │
│  └── PDFExport (Generate downloadable PDF)                      │
│                                                                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Railway (Backend API)                         │
│                    (from Week 3)                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Day 1: Next.js Setup + Basic Layout

### Learning (1 hr)

**Next.js App Router (Quick Refresher)**
- Read: [Next.js - App Router](https://nextjs.org/docs/app) (skim if you know React)
- Key differences from Pages Router: Server components by default, `app/` directory, layouts
- Since you know React, focus on: `"use client"` directive, Server Actions

### Building (5 hrs)

**Task 1: Create Next.js Project**

```bash
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir
cd frontend
```

**Task 2: Install Dependencies**

```bash
npm install recharts react-markdown @react-pdf/renderer lucide-react
npm install -D @types/react-markdown
```

**Task 3: Project Structure**

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx              # Landing page
│   │   ├── dashboard/
│   │   │   └── page.tsx          # Main app
│   │   ├── strategy/
│   │   │   └── [id]/
│   │   │       └── page.tsx      # View strategy
│   │   └── api/
│   │       └── auth/
│   │           └── callback/
│   │               └── route.ts   # OAuth callback
│   ├── components/
│   │   ├── ui/                   # Basic UI components
│   │   ├── ElevationChart.tsx
│   │   ├── StrategyDisplay.tsx
│   │   ├── GPXUploader.tsx
│   │   ├── RaceForm.tsx
│   │   └── PDFExport.tsx
│   ├── lib/
│   │   ├── api.ts               # Backend API client
│   │   └── utils.ts
│   └── types/
│       └── index.ts             # TypeScript types
├── .env.local
└── next.config.js
```

**Task 4: Environment Variables**

Create `.env.local`:
```
NEXT_PUBLIC_API_URL=https://your-app.railway.app
NEXT_PUBLIC_STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
```

**Task 5: Create API Client**

Create `src/lib/api.ts`:
```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL;

export interface CourseAnalysis {
  total_distance_miles: number;
  total_elevation_gain_ft: number;
  total_elevation_loss_ft: number;
  elevation_profile: Array<{
    mile: number;
    elevation_ft: number;
    grade_percent: number;
  }>;
  difficulty_rating: string;
  key_segments: Array<{
    mile: number;
    type: string;
    grade: number;
    advice: string;
  }>;
}

export interface Strategy {
  id: string;
  race_name: string;
  generated_at: string;
  pacing_strategy: string;
  nutrition_plan: string;
  mental_preparation: string;
  course_analysis?: CourseAnalysis;
  predicted_finish_time: number;
}

export interface RaceInfo {
  name: string;
  distance_miles: number;
  date: string;
  location: string;
}

class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_URL || 'http://localhost:8000';
  }

  async getStravaAuthUrl(): Promise<string> {
    const res = await fetch(`${this.baseUrl}/auth/strava/url`);
    const data = await res.json();
    return data.auth_url;
  }

  async exchangeStravaCode(code: string): Promise<{
    access_token: string;
    refresh_token: string;
    athlete_id: number;
  }> {
    const res = await fetch(`${this.baseUrl}/auth/strava/callback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code }),
    });

    if (!res.ok) throw new Error('Failed to exchange code');
    return res.json();
  }

  async analyzeGPX(file: File): Promise<CourseAnalysis> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${this.baseUrl}/course/analyze-gpx`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) throw new Error('Failed to analyze GPX');
    return res.json();
  }

  async analyzeImage(file: File): Promise<{
    extracted_info: Record<string, unknown>;
    confidence: number;
    raw_description: string;
  }> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${this.baseUrl}/course/analyze-image-upload`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) throw new Error('Failed to analyze image');
    return res.json();
  }

  async generateStrategy(
    raceInfo: RaceInfo,
    accessToken: string
  ): Promise<Strategy> {
    const res = await fetch(`${this.baseUrl}/strategy/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        race_info: raceInfo,
        access_token: accessToken,
      }),
    });

    if (!res.ok) throw new Error('Failed to generate strategy');
    return res.json();
  }

  // Streaming version for real-time updates
  async generateStrategyStream(
    raceInfo: RaceInfo,
    accessToken: string,
    onChunk: (chunk: string, section: string) => void
  ): Promise<Strategy> {
    const res = await fetch(`${this.baseUrl}/strategy/generate-stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        race_info: raceInfo,
        access_token: accessToken,
      }),
    });

    if (!res.ok) throw new Error('Failed to generate strategy');

    const reader = res.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) throw new Error('No response body');

    let fullStrategy: Strategy | null = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n').filter(Boolean);

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));

          if (data.type === 'chunk') {
            onChunk(data.content, data.section);
          } else if (data.type === 'complete') {
            fullStrategy = data.strategy;
          }
        }
      }
    }

    if (!fullStrategy) throw new Error('No strategy received');
    return fullStrategy;
  }

  async getStrategy(id: string): Promise<Strategy> {
    const res = await fetch(`${this.baseUrl}/strategy/${id}`);
    if (!res.ok) throw new Error('Strategy not found');
    return res.json();
  }
}

export const api = new ApiClient();
```

**Task 6: Create Basic Layout**

Update `src/app/layout.tsx`:
```tsx
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Race Coach | AI-Powered Race Strategy',
  description: 'Get personalized race strategies powered by AI and your training data',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-gray-50">
          {children}
        </div>
      </body>
    </html>
  );
}
```

**Task 7: Create Landing Page**

Update `src/app/page.tsx`:
```tsx
import Link from 'next/link';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="max-w-2xl text-center">
        <h1 className="text-5xl font-bold text-gray-900 mb-6">
          Race Coach
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          AI-powered race strategies based on your training data, course analysis, and expert running knowledge.
        </p>

        <div className="space-y-4">
          <Link
            href="/dashboard"
            className="inline-block px-8 py-4 bg-orange-500 text-white font-semibold rounded-lg hover:bg-orange-600 transition"
          >
            Get Started
          </Link>

          <div className="text-sm text-gray-500">
            Connect your Strava account to begin
          </div>
        </div>

        <div className="mt-16 grid grid-cols-3 gap-8 text-left">
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Pacing Strategy</h3>
            <p className="text-sm text-gray-600">
              Mile-by-mile splits based on your fitness and the course profile
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Nutrition Plan</h3>
            <p className="text-sm text-gray-600">
              Personalized fueling schedule for race day
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Mental Prep</h3>
            <p className="text-sm text-gray-600">
              Mantras and strategies for when it gets tough
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
```

**Expected output:** Basic Next.js app running with landing page and API client ready.

---

## Day 2: Strava OAuth + Dashboard Shell

### Building (5 hrs)

**Task 1: OAuth Callback Route**

Create `src/app/api/auth/callback/route.ts`:
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { api } from '@/lib/api';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const code = searchParams.get('code');
  const error = searchParams.get('error');

  if (error) {
    return NextResponse.redirect(
      new URL(`/dashboard?error=${error}`, request.url)
    );
  }

  if (!code) {
    return NextResponse.redirect(
      new URL('/dashboard?error=no_code', request.url)
    );
  }

  try {
    const tokens = await api.exchangeStravaCode(code);

    // Store tokens in cookies (httpOnly for security)
    const response = NextResponse.redirect(
      new URL('/dashboard', request.url)
    );

    response.cookies.set('strava_access_token', tokens.access_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 60 * 6, // 6 hours
    });

    response.cookies.set('strava_refresh_token', tokens.refresh_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 30, // 30 days
    });

    response.cookies.set('strava_athlete_id', String(tokens.athlete_id), {
      httpOnly: false, // Allow client access
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 30,
    });

    return response;
  } catch (error) {
    console.error('OAuth error:', error);
    return NextResponse.redirect(
      new URL('/dashboard?error=oauth_failed', request.url)
    );
  }
}
```

**Task 2: Auth Context**

Create `src/lib/auth.tsx`:
```tsx
'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { api } from './api';

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  athleteId: string | null;
  login: () => Promise<void>;
  logout: () => void;
  getAccessToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [athleteId, setAthleteId] = useState<string | null>(null);

  useEffect(() => {
    // Check if user has athlete_id cookie
    const cookies = document.cookie.split(';');
    const athleteCookie = cookies.find(c => c.trim().startsWith('strava_athlete_id='));

    if (athleteCookie) {
      const id = athleteCookie.split('=')[1];
      setAthleteId(id);
      setIsAuthenticated(true);
    }
    setIsLoading(false);
  }, []);

  const login = async () => {
    const authUrl = await api.getStravaAuthUrl();
    window.location.href = authUrl;
  };

  const logout = () => {
    // Clear cookies
    document.cookie = 'strava_access_token=; Max-Age=0; path=/';
    document.cookie = 'strava_refresh_token=; Max-Age=0; path=/';
    document.cookie = 'strava_athlete_id=; Max-Age=0; path=/';
    setIsAuthenticated(false);
    setAthleteId(null);
  };

  const getAccessToken = async (): Promise<string | null> => {
    // In production, call your backend to get/refresh token
    // For now, return from API route
    const res = await fetch('/api/auth/token');
    if (res.ok) {
      const data = await res.json();
      return data.access_token;
    }
    return null;
  };

  return (
    <AuthContext.Provider value={{
      isAuthenticated,
      isLoading,
      athleteId,
      login,
      logout,
      getAccessToken,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
```

**Task 3: Token API Route**

Create `src/app/api/auth/token/route.ts`:
```typescript
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const accessToken = request.cookies.get('strava_access_token')?.value;

  if (!accessToken) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
  }

  return NextResponse.json({ access_token: accessToken });
}
```

**Task 4: Dashboard Page**

Create `src/app/dashboard/page.tsx`:
```tsx
'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/auth';
import { api, Strategy, CourseAnalysis, RaceInfo } from '@/lib/api';
import GPXUploader from '@/components/GPXUploader';
import RaceForm from '@/components/RaceForm';
import ElevationChart from '@/components/ElevationChart';
import StrategyDisplay from '@/components/StrategyDisplay';
import { Loader2, LogOut } from 'lucide-react';

type Step = 'connect' | 'upload' | 'details' | 'generating' | 'result';

export default function Dashboard() {
  const { isAuthenticated, isLoading, login, logout, getAccessToken } = useAuth();

  const [step, setStep] = useState<Step>('connect');
  const [courseAnalysis, setCourseAnalysis] = useState<CourseAnalysis | null>(null);
  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [streamingContent, setStreamingContent] = useState<{
    pacing: string;
    nutrition: string;
    mental: string;
  }>({ pacing: '', nutrition: '', mental: '' });
  const [currentSection, setCurrentSection] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  // Update step based on auth status
  if (!isLoading && isAuthenticated && step === 'connect') {
    setStep('upload');
  }

  const handleGPXUpload = async (file: File) => {
    try {
      setError(null);
      const analysis = await api.analyzeGPX(file);
      setCourseAnalysis(analysis);
      setStep('details');
    } catch (err) {
      setError('Failed to analyze GPX file');
    }
  };

  const handleGenerateStrategy = async (raceInfo: RaceInfo) => {
    try {
      setError(null);
      setStep('generating');
      setStreamingContent({ pacing: '', nutrition: '', mental: '' });

      const accessToken = await getAccessToken();
      if (!accessToken) {
        throw new Error('Not authenticated');
      }

      // Use streaming if available, fallback to regular
      try {
        const result = await api.generateStrategyStream(
          raceInfo,
          accessToken,
          (chunk, section) => {
            setCurrentSection(section);
            setStreamingContent(prev => ({
              ...prev,
              [section]: prev[section as keyof typeof prev] + chunk,
            }));
          }
        );
        setStrategy(result);
      } catch {
        // Fallback to non-streaming
        const result = await api.generateStrategy(raceInfo, accessToken);
        setStrategy(result);
      }

      setStep('result');
    } catch (err) {
      setError('Failed to generate strategy');
      setStep('details');
    }
  };

  const handleStartOver = () => {
    setCourseAnalysis(null);
    setStrategy(null);
    setStreamingContent({ pacing: '', nutrition: '', mental: '' });
    setStep('upload');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-orange-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-5xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-xl font-bold text-gray-900">Race Coach</h1>
          {isAuthenticated && (
            <button
              onClick={logout}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          )}
        </div>
      </header>

      {/* Progress Steps */}
      <div className="bg-white border-b">
        <div className="max-w-5xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            {['Connect Strava', 'Upload Course', 'Race Details', 'Strategy'].map((label, i) => {
              const stepIndex = ['connect', 'upload', 'details', 'result'].indexOf(step);
              const isActive = i <= stepIndex || (step === 'generating' && i <= 3);
              return (
                <div key={label} className="flex items-center gap-2">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    isActive ? 'bg-orange-500 text-white' : 'bg-gray-200 text-gray-500'
                  }`}>
                    {i + 1}
                  </div>
                  <span className={isActive ? 'text-gray-900' : 'text-gray-400'}>
                    {label}
                  </span>
                  {i < 3 && <div className="w-8 h-px bg-gray-300" />}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {/* Step: Connect */}
        {step === 'connect' && (
          <div className="text-center py-16">
            <h2 className="text-2xl font-bold mb-4">Connect Your Strava Account</h2>
            <p className="text-gray-600 mb-8">
              We'll analyze your training data to create a personalized race strategy.
            </p>
            <button
              onClick={login}
              className="px-8 py-4 bg-orange-500 text-white font-semibold rounded-lg hover:bg-orange-600"
            >
              Connect with Strava
            </button>
          </div>
        )}

        {/* Step: Upload */}
        {step === 'upload' && (
          <div>
            <h2 className="text-2xl font-bold mb-4">Upload Course Data</h2>
            <p className="text-gray-600 mb-8">
              Upload a GPX file of your race course for elevation analysis.
            </p>
            <GPXUploader onUpload={handleGPXUpload} />
            <button
              onClick={() => setStep('details')}
              className="mt-4 text-gray-500 hover:text-gray-700"
            >
              Skip (no GPX file)
            </button>
          </div>
        )}

        {/* Step: Details */}
        {step === 'details' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div>
              <h2 className="text-2xl font-bold mb-4">Race Details</h2>
              <RaceForm
                onSubmit={handleGenerateStrategy}
                defaultDistance={courseAnalysis?.total_distance_miles}
              />
            </div>

            {courseAnalysis && (
              <div>
                <h3 className="text-lg font-semibold mb-4">Course Analysis</h3>
                <ElevationChart data={courseAnalysis.elevation_profile} />
                <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Distance:</span>{' '}
                    {courseAnalysis.total_distance_miles.toFixed(1)} mi
                  </div>
                  <div>
                    <span className="text-gray-500">Elevation Gain:</span>{' '}
                    {courseAnalysis.total_elevation_gain_ft} ft
                  </div>
                  <div>
                    <span className="text-gray-500">Difficulty:</span>{' '}
                    <span className="capitalize">{courseAnalysis.difficulty_rating}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step: Generating */}
        {step === 'generating' && (
          <div>
            <div className="flex items-center gap-3 mb-8">
              <Loader2 className="w-6 h-6 animate-spin text-orange-500" />
              <h2 className="text-2xl font-bold">Generating Your Strategy...</h2>
            </div>

            <div className="space-y-6">
              {['pacing', 'nutrition', 'mental'].map((section) => (
                <div key={section} className="bg-white rounded-lg border p-6">
                  <h3 className="font-semibold capitalize mb-3 flex items-center gap-2">
                    {section === 'pacing' && 'Pacing Strategy'}
                    {section === 'nutrition' && 'Nutrition Plan'}
                    {section === 'mental' && 'Mental Preparation'}
                    {currentSection === section && (
                      <Loader2 className="w-4 h-4 animate-spin text-orange-500" />
                    )}
                  </h3>
                  <div className="prose prose-sm max-w-none">
                    {streamingContent[section as keyof typeof streamingContent] || (
                      <span className="text-gray-400">Waiting...</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step: Result */}
        {step === 'result' && strategy && (
          <div>
            <div className="flex justify-between items-center mb-8">
              <h2 className="text-2xl font-bold">Your Race Strategy</h2>
              <div className="flex gap-4">
                <button
                  onClick={handleStartOver}
                  className="px-4 py-2 text-gray-600 hover:text-gray-900"
                >
                  Start Over
                </button>
              </div>
            </div>

            <StrategyDisplay strategy={strategy} courseAnalysis={courseAnalysis} />
          </div>
        )}
      </main>
    </div>
  );
}
```

**Expected output:** Dashboard with OAuth flow and step-by-step UI.

---

## Day 3: Components - GPX Upload + Elevation Chart

### Learning (1 hr)

**Recharts Basics**
- Read: [Recharts - Getting Started](https://recharts.org/en-US/guide)
- Focus on: AreaChart, LineChart, responsive containers
- Key concept: Recharts uses React components, data is just arrays of objects

### Building (4 hrs)

**Task 1: GPX Uploader Component**

Create `src/components/GPXUploader.tsx`:
```tsx
'use client';

import { useState, useCallback } from 'react';
import { Upload, FileText, X, Loader2 } from 'lucide-react';

interface GPXUploaderProps {
  onUpload: (file: File) => Promise<void>;
}

export default function GPXUploader({ onUpload }: GPXUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true);
    } else if (e.type === 'dragleave') {
      setIsDragging(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.name.endsWith('.gpx')) {
      setFile(droppedFile);
      setError(null);
    } else {
      setError('Please upload a .gpx file');
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && selectedFile.name.endsWith('.gpx')) {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Please upload a .gpx file');
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);

    try {
      await onUpload(file);
    } catch (err) {
      setError('Failed to upload file');
    } finally {
      setIsUploading(false);
    }
  };

  const handleRemove = () => {
    setFile(null);
    setError(null);
  };

  return (
    <div className="space-y-4">
      {!file ? (
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-8 text-center transition ${
            isDragging
              ? 'border-orange-500 bg-orange-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
          <p className="text-gray-600 mb-2">
            Drag and drop your GPX file here, or
          </p>
          <label className="cursor-pointer text-orange-500 hover:text-orange-600 font-medium">
            browse files
            <input
              type="file"
              accept=".gpx"
              onChange={handleFileSelect}
              className="hidden"
            />
          </label>
          <p className="text-sm text-gray-400 mt-2">
            GPX files from Strava, Garmin, or other running apps
          </p>
        </div>
      ) : (
        <div className="border rounded-lg p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FileText className="w-8 h-8 text-orange-500" />
            <div>
              <p className="font-medium">{file.name}</p>
              <p className="text-sm text-gray-500">
                {(file.size / 1024).toFixed(1)} KB
              </p>
            </div>
          </div>
          <button
            onClick={handleRemove}
            className="p-2 text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      )}

      {error && (
        <p className="text-red-500 text-sm">{error}</p>
      )}

      {file && (
        <button
          onClick={handleUpload}
          disabled={isUploading}
          className="w-full py-3 bg-orange-500 text-white font-semibold rounded-lg hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isUploading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Analyzing...
            </>
          ) : (
            'Analyze Course'
          )}
        </button>
      )}
    </div>
  );
}
```

**Task 2: Elevation Chart Component**

Create `src/components/ElevationChart.tsx`:
```tsx
'use client';

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface ElevationPoint {
  mile: number;
  elevation_ft: number;
  grade_percent: number;
}

interface ElevationChartProps {
  data: ElevationPoint[];
}

export default function ElevationChart({ data }: ElevationChartProps) {
  // Calculate min/max for better visualization
  const elevations = data.map(d => d.elevation_ft);
  const minElevation = Math.min(...elevations);
  const maxElevation = Math.max(...elevations);
  const padding = (maxElevation - minElevation) * 0.1;

  return (
    <div className="bg-white rounded-lg border p-4">
      <h4 className="text-sm font-medium text-gray-500 mb-4">Elevation Profile</h4>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="elevationGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="mile"
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => `${value}mi`}
          />
          <YAxis
            domain={[minElevation - padding, maxElevation + padding]}
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => `${value.toFixed(0)}ft`}
            width={50}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const point = payload[0].payload as ElevationPoint;
                return (
                  <div className="bg-white border rounded-lg shadow-lg p-3">
                    <p className="font-medium">Mile {point.mile}</p>
                    <p className="text-sm text-gray-600">
                      Elevation: {point.elevation_ft.toFixed(0)} ft
                    </p>
                    <p className="text-sm text-gray-600">
                      Grade: {point.grade_percent.toFixed(1)}%
                    </p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Area
            type="monotone"
            dataKey="elevation_ft"
            stroke="#f97316"
            strokeWidth={2}
            fill="url(#elevationGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
```

**Task 3: Race Form Component**

Create `src/components/RaceForm.tsx`:
```tsx
'use client';

import { useState } from 'react';
import { RaceInfo } from '@/lib/api';
import { Loader2 } from 'lucide-react';

interface RaceFormProps {
  onSubmit: (raceInfo: RaceInfo) => Promise<void>;
  defaultDistance?: number;
}

const COMMON_DISTANCES = [
  { label: '5K', miles: 3.1 },
  { label: '10K', miles: 6.2 },
  { label: 'Half Marathon', miles: 13.1 },
  { label: 'Marathon', miles: 26.2 },
  { label: '50K', miles: 31.1 },
];

export default function RaceForm({ onSubmit, defaultDistance }: RaceFormProps) {
  const [name, setName] = useState('');
  const [distance, setDistance] = useState(defaultDistance?.toString() || '26.2');
  const [date, setDate] = useState('');
  const [location, setLocation] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await onSubmit({
        name,
        distance_miles: parseFloat(distance),
        date,
        location,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Race Name
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g., Boston Marathon"
          required
          className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Distance
        </label>
        <div className="flex flex-wrap gap-2 mb-3">
          {COMMON_DISTANCES.map((d) => (
            <button
              key={d.label}
              type="button"
              onClick={() => setDistance(d.miles.toString())}
              className={`px-3 py-1 rounded-full text-sm ${
                parseFloat(distance) === d.miles
                  ? 'bg-orange-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {d.label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <input
            type="number"
            value={distance}
            onChange={(e) => setDistance(e.target.value)}
            step="0.1"
            min="0.1"
            required
            className="w-24 px-4 py-3 border rounded-lg focus:ring-2 focus:ring-orange-500"
          />
          <span className="text-gray-500">miles</span>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Race Date
        </label>
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          required
          className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-orange-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Location
        </label>
        <input
          type="text"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="e.g., Boston, MA"
          required
          className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-orange-500"
        />
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full py-4 bg-orange-500 text-white font-semibold rounded-lg hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {isSubmitting ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Generating Strategy...
          </>
        ) : (
          'Generate Race Strategy'
        )}
      </button>
    </form>
  );
}
```

**Expected output:** File upload working, elevation chart rendering, race form complete.

---

## Day 4: Strategy Display + Streaming UI

### Learning (1.5 hrs)

**Server-Sent Events (SSE)**
- Read: [MDN - Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- Key concepts: EventSource, event streams, reconnection
- Alternative: Fetch with ReadableStream (what we're using)

**React Markdown**
- Read: [react-markdown docs](https://github.com/remarkjs/react-markdown)
- Simple usage: `<ReactMarkdown>{markdownString}</ReactMarkdown>`

### Building (5 hrs)

**Task 1: Add Streaming Endpoint to Backend**

Update `backend/api/routes/strategy.py` (add this endpoint):
```python
from fastapi.responses import StreamingResponse
import asyncio
import json

@router.post("/generate-stream")
async def generate_strategy_stream(request: GenerateStrategyRequest):
    """
    Generate strategy with streaming responses.

    Returns Server-Sent Events with progress updates.
    """
    async def event_stream():
        try:
            # Convert request to internal model
            race_info = RaceInfo(
                name=request.race_info.name,
                distance_miles=request.race_info.distance_miles,
                date=request.race_info.date,
                location=request.race_info.location
            )

            # Build context
            profile = build_runner_profile(request.access_token)
            context = prepare_race_context(profile, race_info)

            # Stream each agent's response
            sections = [
                ("pacing", orchestrator.pacing_agent, "Create a pacing strategy"),
                ("nutrition", orchestrator.nutrition_agent, "Create a nutrition plan"),
                ("mental", orchestrator.mental_agent, "Create mental preparation")
            ]

            results = {}

            for section_name, agent, prompt in sections:
                # Send section start
                yield f"data: {json.dumps({'type': 'section_start', 'section': section_name})}\n\n"

                # Generate response (in production, stream from OpenAI)
                response = agent.run(prompt, context=context)
                results[section_name] = response

                # Simulate streaming by chunking the response
                words = response.split(' ')
                chunk_size = 5

                for i in range(0, len(words), chunk_size):
                    chunk = ' '.join(words[i:i + chunk_size]) + ' '
                    yield f"data: {json.dumps({'type': 'chunk', 'section': section_name, 'content': chunk})}\n\n"
                    await asyncio.sleep(0.05)  # Small delay for effect

                yield f"data: {json.dumps({'type': 'section_complete', 'section': section_name})}\n\n"

            # Save and return complete strategy
            user_id = await get_or_create_user(12345)
            strategy_id = await save_strategy(
                user_id=user_id,
                race_name=race_info.name,
                race_distance=race_info.distance_miles,
                race_date=race_info.date,
                pacing=results["pacing"],
                nutrition=results["nutrition"],
                mental=results["mental"],
                course_analysis=None,
                predicted_time=profile.predicted_marathon_time
            )

            final_strategy = {
                "id": strategy_id,
                "race_name": race_info.name,
                "generated_at": datetime.now().isoformat(),
                "pacing_strategy": results["pacing"],
                "nutrition_plan": results["nutrition"],
                "mental_preparation": results["mental"],
                "predicted_finish_time": profile.predicted_marathon_time
            }

            yield f"data: {json.dumps({'type': 'complete', 'strategy': final_strategy})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

**Task 2: Strategy Display Component**

Create `src/components/StrategyDisplay.tsx`:
```tsx
'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Strategy, CourseAnalysis } from '@/lib/api';
import ElevationChart from './ElevationChart';
import PDFExport from './PDFExport';
import { Share2, Download, Copy, Check } from 'lucide-react';

interface StrategyDisplayProps {
  strategy: Strategy;
  courseAnalysis?: CourseAnalysis | null;
}

export default function StrategyDisplay({ strategy, courseAnalysis }: StrategyDisplayProps) {
  const [activeTab, setActiveTab] = useState<'pacing' | 'nutrition' | 'mental'>('pacing');
  const [copied, setCopied] = useState(false);

  const shareUrl = `${window.location.origin}/strategy/${strategy.id}`;

  const handleCopyLink = async () => {
    await navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return hours > 0 ? `${hours}:${mins.toString().padStart(2, '0')}` : `${mins} min`;
  };

  const tabs = [
    { id: 'pacing', label: 'Pacing Strategy', content: strategy.pacing_strategy },
    { id: 'nutrition', label: 'Nutrition Plan', content: strategy.nutrition_plan },
    { id: 'mental', label: 'Mental Prep', content: strategy.mental_preparation },
  ] as const;

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="bg-white rounded-lg border p-6">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{strategy.race_name}</h2>
            <p className="text-gray-500 mt-1">
              Generated on {new Date(strategy.generated_at).toLocaleDateString()}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">Predicted Finish</p>
            <p className="text-3xl font-bold text-orange-500">
              {formatTime(strategy.predicted_finish_time)}
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 mt-6 pt-6 border-t">
          <button
            onClick={handleCopyLink}
            className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-50"
          >
            {copied ? <Check className="w-4 h-4 text-green-500" /> : <Share2 className="w-4 h-4" />}
            {copied ? 'Copied!' : 'Share'}
          </button>
          <PDFExport strategy={strategy} courseAnalysis={courseAnalysis} />
        </div>
      </div>

      {/* Elevation Chart */}
      {courseAnalysis && (
        <ElevationChart data={courseAnalysis.elevation_profile} />
      )}

      {/* Strategy Tabs */}
      <div className="bg-white rounded-lg border">
        <div className="border-b">
          <div className="flex">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 px-6 py-4 text-sm font-medium transition ${
                  activeTab === tab.id
                    ? 'text-orange-500 border-b-2 border-orange-500'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="p-6">
          {tabs.map((tab) => (
            <div
              key={tab.id}
              className={activeTab === tab.id ? 'block' : 'hidden'}
            >
              <div className="prose prose-orange max-w-none">
                <ReactMarkdown>{tab.content}</ReactMarkdown>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

**Task 3: Shareable Strategy Page**

Create `src/app/strategy/[id]/page.tsx`:
```tsx
import { api } from '@/lib/api';
import StrategyDisplay from '@/components/StrategyDisplay';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

interface PageProps {
  params: { id: string };
}

export default async function StrategyPage({ params }: PageProps) {
  let strategy;

  try {
    strategy = await api.getStrategy(params.id);
  } catch {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Strategy Not Found</h1>
          <p className="text-gray-600 mb-8">This strategy may have been deleted or the link is invalid.</p>
          <Link href="/" className="text-orange-500 hover:text-orange-600">
            Go Home
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-5xl mx-auto px-4 py-4">
          <Link href="/dashboard" className="flex items-center gap-2 text-gray-600 hover:text-gray-900">
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        <StrategyDisplay strategy={strategy} />
      </main>

      <footer className="border-t bg-white mt-16">
        <div className="max-w-5xl mx-auto px-4 py-8 text-center text-gray-500">
          <p>Generated by <Link href="/" className="text-orange-500">Race Coach</Link></p>
        </div>
      </footer>
    </div>
  );
}
```

**Expected output:** Strategy renders with markdown formatting, tabs work, share link works.

---

## Day 5: PDF Export

### Learning (1 hr)

**React-PDF Options:**
- `@react-pdf/renderer` - Generate PDFs in React (what we'll use)
- `html2pdf.js` - Convert HTML to PDF (simpler but less control)
- Server-side generation (better for complex PDFs)

Read: [@react-pdf/renderer docs](https://react-pdf.org/)

### Building (4 hrs)

**Task 1: PDF Export Component**

Create `src/components/PDFExport.tsx`:
```tsx
'use client';

import { useState } from 'react';
import {
  Document,
  Page,
  Text,
  View,
  StyleSheet,
  pdf,
} from '@react-pdf/renderer';
import { Strategy, CourseAnalysis } from '@/lib/api';
import { Download, Loader2 } from 'lucide-react';

// PDF Styles
const styles = StyleSheet.create({
  page: {
    padding: 40,
    fontFamily: 'Helvetica',
  },
  header: {
    marginBottom: 30,
    borderBottom: '1 solid #e5e7eb',
    paddingBottom: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
  },
  subtitle: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 8,
  },
  predictedTime: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#f97316',
    marginTop: 12,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 12,
    backgroundColor: '#f3f4f6',
    padding: 8,
  },
  content: {
    fontSize: 11,
    lineHeight: 1.6,
    color: '#374151',
  },
  paragraph: {
    marginBottom: 8,
  },
  footer: {
    position: 'absolute',
    bottom: 30,
    left: 40,
    right: 40,
    textAlign: 'center',
    fontSize: 10,
    color: '#9ca3af',
  },
  courseStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    backgroundColor: '#f9fafb',
    padding: 12,
    marginBottom: 20,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#111827',
  },
  statLabel: {
    fontSize: 10,
    color: '#6b7280',
  },
});

interface PDFDocumentProps {
  strategy: Strategy;
  courseAnalysis?: CourseAnalysis | null;
}

const formatTime = (minutes: number) => {
  const hours = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);
  return hours > 0 ? `${hours}:${mins.toString().padStart(2, '0')}` : `${mins} min`;
};

// Simple markdown to plain text (basic conversion)
const markdownToPlain = (md: string): string[] => {
  return md
    .replace(/#{1,6}\s/g, '') // Remove headers
    .replace(/\*\*/g, '') // Remove bold
    .replace(/\*/g, '') // Remove italic
    .replace(/`/g, '') // Remove code
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Convert links to text
    .split('\n')
    .filter(line => line.trim());
};

const StrategyPDF = ({ strategy, courseAnalysis }: PDFDocumentProps) => (
  <Document>
    <Page size="A4" style={styles.page}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>{strategy.race_name}</Text>
        <Text style={styles.subtitle}>
          Race Strategy | Generated {new Date(strategy.generated_at).toLocaleDateString()}
        </Text>
        <Text style={styles.predictedTime}>
          Predicted Finish: {formatTime(strategy.predicted_finish_time)}
        </Text>
      </View>

      {/* Course Stats */}
      {courseAnalysis && (
        <View style={styles.courseStats}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{courseAnalysis.total_distance_miles.toFixed(1)} mi</Text>
            <Text style={styles.statLabel}>Distance</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{courseAnalysis.total_elevation_gain_ft} ft</Text>
            <Text style={styles.statLabel}>Elevation Gain</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{courseAnalysis.difficulty_rating}</Text>
            <Text style={styles.statLabel}>Difficulty</Text>
          </View>
        </View>
      )}

      {/* Pacing Strategy */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Pacing Strategy</Text>
        <View style={styles.content}>
          {markdownToPlain(strategy.pacing_strategy).map((para, i) => (
            <Text key={i} style={styles.paragraph}>{para}</Text>
          ))}
        </View>
      </View>

      {/* Nutrition Plan */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Nutrition Plan</Text>
        <View style={styles.content}>
          {markdownToPlain(strategy.nutrition_plan).map((para, i) => (
            <Text key={i} style={styles.paragraph}>{para}</Text>
          ))}
        </View>
      </View>

      {/* Footer */}
      <Text style={styles.footer}>
        Generated by Race Coach | race-coach.vercel.app
      </Text>
    </Page>

    {/* Page 2: Mental Preparation */}
    <Page size="A4" style={styles.page}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Mental Preparation</Text>
        <View style={styles.content}>
          {markdownToPlain(strategy.mental_preparation).map((para, i) => (
            <Text key={i} style={styles.paragraph}>{para}</Text>
          ))}
        </View>
      </View>

      <Text style={styles.footer}>
        Generated by Race Coach | race-coach.vercel.app
      </Text>
    </Page>
  </Document>
);

interface PDFExportProps {
  strategy: Strategy;
  courseAnalysis?: CourseAnalysis | null;
}

export default function PDFExport({ strategy, courseAnalysis }: PDFExportProps) {
  const [isGenerating, setIsGenerating] = useState(false);

  const handleExport = async () => {
    setIsGenerating(true);

    try {
      const blob = await pdf(
        <StrategyPDF strategy={strategy} courseAnalysis={courseAnalysis} />
      ).toBlob();

      // Create download link
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${strategy.race_name.replace(/\s+/g, '-')}-strategy.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('PDF generation failed:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <button
      onClick={handleExport}
      disabled={isGenerating}
      className="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50"
    >
      {isGenerating ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        <Download className="w-4 h-4" />
      )}
      {isGenerating ? 'Generating...' : 'Download PDF'}
    </button>
  );
}
```

**Expected output:** Click "Download PDF" → downloads formatted strategy document.

---

## Day 6: Vercel Deployment + Final Polish

### Building (5 hrs)

**Task 1: Prepare for Deployment**

Update `next.config.js`:
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Allow images from external sources if needed
  images: {
    domains: ['your-domain.com'],
  },

  // Environment variables exposed to browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
};

module.exports = nextConfig;
```

**Task 2: Update CORS on Backend**

In your Railway backend, update the `ALLOWED_ORIGINS` environment variable:
```
ALLOWED_ORIGINS=https://race-coach.vercel.app,https://your-custom-domain.com
```

**Task 3: Deploy to Vercel**

1. Push your code to GitHub
2. Go to [vercel.com](https://vercel.com) and import your repository
3. Configure environment variables:
   ```
   NEXT_PUBLIC_API_URL=https://your-app.railway.app
   NEXT_PUBLIC_STRAVA_CLIENT_ID=your_client_id
   STRAVA_CLIENT_SECRET=your_client_secret
   ```
4. Deploy

**Task 4: Update Strava OAuth Redirect**

Go to Strava API settings and add your Vercel URL as an authorized redirect URI:
```
https://race-coach.vercel.app/api/auth/callback
```

**Task 5: Final UI Polish**

Add loading states, error boundaries, and responsive design:

Create `src/components/ui/LoadingSpinner.tsx`:
```tsx
import { Loader2 } from 'lucide-react';

export default function LoadingSpinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  return (
    <div className="flex items-center justify-center p-8">
      <Loader2 className={`${sizeClasses[size]} animate-spin text-orange-500`} />
    </div>
  );
}
```

Create `src/app/error.tsx`:
```tsx
'use client';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Something went wrong</h2>
        <p className="text-gray-600 mb-8">{error.message}</p>
        <button
          onClick={reset}
          className="px-6 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
```

**Task 6: Test Full Flow**

1. Visit your deployed Vercel URL
2. Connect Strava account
3. Upload GPX file (or skip)
4. Fill in race details
5. Generate strategy
6. Download PDF
7. Share link and verify it works

**Expected output:** Full app working on production URLs.

---

## Day 7: Documentation + Demo Video

### Building (4 hrs)

**Task 1: Update README.md**

Create a professional README:
```markdown
# Race Coach

AI-powered race strategy generator that creates personalized pacing, nutrition, and mental preparation plans based on your training data.

![Race Coach Demo](./demo.gif)

## Features

- **Strava Integration** - Analyzes your training history automatically
- **Course Analysis** - Upload GPX files for elevation-aware strategies
- **Multi-Agent AI** - Specialized agents for pacing, nutrition, and mental prep
- **Vision Analysis** - Upload course photos for AI-powered insights
- **PDF Export** - Download your strategy for race day
- **Shareable Links** - Share strategies with coaches or friends

## Tech Stack

### Frontend
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Recharts for visualization
- React-PDF for exports

### Backend
- FastAPI (Python)
- Multi-agent architecture with OpenAI
- Pinecone vector database for RAG
- PostgreSQL for persistence
- Semantic caching layer

### Infrastructure
- Vercel (Frontend)
- Railway (Backend + Database)

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Vercel    │────▶│   Railway   │────▶│  Pinecone   │
│  (Next.js)  │     │  (FastAPI)  │     │  (Vectors)  │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
              ┌──────────┐  ┌──────────┐
              │ Postgres │  │  OpenAI  │
              └──────────┘  └──────────┘
```

## Local Development

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Fill in API keys
uvicorn backend.api.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local  # Fill in API URL
npm run dev
```

## Environment Variables

### Backend (.env)
```
OPENAI_API_KEY=
PINECONE_API_KEY=
PINECONE_ENVIRONMENT=
MAPBOX_ACCESS_TOKEN=
STRAVA_CLIENT_ID=
STRAVA_CLIENT_SECRET=
DATABASE_URL=
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=
NEXT_PUBLIC_STRAVA_CLIENT_ID=
STRAVA_CLIENT_SECRET=
```

## Skills Demonstrated

- **AI Engineering**: Multi-agent orchestration, RAG pipelines, prompt engineering
- **Full-Stack Development**: React, FastAPI, PostgreSQL
- **API Integration**: Strava OAuth, OpenAI, Pinecone, Mapbox
- **Production Systems**: Caching, streaming, error handling
- **DevOps**: Vercel, Railway, environment management

## License

MIT

---

Built by [Your Name] for Waterloo SE Co-op applications.
```

**Task 2: Record Demo Video**

Use Loom (free) to record a 60-90 second demo:

**Script:**
1. (0-10s) "This is Race Coach, an AI-powered race strategy generator I built."
2. (10-25s) Show Strava login and data being pulled
3. (25-40s) Upload GPX file, show elevation chart
4. (40-60s) Generate strategy, show streaming UI
5. (60-75s) Show the three strategy sections (pacing, nutrition, mental)
6. (75-90s) "Built with FastAPI, multi-agent AI, and RAG. Check out the code on GitHub."

**Task 3: Create Architecture Diagram**

Use Excalidraw (free) to create a visual diagram showing:
- Frontend (Vercel) → Backend (Railway)
- Backend → Pinecone (RAG), OpenAI (LLM), Postgres (Storage)
- The three agents with their tools
- Data flow from Strava → Processing → AI → Strategy

Save as `architecture.png` in your repo.

**Task 4: Final GitHub Polish**

- Add demo GIF to README (use LICEcap or similar to record)
- Ensure no API keys in code
- Add `.env.example` files
- Add LICENSE file
- Tag release as v1.0.0

---

## Week 4 Deliverables

By end of week, you should have:

1. **Complete frontend** - Next.js app with all pages working
2. **Streaming UI** - Real-time strategy generation display
3. **PDF export** - Downloadable strategy documents
4. **Shareable links** - Public strategy pages
5. **Production deployment** - Vercel + Railway fully connected
6. **Demo video** - 60-90 second walkthrough
7. **Documentation** - Professional README with architecture

### Final File Structure

```
Race-Coach/
├── backend/
│   ├── api/
│   ├── agents/
│   ├── rag/
│   ├── course/
│   ├── cache/
│   ├── database/
│   ├── requirements.txt
│   └── railway.toml
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   └── types/
│   ├── package.json
│   └── next.config.js
├── PLAN.md
├── WEEK1.md
├── WEEK2.md
├── WEEK3.md
├── WEEK4.md
├── README.md
├── architecture.png
└── demo.gif
```

---

## Learning Resources Summary

| Resource | Time | When |
|----------|------|------|
| [Next.js App Router](https://nextjs.org/docs/app) | 1 hr | Day 1 |
| [Recharts Guide](https://recharts.org/en-US/guide) | 30 min | Day 3 |
| [MDN - Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events) | 45 min | Day 4 |
| [React-PDF Docs](https://react-pdf.org/) | 45 min | Day 5 |

**Total structured learning: ~4-5 hours**

---

## Project Complete!

You now have a portfolio project demonstrating:

1. **AI Engineering** - Multi-agent orchestration, RAG, function calling, vision
2. **Full-Stack Skills** - React, Python, SQL, REST APIs
3. **Production Mindset** - Caching, streaming, error handling, deployment
4. **Developer Experience** - Documentation, demos, clean code

### Next Steps for Co-op Applications

1. Add this to your resume under "Projects"
2. Include the live demo link and GitHub repo
3. Prepare to discuss:
   - Why you chose multi-agent over single prompt
   - How RAG reduces hallucinations
   - Your caching strategy and why it matters
   - Challenges you faced and how you solved them

Good luck with your Waterloo co-op search!
