# Week 4: Frontend + Polish (Simplified)

**Goal:** Build a clean React frontend with strategy display, elevation chart, browser-based PDF export, and deploy to Vercel. Create documentation for your portfolio.

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
│  ├── / (Landing page)                                           │
│  ├── /dashboard (Main app after login)                          │
│  └── /strategy/[id] (View/share strategy)                       │
│                                                                  │
│  Components:                                                     │
│  ├── ElevationChart (Recharts visualization)                    │
│  ├── StrategyDisplay (Markdown rendering)                       │
│  ├── GPXUploader (File upload)                                  │
│  └── RaceForm (Race details input)                              │
│                                                                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Railway (Backend API)                         │
└─────────────────────────────────────────────────────────────────┘
```

**What We're Building:**
- Simple, functional UI (not over-designed)
- Elevation chart with Recharts
- Markdown strategy display
- Browser print for PDF (Cmd+P / Ctrl+P)
- Shareable strategy links

**What We're NOT Building:**
- ❌ Streaming/typewriter effects
- ❌ react-pdf complex rendering
- ❌ Fancy animations

---

## Day 1: Next.js Setup + Basic Layout

### Learning (1 hr)

**Next.js App Router (Quick Refresher)**
- Read: [Next.js - App Router Basics](https://nextjs.org/docs/app/building-your-application/routing)
- Key concepts: Server vs client components, `"use client"` directive

### Building (5 hrs)

**Task 1: Create Next.js Project**

```bash
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir
cd frontend
```

**Task 2: Install Dependencies**

```bash
npm install recharts react-markdown
```

**Task 3: Project Structure**

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx              # Landing page
│   │   ├── globals.css
│   │   ├── dashboard/
│   │   │   └── page.tsx          # Main app
│   │   └── strategy/
│   │       └── [id]/
│   │           └── page.tsx      # View strategy
│   ├── components/
│   │   ├── ElevationChart.tsx
│   │   ├── StrategyDisplay.tsx
│   │   ├── GPXUploader.tsx
│   │   └── RaceForm.tsx
│   ├── lib/
│   │   └── api.ts               # Backend API client
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
```

**Task 5: Create Types**

Create `src/types/index.ts`:
```typescript
export interface ElevationPoint {
  mile: number;
  elevation_ft: number;
  grade_percent: number;
}

export interface CourseAnalysis {
  total_distance_miles: number;
  total_elevation_gain_ft: number;
  total_elevation_loss_ft: number;
  elevation_profile: ElevationPoint[];
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
  strategy_content: string;
  course_analysis?: CourseAnalysis;
  predicted_finish_time?: number;
}

export interface RaceInfo {
  name: string;
  distance_miles: number;
  date: string;
  location: string;
}
```

**Task 6: Create API Client**

Create `src/lib/api.ts`:
```typescript
import { CourseAnalysis, Strategy, RaceInfo } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  async getStravaAuthUrl(): Promise<string> {
    const res = await fetch(`${API_URL}/auth/strava/url`);
    const data = await res.json();
    return data.auth_url;
  }

  async analyzeGPX(file: File): Promise<CourseAnalysis> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_URL}/course/analyze-gpx`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) throw new Error('Failed to analyze GPX');
    return res.json();
  }

  async generateStrategy(
    raceInfo: RaceInfo,
    stravaToken: string,
    stravaAthleteId: number,
    courseAnalysis?: CourseAnalysis
  ): Promise<Strategy> {
    const res = await fetch(
      `${API_URL}/strategy/generate?strava_token=${stravaToken}&strava_athlete_id=${stravaAthleteId}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          race_info: raceInfo,
          course_analysis: courseAnalysis,
        }),
      }
    );

    if (!res.ok) throw new Error('Failed to generate strategy');
    return res.json();
  }

  async getStrategy(id: string): Promise<Strategy> {
    const res = await fetch(`${API_URL}/strategy/${id}`);
    if (!res.ok) throw new Error('Strategy not found');
    return res.json();
  }

  async getUserPreferences(userId: number): Promise<Record<string, string>> {
    const res = await fetch(`${API_URL}/user/preferences?user_id=${userId}`);
    if (!res.ok) return {};
    const data = await res.json();
    return data.preferences;
  }

  async updateUserPreferences(userId: number, preferences: Record<string, string>): Promise<void> {
    await fetch(`${API_URL}/user/preferences?user_id=${userId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(preferences),
    });
  }
}

