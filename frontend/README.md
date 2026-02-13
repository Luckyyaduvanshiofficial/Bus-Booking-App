# Bus Booking Platform - Frontend

Next.js 14 PWA for Bus Booking Platform

## Setup Instructions

### 1. Installation

```bash
# Install dependencies
npm install

# Create .env.local
cp .env.example .env.local
```

### 2. Environment Variables

```
NEXT_PUBLIC_BACKEND_API=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-key
```

### 3. Running Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view it on your browser.

### 4. Building for Production

```bash
npm run build
npm run start
```

### 5. Deploying to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variables in Vercel dashboard
```

## Project Structure

```
frontend/
├── app/                    # Next.js 14 app router
│   ├── (auth)/            # Auth pages (login, register)
│   ├── dashboard/         # User dashboard
│   ├── search/           # Bus search
│   ├── my-bookings/      # Booking management
│   ├── operator/         # Operator pages
│   ├── layout.tsx        # Root layout
│   └── page.tsx          # Home page
├── components/           # Reusable React components
├── lib/
│   ├── api.ts           # API client
│   ├── supabase.ts      # Supabase client
│   ├── store.ts         # Zustand stores
│   └── i18n.ts          # Translations (Hi + En)
├── styles/
│   └── globals.css      # Global styles + Tailwind
├── public/              # Static files
└── package.json
```

## Technologies

- **Framework:** Next.js 14 (App Router)
- **Styling:** Tailwind CSS
- **State Management:** Zustand
- **Authentication:** Supabase Auth
- **API:** Axios
- **Maps:** Leaflet + React-Leaflet
- **Form Handling:** React Hook Form

## Features

- ✅ Mobile-first PWA design
- ✅ Hindi + English bilingual support
- ✅ Real-time bus search
- ✅ Booking management
- ✅ Payment integration ready
- ✅ Operator dashboard
- ✅ Reviews and ratings

## Key Pages

- `/` - Home page
- `/login` - Login with OTP
- `/register` - User registration
- `/dashboard` - User dashboard
- `/search` - Bus search
- `/my-bookings` - Booking history
- `/profile` - User profile
- `/operator/buses` - Operator's buses
- `/become-operator` - Register as operator

## Development Tips

1. Use `useAuthStore` for authentication state
2. Use `useSearchStore` for search parameters
3. Use `useUIStore` for UI state (language, etc)
4. Always use `API` client for backend calls
5. Images are proxied through Cloudinary
6. All pages must check authentication

## Contributing

1. Create feature branch
2. Make changes
3. Test on mobile device
4. Create pull request

## Support

For issues or questions, contact: [your-email]
