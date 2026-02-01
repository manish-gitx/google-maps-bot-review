# Approach: Browser Automation + AI CAPTCHA Solver

## What Is This?

Automate a real browser (Playwright/Puppeteer) with stealth patches to log into Gmail accounts and submit Google Maps reviews. When CAPTCHAs appear, an AI-powered solver handles them automatically.

---

## Technology Stack

```
Language:        Python / Node.js
Browser Driver:  Playwright + stealth plugin
CAPTCHA Solver:  2Captcha / Anti-Captcha / CapSolver / custom AI model
AI Agent:        GPT-4 Vision / Claude Vision / custom CNN model
Proxy:           Residential rotating proxies
Anti-detect:     Multilogin / GoLogin / Playwright-stealth
```

---

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      MAIN ORCHESTRATOR                          │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │ Account  │   │  Proxy   │   │ Browser  │   │  Review  │    │
│  │ Manager  │   │ Rotator  │   │ Launcher │   │ Composer │    │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘    │
│       │              │              │              │            │
│       ▼              ▼              ▼              ▼            │
│  Loads email/    Assigns a      Launches         Generates     │
│  password from   residential    Playwright       unique review │
│  accounts.json   proxy per      with stealth     text per      │
│                  session        plugins          account       │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   CAPTCHA SOLVER LAYER                    │   │
│  │                                                          │   │
│  │  CAPTCHA detected? ──YES──► Identify type:               │   │
│  │       │                     │                            │   │
│  │       NO                    ├─► v2 checkbox → solver API │   │
│  │       │                     ├─► v2 image   → AI vision   │   │
│  │       ▼                     ├─► v3 invisible → behavior  │   │
│  │    Continue                 │    simulation (best effort) │   │
│  │    normally                 └─► phone verify → SMS API   │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   RESULT TRACKER                          │   │
│  │                                                          │   │
│  │  Log: account, place, rating, status (success/fail),     │   │
│  │       CAPTCHA type encountered, solve time, proxy used   │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Execution Flow

