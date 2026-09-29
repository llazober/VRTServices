# User Customizations & Rules

## Deployment Rule
- The user will handle all live deployments manually.
- Do NOT poll, wait for, or run automated background checks for live deployments. Once changes are committed and pushed to git, complete the task response immediately without waiting or polling.

## Resend Email & Domain Reference (Method 1)
- Refer to [RESEND_CUSTOM_DOMAINS_GUIDE.md](file:///d:/VRTServices/docs/RESEND_CUSTOM_DOMAINS_GUIDE.md) for custom domain DKIM, SPF, DMARC, and per-portal webhook routing setup.

## Eastern Time (NY) Standard Rule
- ALWAYS use US Eastern Time (`America/New_York`) for all timestamp generation, date/time fields, database defaults/queries, and UI date displays across all modules in the application.


