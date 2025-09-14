# Google Maps API Setup

To enable Google Maps integration for location search with coordinates, you need to set up the Google Maps API.

## Steps:

1. **Go to Google Cloud Console**: https://console.cloud.google.com/

2. **Create a new project or select existing project**

3. **Enable the following APIs**:
   - Places API
   - Geocoding API
   - Maps JavaScript API (optional, for future map display)

4. **Create API Key**:
   - Go to "Credentials" in the left sidebar
   - Click "Create Credentials" → "API Key"
   - Copy the generated API key

5. **Restrict the API Key** (recommended for production):
   - Click on the created API key
   - Under "Application restrictions", select "HTTP referrers"
   - Add your domain (e.g., `localhost:3000/*`, `yourdomain.com/*`)
   - Under "API restrictions", select "Restrict key" and choose:
     - Places API
     - Geocoding API

6. **Add to Environment Variables**:
   
   In your `.env.local` file (client side):
   ```
   NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your_api_key_here
   ```

   In your `.env` file (server side, if needed):
   ```
   GOOGLE_MAPS_API_KEY=your_api_key_here
   ```

## Fallback

If Google Maps API is not configured, the system will automatically fall back to Mapbox (if `NEXT_PUBLIC_MAPBOX_TOKEN` is available).

## Features Enabled

With Google Maps API configured, users can:
- Search for locations with autocomplete
- Get precise latitude/longitude coordinates
- Select from suggested places
- Store location data with coordinates in MongoDB

## Cost Considerations

- Google Places API has usage limits and costs
- Autocomplete requests: $0.00283 per session
- Place Details requests: $0.017 per request
- Geocoding requests: $0.005 per request

Consider implementing usage limits or caching for production use.