```
START
  │
  ├─1► Load account from accounts.json
  │      { "email": "user@gmail.com", "password": "..." }
  │
  ├─2► Assign residential proxy
  │      Rotate per session to avoid IP correlation
  │
  ├─3► Launch Playwright browser with stealth
  │      │
  │      ├─► Apply stealth plugin patches:
  │      │     - Remove navigator.webdriver flag
  │      │     - Fake chrome.runtime
  │      │     - Spoof navigator.plugins array
  │      │     - Randomize canvas fingerprint
  │      │     - Fake WebGL vendor/renderer
  │      │     - Set realistic screen resolution
  │      │     - Randomize User-Agent
  │      │
  │      └─► Load unique browser profile (cookies, localStorage)
  │
  ├─4► Navigate to accounts.google.com
  │      │
  │      ├─► Type email with human-like delays (80-200ms/char, random)
  │      ├─► Click "Next"
  │      ├─► Wait 1-3 seconds (human pause)
  │      ├─► Type password with delays
  │      └─► Click "Next"
  │            │
  │            ├─► [CAPTCHA v2] ──────────────────────────────┐
  │            │                                               │
  │            │   ┌───────────────────────────────────────┐   │
  │            │   │  AI CAPTCHA SOLVER ACTIVATES           │   │
  │            │   │                                       │   │
  │            │   │  1. Extract sitekey from page HTML    │   │
  │            │   │  2. Send to 2Captcha/CapSolver API    │   │
  │            │   │  3. Wait for solution (15-45 sec)     │   │
  │            │   │  4. Receive g-recaptcha-response      │   │
  │            │   │  5. Inject token into page DOM        │   │
  │            │   │  6. Submit the form                   │   │
  │            │   │                                       │   │
  │            │   │  If IMAGE challenge:                  │   │
  │            │   │  1. Screenshot the grid               │   │
  │            │   │  2. Send to AI Vision model           │   │
  │            │   │  3. AI returns tile positions         │   │
  │            │   │  4. Click identified tiles            │   │
  │            │   │  5. Click "Verify"                    │   │
  │            │   └───────────────────────────────────────┘   │
  │            │                                               │
  │            ├─► [CAPTCHA v3 invisible] ─────────────────────┤
  │            │                                               │
  │            │   ┌───────────────────────────────────────┐   │
  │            │   │  BEHAVIOR SIMULATION (best effort)     │   │
  │            │   │                                       │   │
  │            │   │  - Random mouse curves (Bezier paths) │   │
  │            │   │  - Hover over random elements         │   │
  │            │   │  - Scroll up/down naturally           │   │
  │            │   │  - Click non-target areas first       │   │
  │            │   │  - Wait 10-30 sec before action       │   │
  │            │   │                                       │   │
  │            │   │  ⚠️  SUCCESS RATE: ~30-40%            │   │
  │            │   │  This is the weakest link.            │   │
  │            │   └───────────────────────────────────────┘   │
  │            │                                               │
  │            ├─► [2FA / Phone verify] ───────────────────────┤
  │            │                                               │
  │            │   ┌───────────────────────────────────────┐   │
  │            │   │  SMS VERIFICATION SERVICE              │   │
  │            │   │                                       │   │
  │            │   │  1. Request number from SMS API       │   │
  │            │   │     (sms-activate.org, 5sim.net)      │   │
  │            │   │  2. Enter number on Google page       │   │
  │            │   │  3. Poll SMS API for incoming code    │   │
  │            │   │  4. Enter code on Google page         │   │
  │            │   │                                       │   │
  │            │   │  Cost: $0.10-0.50 per number          │   │
  │            │   │  Risk: Numbers get recycled/flagged   │   │
  │            │   └───────────────────────────────────────┘   │
  │            │                                               │
  │            └─► [SUCCESS] ──► Logged in ◄───────────────────┘
  │
  ├─5► Navigate to Google Maps place
  │      │
  │      ├─► Go to: maps.google.com/maps/place?q=place+name
  │      ├─► Or search: type place name in search bar
  │      └─► Wait for place details to load
  │
  ├─6► Click "Write a Review"
  │      │
  │      ├─► Scroll to reviews section (natural scroll)
  │      ├─► Click star rating (randomize: 4-5 stars mostly)
  │      ├─► Click text input area
  │      ├─► Type review with human-like patterns:
  │      │     - Variable speed (60-250ms per character)
  │      │     - Occasional pauses (thinking)
  │      │     - Random typos + corrections (backspace)
  │      │     - Unique text per review (AI-generated)
  │      └─► Click "Post"
  │
  ├─7► Verify review posted
  │      │
  │      ├─► Check for success confirmation
  │      ├─► Log result to results.json
  │      └─► Screenshot for proof
  │
  ├─8► Cleanup
  │      │
  │      ├─► Save cookies/session for this account
  │      ├─► Close browser
  │      └─► Wait random delay (5-30 min) before next account
  │
  └─9► REPEAT from step 1 with next account
```

---

