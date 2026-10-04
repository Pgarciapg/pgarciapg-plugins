---
description: Deploy MVP to Vercel with production-ready configuration
argument-hint: "[preview|production]"
---

# MVP Ship

Deploy the MVP to Vercel with proper configuration.

## Environment: $ARGUMENTS

Deploy to the environment named above, `preview` or `production`. If none was given, use `preview`.

## Pre-flight Checks

### 1. Verify Project Structure
- Confirm this is a Next.js project (check for next.config.ts/mjs)
- Check for package.json
- Verify .env.local exists with Supabase credentials

### 2. Import Verification (CRITICAL)
Before deploying, check that all imported files are tracked by git:
```bash
git status
```
- Look for untracked files in `src/` that might be imported by committed code
- Uncommitted imports cause silent production crashes — the build passes locally because the file exists, but fails on Vercel where only committed files are deployed
- Run `git show HEAD:<file>` for any suspicious imports to confirm tracking

### 3. CSS Import Order
Check `src/app/globals.css`:
- `@import url(...)` statements MUST come before `@tailwind` directives
- Wrong order causes silent styling failures in production

### 4. Build Check
```bash
npm run build
```
If build fails:
- Delete `.next/dev/lock` if present (leftover from crash)
- Fix TypeScript errors
- Check for missing environment variables

### 5. Check Git Status
```bash
git status
```
- If uncommitted changes exist, ask user if they want to commit first
- Always `git pull` before committing when remote exists
- Suggest meaningful commit message based on changes

## Deployment Steps

### Step 1: Ensure Vercel CLI
Check if Vercel CLI is installed:
```bash
which vercel || npm install -g vercel
```

### Step 2: Link Project (if not linked)
```bash
vercel link
```

**Gotcha**: If the directory name has spaces, use `vercel link --project kebab-case-name`.

Guide user through:
- Select or create Vercel project
- Confirm settings

### Step 3: Set Environment Variables

Check if env vars are set on Vercel:
```bash
vercel env ls
```

If missing, set them using the pipe pattern (--yes flag does NOT work on `vercel env add`):
```bash
printf 'your-supabase-url' | vercel env add NEXT_PUBLIC_SUPABASE_URL production
printf 'your-anon-key' | vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
```

For production, also set:
- `NEXT_PUBLIC_SITE_URL` — Set to production domain

If project uses AI Gateway:
- Run `vercel env pull` to get OIDC credentials (auto-provisioned, no manual API keys needed)

### Step 4: Deploy

For preview:
```bash
vercel
```

For production:
```bash
vercel --prod
```

## Post-Deployment Verification

After successful deployment:

```
Deployed successfully!

Deployment URL: [url from vercel output]

MANDATORY: Click through the deployed site to verify:
[ ] Home page loads correctly
[ ] Login/signup flow works
[ ] Dashboard loads after login
[ ] All protected routes redirect properly
[ ] Styles render correctly (no dark mode bleed, no broken CSS)
[ ] Mobile viewport looks correct
[ ] No console errors in browser DevTools

Supabase configuration:
[ ] Add deployment URL to Supabase Auth settings:
  - Go to Authentication > URL Configuration
  - Add Site URL: [production url]
  - Add Redirect URLs: [production url]/**

Domain setup (if needed):
[ ] Add custom domain in Vercel dashboard
[ ] Update Supabase redirect URLs with custom domain
[ ] Update NEXT_PUBLIC_SITE_URL env var
```

**IMPORTANT**: Don't just check the build passes — actually test the experience. Navigate the full user flow. Bugs like invisible content, broken auth redirects, and styling issues are only caught by clicking through the UI.

## Troubleshooting Common Issues

### Build Fails on Vercel but Passes Locally
- **Untracked imports**: A file exists locally but isn't committed to git
- **Missing env vars**: Set them with `vercel env add`
- **Different Node version**: Check `engines` in package.json

### Auth Not Working
- Verify Supabase URL Configuration includes the deployment URL
- Check redirect URLs in Supabase dashboard
- Ensure proxy.ts is in the right location (`src/proxy.ts` with --src-dir)
- Verify cookies are being set properly

### 500 Errors
- Check Vercel function logs: `vercel logs [deployment-url]`
- Verify environment variables are set correctly
- Check Supabase service is running

### Styles Look Wrong
- Check CSS import order in globals.css
- Verify Tailwind v4 light-mode fix is in place
- Check for `prefers-color-scheme` interference

## Rollback

If something goes wrong:
```bash
vercel rollback
```

Or from dashboard: Vercel Dashboard > Deployments > ... > Rollback

## Next Steps

After first successful deployment:
1. Set up custom domain (if needed)
2. Configure Supabase production settings
3. Enable Vercel Analytics (zero-config: `npm install @vercel/analytics`)
4. Consider adding error tracking (Sentry)
5. Set up AI Gateway if AI features are planned (`vercel env pull` for OIDC)
