# Team Risk Analysis Dashboard

A React-based frontend for visualizing team risk analysis data.

## Features

- **Radar Chart Visualization**: Five-axis radar chart showing risk dimensions
- **Risk List**: Sortable list of detected risks with severity badges
- **Risk Details**: Detailed view with AI-generated recommendations
- **Bilingual Support**: Toggle between Spanish and English
- **Mock Data Mode**: Demo mode with simulated data for testing

## Quick Start

### Install Dependencies

```bash
npm install
```

### Run Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:3000`.

### Build for Production

```bash
npm run build
```

The production build will be in the `dist` directory.

## Components

- **Dashboard**: Main component integrating all features
- **RiskRadarChart**: Radar chart visualization using Chart.js
- **RiskList**: List of risks sorted by severity
- **RiskDetail**: Detailed risk view with recommendations
- **LanguageToggle**: Switch between English and Spanish
- **MockDataToggle**: Toggle between mock and live data

## Mock Data

The dashboard includes built-in mock data for demonstration purposes. The mock data simulates an "overloaded" team scenario with:

- 8 engineers across 3 projects
- Multiple risks at different severity levels
- Bilingual descriptions and recommendations

## API Integration

The dashboard connects to the backend API at `/api`. In development, requests are proxied to `http://localhost:8000`.

### API Endpoints

- `GET /api/risks?team_id={id}&language={en|es}` - Fetch risk data
- `POST /api/signals` - Submit team signals
- `POST /api/analyze` - Trigger risk analysis
- `GET /api/mock-data` - Fetch mock data

## Technology Stack

- **React 18**: UI framework
- **TypeScript**: Type safety
- **Chart.js**: Radar chart visualization
- **Vite**: Build tool and dev server
- **Context API**: State management for language preference

## Privacy

The dashboard displays only team-level aggregated data. No individual engineer information is shown or tracked.
