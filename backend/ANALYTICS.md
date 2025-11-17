# Analytics Integration Guide

Data Detective Academy supports privacy-friendly analytics tracking to help you understand user engagement and optimize your marketing pages.

## Table of Contents

- [Overview](#overview)
- [Supported Analytics Providers](#supported-analytics-providers)
- [Quick Start](#quick-start)
- [Plausible Analytics Setup](#plausible-analytics-setup)
- [Google Analytics Setup](#google-analytics-setup)
- [Tracked Events](#tracked-events)
- [Privacy & GDPR Compliance](#privacy--gdpr-compliance)
- [Testing Analytics](#testing-analytics)
- [Troubleshooting](#troubleshooting)

## Overview

The analytics integration is built into the marketing pages and tracks:

- **Page Views**: Automatically tracked on all marketing pages
- **Button Clicks**: Sign Up, Login, Demo, Contact Sales, etc.
- **Conversions**: User registration and key engagement actions
- **Location Context**: Which page/section triggered the event

All analytics tracking is:
- **Optional**: Disabled by default, enable via environment variables
- **Privacy-focused**: Recommended provider (Plausible) doesn't use cookies
- **Configurable**: Easy to switch between providers or disable completely

## Supported Analytics Providers

### 1. Plausible Analytics (Recommended)

**Pros:**
- ✅ Privacy-friendly and GDPR compliant by default
- ✅ No cookies, no consent banner needed
- ✅ Lightweight (< 1KB script)
- ✅ Open-source and can be self-hosted
- ✅ Simple, beautiful dashboard
- ✅ Automatic bot filtering

**Cons:**
- ❌ Less detailed user tracking than GA
- ❌ Paid service (or self-host)

**Recommended for:** Privacy-conscious organizations, European audiences, educational institutions

### 2. Google Analytics 4

**Pros:**
- ✅ Free (with generous limits)
- ✅ Extremely detailed analytics
- ✅ Integration with Google Ads
- ✅ Familiar to most marketers

**Cons:**
- ❌ Uses cookies (requires consent banner)
- ❌ Privacy concerns
- ❌ More complex setup
- ❌ Heavier script

**Recommended for:** Organizations already using Google ecosystem, need detailed analytics

## Quick Start

### 1. Configure Environment Variables

Copy `.env.example` to `.env` if you haven't already:

```bash
cp .env.example .env
```

Edit `.env` and configure analytics:

```bash
# Enable analytics
ANALYTICS_ENABLED=true

# Choose provider: 'plausible' or 'google'
ANALYTICS_PROVIDER=plausible

# For Plausible:
ANALYTICS_DOMAIN=yourdomain.com
ANALYTICS_SCRIPT_URL=https://plausible.io/js/script.js

# For Google Analytics (if using):
# ANALYTICS_ID=G-XXXXXXXXXX
```

### 2. Restart the Backend

```bash
uvicorn app.main:app --reload
```

### 3. Verify Analytics

Visit your marketing pages and check:
- Plausible: Login to your Plausible dashboard
- Google Analytics: Check Real-time reports

## Plausible Analytics Setup

### Option 1: Plausible Cloud (Recommended)

1. **Sign up for Plausible**
   - Visit: https://plausible.io/register
   - 30-day free trial, then €9/month for up to 10k pageviews

2. **Add Your Website**
   - Click "Add a website"
   - Enter your domain (e.g., `datadetective.academy`)
   - Copy the domain name

3. **Configure Environment Variables**

```bash
ANALYTICS_ENABLED=true
ANALYTICS_PROVIDER=plausible
ANALYTICS_DOMAIN=yourdomain.com
ANALYTICS_SCRIPT_URL=https://plausible.io/js/script.js
```

4. **Verify Installation**
   - Visit your website
   - In Plausible dashboard, you should see a green checkmark
   - May take a few minutes to appear

### Option 2: Self-Hosted Plausible

1. **Deploy Plausible**
   - Follow: https://plausible.io/docs/self-hosting
   - Requires Docker and Docker Compose
   - Free and open-source

2. **Configure Environment Variables**

```bash
ANALYTICS_ENABLED=true
ANALYTICS_PROVIDER=plausible
ANALYTICS_DOMAIN=yourdomain.com
ANALYTICS_SCRIPT_URL=https://analytics.yourdomain.com/js/script.js
```

Replace `analytics.yourdomain.com` with your self-hosted Plausible URL.

### Testing Plausible Locally

For local development:

```bash
ANALYTICS_ENABLED=true
ANALYTICS_PROVIDER=plausible
ANALYTICS_DOMAIN=localhost
ANALYTICS_SCRIPT_URL=https://plausible.io/js/script.js
```

Note: Plausible Cloud filters `localhost` by default. Use a test domain or self-hosted instance for local testing.

## Google Analytics Setup

### 1. Create GA4 Property

1. **Sign in to Google Analytics**
   - Visit: https://analytics.google.com/
   - Create account if needed

2. **Create Property**
   - Click "Admin" (gear icon)
   - Under "Property", click "Create Property"
   - Choose "Web" data stream
   - Enter your website URL

3. **Get Measurement ID**
   - Copy your Measurement ID (format: `G-XXXXXXXXXX`)

### 2. Configure Environment Variables

```bash
ANALYTICS_ENABLED=true
ANALYTICS_PROVIDER=google
ANALYTICS_ID=G-XXXXXXXXXX
```

### 3. Add Cookie Consent Banner

Google Analytics uses cookies and requires user consent under GDPR/CCPA.

**Add to your base template:**

```jinja2
{% if analytics_provider == 'google' %}
    {% include 'cookie-banner.html' %}
{% endif %}
```

Add this before the `</body>` tag in `backend/app/templates/base.html` and other standalone pages.

The cookie banner:
- Appears on first visit
- Stores consent for 365 days
- GDPR compliant
- Responsive design

### 4. Verify Setup

1. Visit your website
2. Open Google Analytics → Reports → Realtime
3. You should see your visit (after accepting cookies)

## Tracked Events

### Automatic Events

- **Page Views**: All marketing pages (`/`, `/features`, `/pricing`, `/about`, `/contact`, etc.)

### Custom Events

All custom events include contextual properties for better insights:

| Event Name | Triggers | Properties | Pages |
|------------|----------|------------|-------|
| `Sign Up Click` | User clicks any sign-up button | `location`: Button location | All pages |
| `Login Click` | User clicks login button | `location`: Button location | All pages |
| `Demo Click` | User clicks demo/view demo | `location`: Button location | Home page |
| `Contact Sales Click` | User clicks contact sales | `plan`: Pricing tier | Pricing page |
| `Contact Sales Email Click` | User clicks sales email link | `location`: Section name | Pricing page |
| `Get Started Click` | User clicks "Get Started" | `plan`: Pricing tier | Pricing page |
| `GitHub Click` | User clicks GitHub link | `plan`: Plan name | Pricing page |
| `View Pricing Click` | User navigates to pricing | `location`: Source page | Features page |

### Event Properties

Properties help segment and analyze events:

- **location**: Where the button appears (e.g., "Hero Section", "Header Navigation", "Pricing CTA Section")
- **plan**: Which pricing tier (e.g., "Freedom Edition", "School", "District")

### Viewing Events

**Plausible:**
1. Go to your dashboard
2. Click "Goals" in the left sidebar
3. Custom events appear automatically

**Google Analytics:**
1. Go to Reports → Engagement → Events
2. Click on event name for details
3. View event parameters under "Event details"

## Privacy & GDPR Compliance

### Plausible Analytics

✅ **GDPR Compliant by Design:**
- No cookies
- No personal data collection
- No cross-site tracking
- Anonymous IP addresses
- Data hosted in EU (Plausible Cloud)
- No consent banner needed

**Privacy Policy:**
Update your privacy policy to mention:
- You use Plausible Analytics
- No personal data is collected
- Link to: https://plausible.io/privacy

### Google Analytics

⚠️ **Requires User Consent:**
- Uses cookies
- May transfer data to US
- Requires cookie consent banner
- Must update privacy policy

**Privacy Policy:**
Include:
- You use Google Analytics
- Types of data collected
- User's right to opt-out
- Link to Google's privacy policy

**Cookie Banner:**
Our implementation (`cookie-banner.html`):
- Shows on first visit
- Stores consent preference
- Respects "Decline" choice
- Automatically blocks GA if declined

## Testing Analytics

### 1. Test Locally

Start the backend:

```bash
cd backend
uvicorn app.main:app --reload
```

Visit http://localhost:8000 and click around.

### 2. Browser Developer Tools

**Check Script Loading:**

```javascript
// Open Console (F12)
// For Plausible:
console.log(window.plausible)

// For Google Analytics:
console.log(window.gtag)
```

**Manual Event Test:**

```javascript
// Plausible:
plausible('Test Event', {props: {test: 'value'}})

// Google Analytics:
gtag('event', 'test_event', {'test': 'value'})
```

### 3. Check Network Tab

1. Open Developer Tools (F12)
2. Go to "Network" tab
3. Filter by "script" or search for "plausible" / "gtag"
4. Click a tracked button
5. You should see analytics requests

### 4. Verify in Dashboard

**Plausible:**
- Events appear within seconds
- Check "Realtime visitors" or "Events"

**Google Analytics:**
- Check "Realtime" reports
- Events may take 1-2 minutes to appear

## Troubleshooting

### Analytics Not Loading

**Check Environment Variables:**

```bash
# Make sure analytics is enabled
echo $ANALYTICS_ENABLED  # Should be 'true'

# Restart server after changing .env
uvicorn app.main:app --reload
```

**Check Browser Console:**
- Look for script loading errors
- Adblockers may block analytics (expected)

### Events Not Tracking

**Verify Event Code:**
- Check button `onclick` attributes in HTML
- Test with browser console (see Testing section)

**Check Plausible Dashboard:**
- Make sure domain matches exactly
- Check "Settings" → "Visibility" (public or private)

**Check Google Analytics:**
- Verify Measurement ID is correct
- Make sure cookies are accepted
- Check "DebugView" in GA4

### Cookie Banner Not Appearing

**For Google Analytics:**
- Make sure `ANALYTICS_PROVIDER=google` in `.env`
- Verify `cookie-banner.html` is included in template
- Clear browser cookies and refresh
- Check browser console for JavaScript errors

### Plausible Shows No Data

**Common Issues:**
1. **Domain Mismatch**: `ANALYTICS_DOMAIN` must exactly match the domain in Plausible dashboard
2. **Localhost Filtering**: Plausible Cloud filters localhost by default
3. **Adblocker**: Disable adblockers for testing
4. **Script URL**: Verify `ANALYTICS_SCRIPT_URL` is correct

### Google Analytics Shows No Data

**Common Issues:**
1. **Wrong Measurement ID**: Double-check `ANALYTICS_ID`
2. **Cookies Declined**: Make sure to click "Accept" on cookie banner
3. **Ad Blocker**: Disable for testing
4. **Data Stream**: Verify web data stream is configured in GA4

## Advanced Configuration

### Custom Events

To add new custom events, edit the template and add:

**Plausible:**

```html
<a href="/somewhere"
   onclick="if(window.plausible) plausible('Event Name', {props: {key: 'value'}})">
    Click Me
</a>
```

**Google Analytics:**

```html
<a href="/somewhere"
   onclick="if(window.gtag) gtag('event', 'event_name', {'key': 'value'})">
    Click Me
</a>
```

### Disable Analytics Temporarily

```bash
# In .env
ANALYTICS_ENABLED=false
```

Restart the server.

### Switch Providers

```bash
# Switch to Google Analytics
ANALYTICS_PROVIDER=google
ANALYTICS_ID=G-XXXXXXXXXX

# Or switch to Plausible
ANALYTICS_PROVIDER=plausible
ANALYTICS_DOMAIN=yourdomain.com
```

Restart the server.

## Resources

### Plausible
- Documentation: https://plausible.io/docs
- Self-hosting: https://plausible.io/docs/self-hosting
- API: https://plausible.io/docs/stats-api
- Privacy Policy: https://plausible.io/privacy

### Google Analytics
- Documentation: https://support.google.com/analytics/
- GA4 Setup: https://support.google.com/analytics/answer/9304153
- Event Tracking: https://support.google.com/analytics/answer/9267735
- Privacy: https://support.google.com/analytics/answer/6004245

## Support

If you have questions or issues:
1. Check this documentation
2. Review the Troubleshooting section
3. Check your analytics provider's documentation
4. Open an issue on GitHub

---

**Last Updated**: 2025-11-17
