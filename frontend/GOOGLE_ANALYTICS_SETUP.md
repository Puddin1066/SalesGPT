# Google Analytics Setup

Google Analytics has been integrated into the Next.js frontend application.

## Setup Instructions

### 1. Get Your Google Analytics Measurement ID

1. Go to [Google Analytics](https://analytics.google.com/)
2. Create a new property or use an existing one
3. Get your Measurement ID (format: `G-XXXXXXXXXX`)
4. Copy the Measurement ID

### 2. Configure Environment Variable

Create or update `.env.local` in the `frontend/` directory:

```bash
# Google Analytics Configuration
NEXT_PUBLIC_GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
```

Replace `G-XXXXXXXXXX` with your actual Measurement ID.

**Important:** 
- The `NEXT_PUBLIC_` prefix is required for Next.js to expose the variable to the browser
- Never commit `.env.local` to version control (it should already be in `.gitignore`)

### 3. Restart Development Server

After adding the environment variable, restart your Next.js development server:

```bash
npm run dev
# or
yarn dev
```

## Features

The implementation includes:

1. **Automatic Page View Tracking**: Tracks page views on all route changes
2. **Custom Event Tracking**: Utility functions for tracking custom events
3. **TypeScript Support**: Full type definitions for gtag functions

## Usage

### Track Custom Events

Import the `event` function and use it anywhere in your components:

```typescript
import { event } from '@/lib/gtag';

// Track a button click
event({
  action: 'click',
  category: 'engagement',
  label: 'header_cta_button',
  value: 1
});

// Track a form submission
event({
  action: 'submit',
  category: 'form',
  label: 'contact_form'
});
```

### Manual Page View Tracking

If you need to manually track a page view:

```typescript
import { pageview } from '@/lib/gtag';

pageview('/custom-path');
```

## Files Created

- `src/lib/gtag.ts` - Google Analytics utility functions
- `src/components/GoogleAnalytics.tsx` - Google Analytics component
- `src/types/gtag.d.ts` - TypeScript type definitions
- `src/pages/_app.tsx` - Updated to include Google Analytics tracking

## Verification

1. Open your browser's Developer Tools (F12)
2. Go to the Network tab
3. Filter by "google-analytics" or "gtag"
4. Navigate through your app
5. You should see requests to `https://www.googletagmanager.com/gtag/js` and `https://www.google-analytics.com/g/collect`

Alternatively, use the Google Analytics DebugView:
1. Install the [Google Analytics Debugger](https://chrome.google.com/webstore/detail/google-analytics-debugger/jnkmfdileelhofjcijamephohjechhna) Chrome extension
2. Navigate your app and check the DebugView in Google Analytics

## Troubleshooting

### Analytics not tracking?

1. **Check environment variable**: Ensure `NEXT_PUBLIC_GOOGLE_ANALYTICS_ID` is set in `.env.local`
2. **Restart server**: Environment variables require a server restart in Next.js
3. **Check console**: Open browser console for any errors
4. **Verify ID format**: Measurement ID should start with `G-` (GA4 format)

### TypeScript errors?

If you see TypeScript errors about `window.gtag`, ensure:
- `src/types/gtag.d.ts` is in your `tsconfig.json` include paths
- The types file is properly formatted

## Notes

- The implementation uses Next.js 14's `Script` component for optimal loading
- Analytics only loads in the browser (server-side rendering safe)
- If no `NEXT_PUBLIC_GOOGLE_ANALYTICS_ID` is set, Google Analytics will be disabled (no errors)

