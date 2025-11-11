# LinkedIn Profile Monitor Dashboard

A modern web dashboard for monitoring LinkedIn profiles, built with Next.js 16, TypeScript, and Tailwind CSS.

## Features

- **Profile Management**: View, add, and remove monitored LinkedIn profiles
- **Real-time Stats**: Dashboard showing total profiles and recent activity
- **Direct Database Queries**: Queries Supabase database directly from the frontend
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Type Safety**: Full TypeScript support with Supabase client

## Getting Started

### Prerequisites

- Node.js 18+
- npm, yarn, or pnpm
- Backend API server running (see main project README)

### Installation

1. Install dependencies:
```bash
npm install
# or
yarn install
# or
pnpm install
```

3. Configure environment variables:
```bash
cp .env.local.example .env.local
```

Edit `.env.local` with your Supabase credentials:
```
# Supabase Configuration (required for direct database queries)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

**⚠️ Security Warning**: Direct database queries expose your Supabase credentials to the client-side. Consider using Row Level Security (RLS) policies in Supabase to restrict access.

3. Run the development server:
```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## API Endpoints

The dashboard connects to the following backend endpoints:

- `GET /api/profiles` - Get all monitored profiles
- `POST /api/profiles` - Add a new profile
- `DELETE /api/profiles/{id}` - Remove a profile
- `GET /api/stats` - Get dashboard statistics

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout with metadata
│   ├── page.tsx            # Main dashboard page
│   └── globals.css         # Global styles
├── components/
│   └── ui/                 # Reusable UI components
├── .env.local              # Environment variables
└── README.md               # This file
```

## Technologies Used

- **Next.js 16** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Lucide React** - Icons
- **React Hooks** - State management

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Code Style

This project uses TypeScript for type safety and Tailwind CSS for styling. Components are built with modern React patterns using hooks for state management.

## Contributing

1. Follow the existing code style
2. Add TypeScript types for new features
3. Test API integrations thoroughly
4. Update this README for any new features

## License

This project is part of the LinkedIn Profile Monitor system.
