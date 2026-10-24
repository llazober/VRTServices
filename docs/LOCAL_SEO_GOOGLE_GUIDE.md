# 📍 Local SEO Setup Guide for VRT Services (Google)

> Saved: 2026-10-21 (Eastern Time). Use the checkboxes to track progress.

---

## Step 1: Google Business Profile (GBP), the most important step
- [ ] Go to **business.google.com** and sign in with a business Google account (not a personal one).
- [ ] **Business name:** exact legal or brand name ("VRT Services"). Do NOT add keywords to the name; Google can suspend profiles that do.
- [ ] **Primary category:** *Tax Preparation Service*
- [ ] **Secondary categories** (only ones you offer): *Accountant*, *Bookkeeping Service*, *Payroll Service*, *Tax Consultant*
- [ ] **Address:** real office address. If you serve clients only at their location, hide the address and set a **service area** (cities or counties).
- [ ] **Phone:** local number (not toll-free). **Website:** `https://vrtservices12.com`
- [ ] **Verify:** postcard, phone call, or video (about 5–14 days).

### Complete the profile fully
- [ ] Hours, including extended tax-season hours (Jan–Apr) and holiday hours
- [ ] Services, each with a short description: Individual 1040, S-Corp/LLC returns, Bookkeeping, Payroll, ITIN, IRS letters, etc.
- [ ] Attributes: "Language: Spanish", "Online appointments", "Women-owned" or "Latino-owned" (only if true)
- [ ] Description (750 characters): what you do, cities served, years in business
- [ ] At least 10 real photos: outside of the office, inside, team, logo, cover image
- [ ] Booking/appointment link

---

## Step 2: NAP consistency (Name, Address, Phone)
NAP must be **identical everywhere**, character for character. For example, pick either "Suite 200" or "Ste 200" and use the same form on every listing.

| Priority | Site | Done |
|---|---|---|
| ⭐ Must have | Bing Places (can import your Google profile) | [ ] |
| ⭐ Must have | Apple Business Connect | [ ] |
| ⭐ Must have | Yelp | [ ] |
| ⭐ Must have | Facebook Business Page | [ ] |
| ⭐ Must have | BBB | [ ] |
| Industry | IRS Directory of Preparers (if you have a PTIN with credentials) | [ ] |
| Industry | NATP, Thumbtack, Angi, Expertise.com | [ ] |
| Local | Chamber of Commerce, local Hispanic business associations, city directories | [ ] |
| Data aggregators | Data Axle, Neustar Localeze, Foursquare (these feed hundreds of other sites) | [ ] |

---

## Step 3: Website changes (vrtservices12.com), code tasks
- [ ] Title and meta description per page. Example title: `Tax Preparation in [City], [State] | VRT Services`
- [ ] Footer with the exact NAP plus an embedded Google Map
- [ ] `LocalBusiness` / `AccountingService` JSON-LD schema on the homepage (name, address, geo coordinates, hours, phone, `sameAs` links to Google, Yelp and Facebook)
- [ ] One page per service: `/tax-preparation`, `/bookkeeping`, `/payroll`
- [ ] City landing pages (`/tax-preparation-[city]`), each with unique content; copying the same text with a different city name can hurt rankings
- [ ] Spanish versions (`/es/...`) with `hreflang` tags, if you serve Spanish-speaking clients
- [ ] Mobile-friendly, fast loading, HTTPS, `sitemap.xml`, `robots.txt`

### Example schema (fill in your real data)
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "AccountingService",
  "name": "VRT Services",
  "url": "https://vrtservices12.com",
  "telephone": "+1-XXX-XXX-XXXX",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "STREET",
    "addressLocality": "CITY",
    "addressRegion": "STATE",
    "postalCode": "ZIP",
    "addressCountry": "US"
  },
  "geo": { "@type": "GeoCoordinates", "latitude": 0.0, "longitude": 0.0 },
  "openingHours": "Mo-Fr 09:00-18:00",
  "areaServed": ["CITY 1", "CITY 2"],
  "sameAs": [
    "https://g.page/YOUR-PROFILE",
    "https://www.facebook.com/YOUR-PAGE",
    "https://www.yelp.com/biz/YOUR-BIZ"
  ]
}
</script>
```

---

## Step 4: Google tools
- [ ] **Google Search Console:** verify the domain with a DNS TXT record and submit `sitemap.xml`
- [ ] **Google Analytics 4:** add tracking for calls, form submissions and bookings
- [ ] **UTM link on the Google profile** so Analytics shows which visits came from it. Use this as the profile's website link:
  `https://vrtservices12.com/?utm_source=google&utm_medium=organic&utm_campaign=gbp`

---

## Step 5: Reviews, the biggest factor for ranking in the map results
- [ ] Get your direct review link from the Google profile under **"Ask for reviews"**
- [ ] Ask every client after filing (could be automated after e-signature Step 4 is complete)
- [ ] Reply to every review within 48 hours, including negative ones. Never mention tax details in a reply (IRS § 7216 privacy)
- [ ] Don't offer incentives for reviews and don't post fake ones; Google prohibits both
- Target: 4–8 new reviews per month, more during tax season

---

## Step 6: Ongoing work
- [ ] **Weekly:** Google profile post (deadline reminders, tax tips, offers)
- [ ] **Weekly:** Reply to reviews and Q&A (post and answer common questions yourself)
- [ ] **Monthly:** Add new photos
- [ ] **Monthly:** Review Google profile Performance (calls, direction requests, clicks) and Search Console queries
- [ ] **Ongoing:** Local backlinks: sponsor local events, write guest articles for community sites, partner with realtors, insurance agents or banks
- Optional rank trackers: BrightLocal, Local Falcon

---

## Timeline
| Week | Action |
|---|---|
| 1 | Create the Google profile, request verification, set up Search Console and Analytics |
| 2 | Finish the profile (photos, services); website changes (schema, NAP, meta tags) |
| 3–4 | Build the directory listings and start asking for reviews |
| Ongoing | Weekly posts, reviews, monthly reporting |

Expect visible map-ranking results in about **2–3 months**.

---

## Info needed before starting
- [ ] Office address, or the cities you serve
- [ ] Whether clients come to the office or you serve them remotely
- [ ] Whether you want Spanish SEO