## CAPTCHA Types - What You'll Face

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAPTCHA TYPES ON GOOGLE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TYPE 1: reCAPTCHA v2 (checkbox)                                │
│  ┌──────────────────┐                                           │
│  │  ☐ I'm not a     │  Click → might pass instantly             │
│  │    robot          │  OR triggers image challenge (Type 2)     │
│  └──────────────────┘                                           │
│  AI Solvable? ✅ YES - send sitekey to solver API               │
│  Solve time:  15-45 seconds                                     │
│  Cost:        $1-3 per 1000                                     │
│  Success:     85-95%                                            │
│                                                                 │
│─────────────────────────────────────────────────────────────────│
│                                                                 │
│  TYPE 2: reCAPTCHA v2 (image grid)                              │
│  ┌──────┬──────┬──────┐                                         │
│  │  🚗  │  🌳  │  🚦  │  "Select all squares with               │
│  ├──────┼──────┼──────┤   traffic lights"                       │
│  │  🏠  │  🚦  │  🐕  │                                         │
│  ├──────┼──────┼──────┤  May require multiple rounds             │
│  │  🚦  │  🌊  │  🚗  │  (new images load after selection)       │
│  └──────┴──────┴──────┘                                         │
│  AI Solvable? ✅ YES - screenshot → AI vision model             │
│  Solve time:  20-60 seconds                                     │
│  Cost:        $2-5 per 1000                                     │
│  Success:     70-85%                                            │
│                                                                 │
│─────────────────────────────────────────────────────────────────│
│                                                                 │
│  TYPE 3: reCAPTCHA v3 (INVISIBLE) ⚠️  BIGGEST THREAT           │
│                                                                 │
│  There is NO visual element. Nothing to click. Nothing to see.  │
│  It runs silently in the background on every page load.         │
│                                                                 │
│  What it tracks:                                                │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ - Mouse movement patterns (speed, curves, hesitation)  │     │
│  │ - Scroll behavior (speed, direction, stopping points)  │     │
│  │ - Typing cadence (speed variance, error patterns)      │     │
│  │ - Click patterns (accuracy, timing between clicks)     │     │
│  │ - Page interaction time (how long before first action)  │     │
│  │ - Tab focus/blur events (did you switch tabs?)         │     │
│  │ - Touch vs mouse (mobile detection)                    │     │
│  │ - Browser history/cookies (is this a fresh session?)   │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                 │
│  Scoring: 0.0 (definitely bot) ──── 1.0 (definitely human)     │
│           < 0.3 = blocked    0.3-0.7 = suspicious   > 0.7 = ok │
│                                                                 │
│  AI Solvable? ❌ NO - nothing to solve, it's behavioral         │
│  Workaround:  Simulate human behavior (30-40% success)          │
│  This is why this approach has a 50-70% detection rate.         │
│                                                                 │
│─────────────────────────────────────────────────────────────────│
│                                                                 │
│  TYPE 4: Account verification ("Verify it's you")               │
│  ┌────────────────────────────────────────────────────┐         │
│  │  Google may ask:                                    │         │
│  │  - Enter phone number for SMS code                  │         │
│  │  - Confirm recovery email                           │         │
│  │  - "Tap Yes on your other device"                   │         │
│  │  - Answer security questions                        │         │
│  └────────────────────────────────────────────────────┘         │
│  AI Solvable? ❌ NO - needs real phone/device access            │
│  Workaround:  SMS verification services ($0.10-0.50/number)    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Deep Pros

| # | Pro | Why It Matters |
|---|-----|----------------|
| 1 | **Solves visual CAPTCHAs** | reCAPTCHA v2 image puzzles are solved at 70-95% accuracy. This unblocks the login flow that stops basic browser automation cold. |
| 2 | **Fully automated pipeline** | Once configured: account → proxy → login → solve CAPTCHA → navigate → review → log → next. Zero manual intervention. |
| 3 | **Scales with budget** | More money = more CAPTCHA solves = more proxies = more throughput. 2Captcha handles 10,000+ solves/minute globally. |
| 4 | **Solver fallback chains** | AI model fails? Fall back to 2Captcha. 2Captcha slow? Try Anti-Captcha. Multiple redundancy layers. |
| 5 | **Stealth plugins patch 20+ vectors** | `playwright-stealth` fixes: navigator.webdriver, chrome.runtime, plugin array, languages, permissions, iframe contentWindow, etc. |
| 6 | **Anti-detect browsers** | Multilogin/GoLogin give each account a unique, persistent fingerprint: canvas hash, WebGL renderer, fonts, screen size, timezone, language. Looks like separate real devices. |
| 7 | **Lower resource usage** | Each browser = 200-500MB RAM. Can run 10-20 instances on a single $50/mo VPS. Much cheaper than mobile emulation. |
| 8 | **Large community** | Playwright/Puppeteer have massive ecosystems. When something breaks, someone on GitHub/StackOverflow has already fixed it. |
| 9 | **Easy to debug** | Run in headed mode, watch the browser, see exactly where it fails. Add screenshots at every step. |
| 10 | **Review text generation** | Can integrate LLMs to generate unique, natural-sounding review text per account. Harder for Google's NLP to flag as template. |