export const api = new ApiClient();
```

**Task 7: Create Layout**

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

**Task 8: Create Landing Page**

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
          AI-powered race strategies based on your training data,
          course analysis, and expert running knowledge.
        </p>

        <Link
          href="/dashboard"
          className="inline-block px-8 py-4 bg-orange-500 text-white font-semibold rounded-lg hover:bg-orange-600 transition"
        >
          Get Started
        </Link>

        <div className="mt-16 grid grid-cols-3 gap-8 text-left">
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Pacing Strategy</h3>
            <p className="text-sm text-gray-600">
              Mile-by-mile splits based on your fitness and course profile
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

**Expected output:** Basic Next.js app running with landing page.

---

## Day 2: Components - GPX Upload + Elevation Chart

### Learning (1 hr)

**Recharts Basics**
- Read: [Recharts - Getting Started](https://recharts.org/en-US/guide)
- Focus on: AreaChart, responsive containers

### Building (5 hrs)

**Task 1: GPX Uploader Component**

Create `src/components/GPXUploader.tsx`:
```tsx
'use client';

import { useState, useCallback } from 'react';

interface GPXUploaderProps {
  onUpload: (file: File) => Promise<void>;
  isLoading?: boolean;
}

export default function GPXUploader({ onUpload, isLoading }: GPXUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
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
    if (droppedFile?.name.endsWith('.gpx')) {
      setFile(droppedFile);
      setError(null);
    } else {
      setError('Please upload a .gpx file');
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile?.name.endsWith('.gpx')) {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Please upload a .gpx file');
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setError(null);
    try {
      await onUpload(file);
    } catch {
      setError('Failed to analyze file');
    }
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
          <div>
            <p className="font-medium">{file.name}</p>
            <p className="text-sm text-gray-500">
              {(file.size / 1024).toFixed(1)} KB
            </p>
          </div>
          <button
            onClick={() => setFile(null)}
            className="text-gray-400 hover:text-gray-600"
          >
            Remove
          </button>
        </div>
      )}

      {error && <p className="text-red-500 text-sm">{error}</p>}

      {file && (
        <button
          onClick={handleUpload}
          disabled={isLoading}
          className="w-full py-3 bg-orange-500 text-white font-semibold rounded-lg hover:bg-orange-600 disabled:opacity-50"
        >
          {isLoading ? 'Analyzing...' : 'Analyze Course'}
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
import { ElevationPoint } from '@/types';

interface ElevationChartProps {
  data: ElevationPoint[];
}

export default function ElevationChart({ data }: ElevationChartProps) {
  const elevations = data.map(d => d.elevation_ft);
  const minElevation = Math.min(...elevations);
  const maxElevation = Math.max(...elevations);
  const padding = (maxElevation - minElevation) * 0.1 || 50;

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
            tickFormatter={(value) => `${Math.round(value)}ft`}
            width={50}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload?.[0]) {
                const point = payload[0].payload as ElevationPoint;
                return (
                  <div className="bg-white border rounded-lg shadow-lg p-3">
                    <p className="font-medium">Mile {point.mile}</p>
                    <p className="text-sm text-gray-600">
                      Elevation: {Math.round(point.elevation_ft)} ft
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
import { RaceInfo } from '@/types';

interface RaceFormProps {
  onSubmit: (raceInfo: RaceInfo) => Promise<void>;
  defaultDistance?: number;
  isLoading?: boolean;
}

const DISTANCES = [
  { label: '5K', miles: 3.1 },
  { label: '10K', miles: 6.2 },
  { label: 'Half Marathon', miles: 13.1 },
  { label: 'Marathon', miles: 26.2 },
];

export default function RaceForm({ onSubmit, defaultDistance, isLoading }: RaceFormProps) {
  const [name, setName] = useState('');
  const [distance, setDistance] = useState(defaultDistance?.toString() || '26.2');
  const [date, setDate] = useState('');
  const [location, setLocation] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit({
      name,
      distance_miles: parseFloat(distance),
      date,
      location,
    });
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
          {DISTANCES.map((d) => (
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
        disabled={isLoading}
        className="w-full py-4 bg-orange-500 text-white font-semibold rounded-lg hover:bg-orange-600 disabled:opacity-50"
      >
        {isLoading ? 'Generating Strategy...' : 'Generate Race Strategy'}
      </button>
    </form>
  );
}
```

---

## Day 3: Strategy Display + Dashboard

### Building (5 hrs)

**Task 1: Strategy Display Component**

Create `src/components/StrategyDisplay.tsx`:
```tsx
'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Strategy, CourseAnalysis } from '@/types';
import ElevationChart from './ElevationChart';

interface StrategyDisplayProps {
  strategy: Strategy;
  courseAnalysis?: CourseAnalysis | null;
}

export default function StrategyDisplay({ strategy, courseAnalysis }: StrategyDisplayProps) {
  const [copied, setCopied] = useState(false);

  const shareUrl = typeof window !== 'undefined'
    ? `${window.location.origin}/strategy/${strategy.id}`
    : '';

  const handleCopyLink = async () => {
    await navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePrint = () => {
    window.print();
  };

  const formatTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return hours > 0 ? `${hours}:${mins.toString().padStart(2, '0')}` : `${mins} min`;
  };

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="bg-white rounded-lg border p-6 print:border-none print:p-0">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{strategy.race_name}</h2>
            <p className="text-gray-500 mt-1">
              Generated on {new Date(strategy.generated_at).toLocaleDateString()}
            </p>
          </div>
          {strategy.predicted_finish_time && (
            <div className="text-right">
              <p className="text-sm text-gray-500">Predicted Finish</p>
              <p className="text-3xl font-bold text-orange-500">
                {formatTime(strategy.predicted_finish_time)}
              </p>
            </div>
          )}
        </div>

        {/* Action Buttons - Hidden in print */}
        <div className="flex gap-3 mt-6 pt-6 border-t print:hidden">
          <button
            onClick={handleCopyLink}
            className="px-4 py-2 border rounded-lg hover:bg-gray-50"
          >
            {copied ? 'Copied!' : 'Copy Link'}
          </button>
          <button
            onClick={handlePrint}
            className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800"
          >
            Print / Save PDF
          </button>
        </div>
      </div>

      {/* Elevation Chart - Hidden in print for cleaner output */}
      {courseAnalysis && (
        <div className="print:hidden">
          <ElevationChart data={courseAnalysis.elevation_profile} />
        </div>
      )}

      {/* Course Stats for Print */}
      {courseAnalysis && (
        <div className="hidden print:block mb-4">
          <p><strong>Distance:</strong> {courseAnalysis.total_distance_miles} miles</p>
          <p><strong>Elevation Gain:</strong> {courseAnalysis.total_elevation_gain_ft} ft</p>
          <p><strong>Difficulty:</strong> {courseAnalysis.difficulty_rating}</p>
        </div>
      )}

      {/* Strategy Content */}
      <div className="bg-white rounded-lg border p-6 print:border-none print:p-0">
        <div className="prose prose-orange max-w-none">
          <ReactMarkdown>{strategy.strategy_content}</ReactMarkdown>
        </div>
      </div>

      {/* Footer for print */}
      <div className="hidden print:block text-center text-gray-400 text-sm mt-8">
        Generated by Race Coach - race-coach.vercel.app
      </div>
    </div>
  );
}
```

**Task 2: Add Print Styles**

Update `src/app/globals.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Print styles for PDF export */
@media print {
  body {
    print-color-adjust: exact;
    -webkit-print-color-adjust: exact;
  }

  .print\\:hidden {
    display: none !important;
  }

  .print\\:block {
    display: block !important;
  }

  .print\\:border-none {
    border: none !important;
  }

  .print\\:p-0 {
    padding: 0 !important;
  }

  /* Page breaks */
  h2 {
    page-break-after: avoid;
  }

  .prose h2 {
    margin-top: 1.5rem;
    page-break-after: avoid;
  }

  .prose {
    max-width: none;
    font-size: 11pt;
    line-height: 1.5;
  }
}
```

**Task 3: Dashboard Page**

Create `src/app/dashboard/page.tsx`:
```tsx
'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { Strategy, CourseAnalysis, RaceInfo } from '@/types';
import GPXUploader from '@/components/GPXUploader';
import RaceForm from '@/components/RaceForm';
import ElevationChart from '@/components/ElevationChart';
import StrategyDisplay from '@/components/StrategyDisplay';
import Link from 'next/link';

type Step = 'upload' | 'details' | 'generating' | 'result';

export default function Dashboard() {
  const [step, setStep] = useState<Step>('upload');
  const [courseAnalysis, setCourseAnalysis] = useState<CourseAnalysis | null>(null);
  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // TODO: In production, get these from auth
  const stravaToken = 'demo_token';
  const stravaAthleteId = 12345;

  const handleGPXUpload = async (file: File) => {
    setIsLoading(true);
    setError(null);
    try {
      const analysis = await api.analyzeGPX(file);
      setCourseAnalysis(analysis);
      setStep('details');
    } catch {
      setError('Failed to analyze GPX file');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateStrategy = async (raceInfo: RaceInfo) => {
    setIsLoading(true);
    setError(null);
    setStep('generating');

    try {
      const result = await api.generateStrategy(
        raceInfo,
        stravaToken,
        stravaAthleteId,
        courseAnalysis || undefined
      );
      setStrategy(result);
      setStep('result');
    } catch {
      setError('Failed to generate strategy');
      setStep('details');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartOver = () => {
    setCourseAnalysis(null);
    setStrategy(null);
    setStep('upload');
  };

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-white border-b print:hidden">
        <div className="max-w-5xl mx-auto px-4 py-4 flex justify-between items-center">
          <Link href="/" className="text-xl font-bold text-gray-900">
            Race Coach
          </Link>
        </div>
      </header>

      {/* Progress Steps */}
      <div className="bg-white border-b print:hidden">
        <div className="max-w-5xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            {['Upload Course', 'Race Details', 'Strategy'].map((label, i) => {
              const steps: Step[] = ['upload', 'details', 'result'];
              const currentIndex = steps.indexOf(step === 'generating' ? 'result' : step);
              const isActive = i <= currentIndex;

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
                  {i < 2 && <div className="w-8 h-px bg-gray-300" />}
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

        {/* Step: Upload */}
        {step === 'upload' && (
          <div>
            <h2 className="text-2xl font-bold mb-4">Upload Course Data</h2>
            <p className="text-gray-600 mb-8">
              Upload a GPX file of your race course for elevation analysis (optional).
            </p>
            <GPXUploader onUpload={handleGPXUpload} isLoading={isLoading} />
            <button
              onClick={() => setStep('details')}
              className="mt-4 text-gray-500 hover:text-gray-700"
            >
              Skip - I don't have a GPX file
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
                isLoading={isLoading}
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
          <div className="text-center py-16">
            <div className="inline-block w-8 h-8 border-4 border-orange-500 border-t-transparent rounded-full animate-spin mb-4" />
            <h2 className="text-2xl font-bold">Generating Your Strategy...</h2>
            <p className="text-gray-600 mt-2">This may take a moment.</p>
          </div>
        )}

        {/* Step: Result */}
        {step === 'result' && strategy && (
          <div>
            <div className="flex justify-between items-center mb-8 print:hidden">
              <h2 className="text-2xl font-bold">Your Race Strategy</h2>
              <button
                onClick={handleStartOver}
                className="px-4 py-2 text-gray-600 hover:text-gray-900"
              >
                Start Over
              </button>
            </div>

            <StrategyDisplay strategy={strategy} courseAnalysis={courseAnalysis} />
          </div>
        )}
      </main>
    </div>
  );
}
```

---

## Day 4: Shareable Strategy Page

### Building (4 hrs)

**Task 1: Strategy Page**

Create `src/app/strategy/[id]/page.tsx`:
```tsx
import { api } from '@/lib/api';
import StrategyDisplay from '@/components/StrategyDisplay';
import Link from 'next/link';

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
      <header className="bg-white border-b print:hidden">
        <div className="max-w-5xl mx-auto px-4 py-4">
          <Link href="/" className="text-xl font-bold text-gray-900">
            Race Coach
          </Link>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        <StrategyDisplay strategy={strategy} courseAnalysis={strategy.course_analysis} />
      </main>

      <footer className="border-t bg-white mt-16 print:hidden">
        <div className="max-w-5xl mx-auto px-4 py-8 text-center text-gray-500">
          <p>Generated by <Link href="/" className="text-orange-500">Race Coach</Link></p>
        </div>
      </footer>
    </div>
  );
}
```

---

## Day 5: Vercel Deployment

### Building (4 hrs)

**Task 1: Update next.config.js**

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
};

module.exports = nextConfig;
```

**Task 2: Update Backend CORS**

In Railway, update `ALLOWED_ORIGINS`:
```
ALLOWED_ORIGINS=https://race-coach.vercel.app,http://localhost:3000
```

**Task 3: Deploy to Vercel**

1. Push code to GitHub
2. Go to [vercel.com](https://vercel.com) and import repository
3. Configure environment variables:
   ```
   NEXT_PUBLIC_API_URL=https://your-app.railway.app
   NEXT_PUBLIC_STRAVA_CLIENT_ID=your_client_id
   ```
4. Deploy

**Task 4: Test Full Flow**

1. Visit deployed Vercel URL
2. Upload GPX file (or skip)
3. Fill in race details
4. Generate strategy
5. Use Cmd+P / Ctrl+P to save as PDF
6. Copy and share link

---

## Day 6-7: Documentation + Polish

### Building (4-6 hrs)

**Task 1: Update README.md**

Create a professional README in the root:
```markdown
# Race Coach

AI-powered race strategy generator that creates personalized pacing, nutrition, and mental preparation plans based on your training data.

## Features

- **Strava Integration** - Analyzes your training history
- **Course Analysis** - Upload GPX files for elevation-aware strategies
- **AI Coach** - Single intelligent agent with running expertise
- **PDF Export** - Print or save your strategy (Cmd+P)
- **Shareable Links** - Share strategies with coaches or friends

## Tech Stack

### Frontend
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Recharts

### Backend
- FastAPI (Python)
- OpenAI GPT-4 with function calling
- PostgreSQL (user preferences, strategies)

### Infrastructure
- Vercel (Frontend)
- Railway (Backend + Database)

## Architecture

```
Frontend (Vercel) → Backend API (Railway) → PostgreSQL
                          ↓
                    AI Agent (OpenAI)
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
cp .env.example .env.local
npm run dev
```

## Environment Variables

### Backend
```
OPENAI_API_KEY=
STRAVA_CLIENT_ID=
STRAVA_CLIENT_SECRET=
DATABASE_URL=
```

### Frontend
```
NEXT_PUBLIC_API_URL=
NEXT_PUBLIC_STRAVA_CLIENT_ID=
```

## Skills Demonstrated

- **AI Engineering**: Prompt engineering, function calling, context management
- **Full-Stack Development**: React, FastAPI, PostgreSQL
- **API Integration**: Strava OAuth, OpenAI, weather APIs
- **Data Processing**: Pandas, VDOT calculations, GPX parsing
- **Production Deployment**: Vercel, Railway
- **Software Design**: Knowing when NOT to over-engineer

## License

MIT
```

**Task 2: Create .env.example Files**

Backend `.env.example`:
```
OPENAI_API_KEY=sk-...
STRAVA_CLIENT_ID=
STRAVA_CLIENT_SECRET=
DATABASE_URL=postgresql://...
```

Frontend `.env.example`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRAVA_CLIENT_ID=
```

**Task 3: Final Testing Checklist**

- [ ] Landing page loads
- [ ] GPX upload works
- [ ] Strategy generation completes
- [ ] Strategy renders markdown properly
- [ ] Print/PDF works (Cmd+P)
- [ ] Share link works
- [ ] Mobile responsive
- [ ] No console errors

---

## Week 4 Deliverables

By end of week, you should have:

1. **Next.js frontend** with all pages working
2. **Elevation chart** visualization
3. **Strategy display** with markdown rendering
4. **Browser-based PDF** via print
5. **Shareable links** for strategies
6. **Production deployment** on Vercel
7. **Documentation** - README with setup instructions

### Final File Structure

```
Race-Coach/
├── backend/
│   ├── api/
│   ├── agent/
│   ├── course/
│   ├── database/
│   ├── data_processing/
│   ├── knowledge/
│   ├── models.py
│   ├── pipeline.py
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
├── plans/
│   ├── PLAN.md
│   ├── WEEK1.md
│   ├── WEEK1POST.md
│   ├── WEEK2.md
│   ├── WEEK3.md
│   └── WEEK4.md
├── README.md
└── .gitignore
```

---

## Learning Resources Summary

| Resource | Time | When |
|----------|------|------|
| [Next.js App Router](https://nextjs.org/docs/app) | 1 hr | Day 1 |
| [Recharts Guide](https://recharts.org/en-US/guide) | 30 min | Day 2 |
| [react-markdown](https://github.com/remarkjs/react-markdown) | 30 min | Day 3 |

**Total structured learning: ~4-5 hours**

---

## Project Complete!

You now have a portfolio project demonstrating:

1. **AI Engineering** - Prompt engineering, function calling, context management
2. **Full-Stack Skills** - React, Python, SQL, REST APIs
3. **Production Mindset** - Deployment, error handling, documentation
4. **Good Judgment** - Knowing what to build and what to skip

### For Co-op Applications

- Add to resume under "Projects"
- Include live demo link and GitHub repo
- Be ready to discuss:
  - Why single agent vs multi-agent
  - How you structured the knowledge base
  - Trade-offs you made (what you cut and why)
  - What you'd add with more time