---

## Deep Cons

| # | Con | Why It's a Problem |
|---|-----|--------------------|
| 1 | **reCAPTCHA v3 is unsolvable** | The invisible behavioral scoring has NO visual challenge to solve. AI CAPTCHA services are useless. You can simulate mouse/scroll behavior but Google's ML (trained on billions of sessions) catches fakes ~60-70% of the time. This is the **single biggest failure point**. |
| 2 | **Cost per review is high** | CAPTCHA: $1-5/1000. Proxies: $5-15/GB. Anti-detect: $100+/mo. SMS: $0.10-0.50/number. For 100 reviews: $142-240. And 65-80% get removed. Effective cost per *surviving* review: $4-12. |
| 3 | **Token expiration race** | CAPTCHA tokens expire in ~120 seconds. If solver takes 60s and your page is slow to load, the token is dead. Re-solve = more cost, more time, more suspicion. |
| 4 | **Google adapts weekly** | Google's anti-abuse team specifically monitors solver services. They buy accounts on 2Captcha, study solve patterns, and train detectors against them. Your working setup breaks regularly. |
| 5 | **Multi-layer CAPTCHA stacking** | Google can serve: v2 checkbox → v2 image → v3 invisible → phone verify — all in one login flow. Solving one doesn't mean you pass the next. Each layer multiplies your failure rate. |
| 6 | **Stealth detection arms race** | `puppeteer-stealth` was fingerprinted by Google in 2023. Fixed. Detected again in 2024. Fixed again. Detected in 2025. You're always one step behind. |
| 7 | **Browser fingerprint inconsistencies** | If your spoofed fingerprint says "macOS + Retina display" but your User-Agent says "Windows Chrome" and your timezone is UTC — these mismatches trigger heuristic flags. Keeping everything consistent is hard. |
| 8 | **Login DOM changes** | Google changes login page structure every few weeks. Button IDs, form names, CSS classes — all change. Your selectors break and you scramble to fix them. |
| 9 | **Session isolation is complex** | Each account needs: unique cookies, localStorage, IndexedDB, separate proxy, separate fingerprint. One leak between sessions (shared cookie, same canvas hash) links accounts together → mass ban. |
| 10 | **Legal liability** | CAPTCHA bypassing may independently violate CFAA (Computer Fraud and Abuse Act). Combined with fake reviews (FTC violation), you face two separate legal risks. |
| 11 | **Silent removal** | Reviews post "successfully" but are invisible to other users. You don't know they're gone unless you check from a different, unrelated account. Creates false sense of success. |
| 12 | **Account warming required** | Fresh accounts that immediately review get filtered. Each account needs days/weeks of "normal" activity (search, browse, watch YouTube) before reviews stick. This multiplies time and cost enormously. |

---

## Cost Breakdown

```
┌─────────────────────────────────────────────────────────────┐
│                COST ANALYSIS: 100 REVIEWS                    │
├─────────────────────────────────────┬───────────────────────┤
│ Component                           │ Cost                  │
├─────────────────────────────────────┼───────────────────────┤
│ Residential proxies (10 GB)         │ $50-150               │
│ CAPTCHA solving (~200 challenges)   │ $2-10                 │
│ SMS verification (100 numbers)      │ $10-50                │
│ Anti-detect browser (monthly)       │ $100-200              │
│ VPS/Server (monthly)                │ $20-50                │
│ AI review text generation           │ $5-15                 │
├─────────────────────────────────────┼───────────────────────┤
│ TOTAL                               │ $187-475              │
│ Per review submitted                │ $1.87-4.75            │
├─────────────────────────────────────┼───────────────────────┤
│ Reviews that survive ML filtering   │ ~20-35 out of 100     │
│ Effective cost per SURVIVING review │ $5.34-23.75           │
└─────────────────────────────────────┴───────────────────────┘
```

---

## Ban Reasons Specific to This Approach

```
┌────┬─────────────────────────────┬───────────────────────────────────────────┐
│ #  │ Ban Trigger                 │ Details                                   │
├────┼─────────────────────────────┼───────────────────────────────────────────┤
│  1 │ Stealth plugin fingerprint  │ Google detects known patches from         │
│    │                             │ playwright-stealth / puppeteer-stealth.   │
│    │                             │ They maintain a blacklist of code         │
│    │                             │ patterns these plugins inject.            │
├────┼─────────────────────────────┼───────────────────────────────────────────┤
│  2 │ CAPTCHA solver token pattern│ Tokens from 2Captcha/Anti-Captcha have   │
│    │                             │ statistical timing patterns (solve time   │
│    │                             │ clusters) that differ from real humans.   │
├────┼─────────────────────────────┼───────────────────────────────────────────┤
│  3 │ reCAPTCHA v3 low score      │ Simulated mouse/scroll behavior doesn't  │
│    │                             │ match Google's model of human behavior.   │
│    │                             │ Score falls below 0.3 → action blocked.  │
├────┼─────────────────────────────┼───────────────────────────────────────────┤
│  4 │ CDP (Chrome DevTools Proto) │ Playwright/Puppeteer use CDP to control  │
│    │                             │ Chrome. Google detects CDP connections    │
│    │                             │ via Runtime.evaluate artifacts and other  │
│    │                             │ protocol-level signals.                  │
├────┼─────────────────────────────┼───────────────────────────────────────────┤
│  5 │ Proxy IP reputation         │ Even "residential" proxies get flagged   │
│    │                             │ when they appear in abuse databases      │
│    │                             │ (IP2Proxy, MaxMind GeoIP). Cheap proxy   │
│    │                             │ providers reuse flagged IPs.             │
├────┼─────────────────────────────┼───────────────────────────────────────────┤
│  6 │ Canvas/WebGL mismatch       │ Spoofed canvas hash doesn't match the   │
│    │                             │ expected output for the claimed GPU/OS   │
│    │                             │ combination. Google cross-validates.     │
├────┼─────────────────────────────┼───────────────────────────────────────────┤
│  7 │ Cookie freshness            │ Real Chrome users have months of Google  │
│    │                             │ cookies (NID, SID, HSID, etc.). A fresh  │
│    │                             │ profile with zero cookies screams "new   │
│    │                             │ automation session."                     │
├────┼─────────────────────────────┼───────────────────────────────────────────┤
│  8 │ Timing correlation          │ Multiple accounts logging in at regular  │
│    │                             │ intervals (every 15 min) from similar    │
│    │                             │ IPs within the same hour = coordinated   │
│    │                             │ automation.                              │
├────┼─────────────────────────────┼───────────────────────────────────────────┤
│  9 │ Review text NLP analysis    │ Even AI-generated text has patterns.     │
│    │                             │ Google's models detect: over-politeness, │
│    │                             │ unusual vocabulary, lack of specific     │
│    │                             │ personal details, similar sentence       │
│    │                             │ structure across "different" reviewers.  │
├────┼─────────────────────────────┼───────────────────────────────────────────┤
│ 10 │ No prior Maps activity      │ Account has zero navigation history,    │
│    │                             │ zero saved places, zero searches.       │
│    │                             │ First action is writing a review.       │
│    │                             │ Obvious sockpuppet.                     │
├────┼─────────────────────────────┼───────────────────────────────────────────┤
│ 11 │ Retroactive batch analysis  │ Google runs weekly ML jobs that cross-  │
│    │                             │ reference ALL reviews for a business.   │
│    │                             │ Even if individual reviews pass, the    │
│    │                             │ cluster pattern (timing, rating, style) │
│    │                             │ triggers removal of the entire batch.   │
├────┼─────────────────────────────┼───────────────────────────────────────────┤
│ 12 │ Account age too young       │ Accounts less than 30 days old have     │
│    │                             │ reviews weighted near zero. Even if not  │
│    │                             │ removed, they don't affect the rating.  │
└────┴─────────────────────────────┴───────────────────────────────────────────┘
```

