# Approach: Mobile Emulation / Appium

## What Is This?

Instead of automating a web browser, you automate the **Google Maps Android app** running inside Android emulators. Appium sends tap/swipe/type commands to the emulator just like a real finger would. Each emulator is configured as a unique "device" with its own identity.

---

## Technology Stack

```
Language:         Python / Java / Node.js
Automation:       Appium 2.0 + UiAutomator2 driver
Emulator:         Android Studio AVD / Genymotion / BlueStacks
Android Version:  Android 12-14 (API 31-34)
Google Maps APK:  Sideloaded (pinned version) or Play Store
Proxy:            Proxifier / iptables-level proxy per emulator
GPS Spoofing:     ADB geo fix / mock location app
SafetyNet Bypass: Magisk + Play Integrity Fix module
Fingerprint:      Different IMEI, Android ID, build.prop per instance
```

---

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      MAIN ORCHESTRATOR                          │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │ Account  │   │ Device   │   │ Emulator │   │  Review  │    │
│  │ Manager  │   │ Identity │   │ Pool     │   │ Composer │    │
│  │          │   │ Spoofing │   │ Manager  │   │          │    │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘    │
│       │              │              │              │            │
│       ▼              ▼              ▼              ▼            │
│  Loads email/    Generates     Boots/recycles   Generates     │
│  password from   unique IMEI,  emulator         unique review │
│  accounts.json   Android ID,   instances with   text per      │
│                  build.prop,   Xvfb display     account       │
│                  MAC address                                   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  SAFETYNET BYPASS LAYER                   │   │
│  │                                                          │   │
│  │  Before Google account login:                            │   │
│  │  1. Boot with Magisk (systemless root)                   │   │
│  │  2. Install Play Integrity Fix module                    │   │
│  │  3. Hide Magisk from Google Play Services                │   │
│  │  4. Pass SafetyNet basic + device integrity checks       │   │
│  │                                                          │   │
│  │  ⚠️  Hardware attestation CANNOT be bypassed             │   │
│  │     (requires real device hardware keys)                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  GPS SPOOFING LAYER                       │   │
│  │                                                          │   │
│  │  Set fake coordinates near the target business:          │   │
│  │  adb emu geo fix <longitude> <latitude>                  │   │
│  │                                                          │   │
│  │  Add slight randomization (±0.001 degrees) to avoid      │   │
│  │  all "visitors" appearing at exact same coordinates      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  RESULT TRACKER                           │   │
│  │                                                          │   │
│  │  Log: account, place, rating, status, device profile,    │   │
│  │       GPS coords used, proxy IP, app version, timestamps │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Execution Flow

```
START
  │
  ├─1► Create emulator with unique identity
  │      │
  │      ├─► Generate unique device properties:
  │      │     ┌────────────────────────────────────────────┐
  │      │     │  IMEI:          randomly generated (valid) │
  │      │     │  Android ID:    random 16-char hex         │
  │      │     │  Device Model:  Pixel 7 / Samsung S23 /    │
  │      │     │                 OnePlus 11 (rotate)        │
  │      │     │  Build.prop:    matching device firmware    │
  │      │     │  MAC Address:   random (valid OUI prefix)  │
  │      │     │  Serial:        random alphanumeric        │
  │      │     │  Screen:        1080x2400 / 1440x3200      │
  │      │     │  DPI:           420 / 560                  │
  │      │     └────────────────────────────────────────────┘
  │      │
  │      ├─► Configure proxy at OS level
  │      │     Route ALL traffic through residential proxy
  │      │     (not just browser — entire emulator)
  │      │
  │      └─► Set up SafetyNet bypass
  │            Flash Magisk → Install Play Integrity Fix
  │
  ├─2► Boot emulator
  │      │
  │      ├─► Start with Xvfb (virtual display) on server
  │      │   Or: run headless with -no-window flag
  │      │
  │      ├─► Wait for boot complete signal:
  │      │   adb wait-for-device
  │      │   adb shell getprop sys.boot_completed → "1"
  │      │
  │      └─► Boot time: 60-120 seconds
  │
  ├─3► Add Google Account to device
  │      │
  │      ├─► Navigate: Settings → Accounts → Add Account → Google
  │      │
  │      ├─► Appium taps through the flow:
  │      │     ┌────────────────────────────────────────────┐
  │      │     │  1. Tap "Google" account type              │
  │      │     │  2. Wait for login WebView to load         │
  │      │     │  3. Tap email field                        │
  │      │     │  4. Type email (with touch keyboard)       │
  │      │     │  5. Tap "Next"                             │
  │      │     │  6. Wait 2-5 seconds                       │
  │      │     │  7. Tap password field                     │
  │      │     │  8. Type password (with touch keyboard)    │
  │      │     │  9. Tap "Next"                             │
  │      │     └────────────────────────────────────────────┘
  │      │
  │      ├─► Possible blocks:
  │      │     │
  │      │     ├─► [CAPTCHA on mobile]
  │      │     │     Mobile uses different CAPTCHA than web.
  │      │     │     Usually simpler image challenges.
  │      │     │     Can use same solver API (screenshot → solve)
  │      │     │
  │      │     ├─► [DEVICE VERIFICATION]
  │      │     │     "Verify on your other device"
  │      │     │     ❌ BLOCKED unless you have a real device
  │      │     │     or another emulator already logged in
  │      │     │
  │      │     ├─► [PHONE VERIFICATION]
  │      │     │     SMS code required
  │      │     │     Use SMS verification service
  │      │     │
  │      │     └─► [SAFETYNET FAILURE]
  │      │           "This device is not recognized"
  │      │           Account addition blocked entirely
  │      │           Need to fix SafetyNet bypass
  │      │
  │      └─► Accept Terms → Account added
  │
  ├─4► Set fake GPS near target business
  │      │
  │      ├─► adb emu geo fix -73.9857 40.7484
  │      │   (example: near Empire State Building)
  │      │
  │      ├─► Add random offset: ±0.0005 to ±0.002 degrees
  │      │   (50-200 meters of natural variation)
  │      │
  │      └─► Maintain location for duration of session
  │          (sudden GPS jumps trigger location fraud detection)
  │
  ├─5► Open Google Maps app
  │      │
  │      ├─► adb shell am start -n com.google.android.apps.maps/...
  │      │
  │      ├─► Handle first-launch prompts:
  │      │     - "What's new" popup → dismiss
  │      │     - Location permission → "While using the app"
  │      │     - Notification permission → "Allow" or "Deny"
  │      │     - "Sign in" prompt → already signed in via device
  │      │
  │      └─► Wait for map to fully render (5-15 seconds)
  │
  ├─6► Search for target place
  │      │
  │      ├─► Tap search bar at top
  │      ├─► Type place name with realistic touch keyboard speed
  │      │   (150-400ms between taps, occasional wrong key + correction)
  │      ├─► Wait for autocomplete suggestions (1-3 sec)
  │      ├─► Tap the correct suggestion
  │      └─► Wait for place details card to slide up (2-5 sec)
  │
  ├─7► Submit review
  │      │
  │      ├─► Scroll down in place details (swipe up gesture)
  │      │   ┌────────────────────────────────────────────┐
  │      │   │  Appium swipe:                             │
  │      │   │  start: (540, 1800) → end: (540, 600)     │
  │      │   │  duration: 800-1200ms (natural speed)      │
  │      │   │  Wait 1-2 seconds between swipes           │
  │      │   └────────────────────────────────────────────┘
  │      │
  │      ├─► Find "Rate and review" section
  │      │
  │      ├─► Tap star rating
  │      │     Stars 1-5, randomly weight toward 4-5
  │      │     Occasionally give 3 stars for realism
  │      │
  │      ├─► Tap "Describe your experience" text field
  │      │
  │      ├─► Type review text
  │      │     ┌────────────────────────────────────────────┐
  │      │     │  Typing simulation on touch keyboard:      │
  │      │     │                                            │
  │      │     │  - Tap each key with slight position       │
  │      │     │    variance (±3-5 pixels from center)      │
  │      │     │  - Speed: 150-400ms between taps           │
  │      │     │  - Add pauses every 5-15 characters        │
  │      │     │    (simulating thinking)                   │
  │      │     │  - Occasional wrong key → backspace →      │
  │      │     │    correct key (2-5% error rate)           │
  │      │     │  - Some reviews: add a photo               │
  │      │     │    (push image via adb, attach in app)     │
  │      │     └────────────────────────────────────────────┘
  │      │
  │      └─► Tap "Post" button
  │            │
  │            ├─► [SUCCESS] → "Review posted" toast appears
  │            ├─► [BLOCKED] → "Can't post review" → account flagged
  │            └─► [CRASH]   → App force-closed → retry once
  │
  ├─8► Verify + Log
  │      │
  │      ├─► Take screenshot as proof
  │      ├─► Log result to results.json
  │      └─► Record: account, place, rating, text, GPS, timestamp
  │
  ├─9► Cleanup
  │      │
  │      ├─► Option A: Remove account, keep emulator
  │      │     Settings → Accounts → Remove Google account
  │      │     Wipe app data: adb shell pm clear com.google.android.apps.maps
  │      │
  │      └─► Option B: Destroy emulator, create fresh one
  │            More thorough but slower (+ 2 min boot time)
  │
  ├─10► Cooldown
  │      │
  │      └─► Wait 15-60 minutes before next review
  │          (random delay to avoid timing patterns)
  │
  └─11► REPEAT from step 1 with next account
```

---

## Deep Pros

| # | Pro | Why It Matters |
|---|-----|----------------|
| 1 | **No reCAPTCHA v3** | The Google Maps Android app does NOT use reCAPTCHA v3 (which is web-only JavaScript). This completely eliminates the single biggest blocker from browser automation. Mobile uses different, generally simpler verification. |
| 2 | **Different detection surface** | Google's web bot detection (navigator.webdriver, canvas fingerprinting, CDP detection, stealth plugin fingerprinting) does NOT apply to native Android apps. The detection systems are entirely separate teams/codebases at Google. |
| 3 | **Device-level identity is convincing** | Each emulator gets: unique IMEI, Android ID, build fingerprint, device model, serial number, MAC address. This is far more convincing than browser fingerprint spoofing because device IDs are hardware-level identifiers Google was designed to trust. |
| 4 | **GPS spoofing = location proximity** | Google heavily weights whether the reviewer was physically near the business. With GPS spoofing, every "reviewer" appears to have visited the location. This is a major trust signal that browser automation cannot replicate. |
| 5 | **Touch interactions are harder to distinguish** | Touch events (pressure, contact area, gesture velocity) on a native app are harder for Google to fingerprint vs. the highly-studied mouse movement patterns on web. |
| 6 | **Photos increase trust** | Easy to push photos to the emulator via `adb push` and attach them to reviews. Reviews with photos are weighted more heavily and filtered less aggressively. |
| 7 | **App caching behavior** | The Maps app caches map tiles, search history, and place data. Cached sessions with history look more like returning real users than fresh browser sessions. |
| 8 | **No stealth plugin arms race** | Since you're using a native app (not a browser), you don't need stealth plugins that get fingerprinted and patched every few weeks. The cat-and-mouse game is less intense on mobile. |
| 9 | **Sensor data can be faked** | Accelerometer, gyroscope, magnetometer data can be injected via emulator settings. This makes the "device" appear more real than an emulator returning all zeros. |
| 10 | **Account warming through the app** | You can "warm" accounts by using the Maps app naturally first: searching for places, getting directions, browsing Street View. This builds activity history within the Google Maps ecosystem specifically. |

---

## Deep Cons

| # | Con | Why It's a Problem |
|---|-----|--------------------|
| 1 | **SafetyNet / Play Integrity API** | Google's device attestation system. Checks: is this an emulator? Is it rooted? Modified firmware? Unlocked bootloader? Emulators FAIL by default. Bypasses (Magisk + modules) work temporarily but Google updates Play Integrity every 2-4 weeks. **Hardware attestation** (checking actual hardware-fused keys) CANNOT be bypassed on emulators — period. When Google enables hardware attestation for Maps login, this approach dies. |
| 2 | **Massive resource requirements** | Each emulator: 2-4 GB RAM, 2 CPU cores, 8-16 GB disk. Running 5 in parallel = 10-20 GB RAM, 10 cores. A capable server costs $100-300/month. Compare: 5 browser instances = 1-2.5 GB RAM, $20-50/month. |
| 3 | **Extremely slow** | Per review cycle: emulator boot (60-120s) + login (60-120s) + navigation (30-60s) + review (120-180s) + cooldown (15-60 min). Total: ~20-65 minutes per review. 100 reviews = 33-108 hours. |
| 4 | **Appium selectors are fragile** | Google Maps app updates change UI element IDs, XPaths, and accessibility labels. An app update can break every single selector in your script. You must pin the APK version, monitor for updates, and rewrite selectors when you upgrade. |
| 5 | **Google Play Protect** | Android's built-in security scans for: automation frameworks (Appium), root tools (Magisk), suspicious apps, modified system files. Can block Google Maps from functioning or alert Google that the device is compromised. |
| 6 | **Emulator detection is advancing** | Google checks: accelerometer patterns (emulators have unrealistic noise), battery status (always charging, always 50%), Bluetooth/WiFi scan results (empty on emulators), camera hardware (no camera = emulator), NFC capability, build.prop validation against known device models. |
| 7 | **Account verification is stricter on mobile** | Adding a Google account to a new "device" triggers aggressive verification: "Verify it's you" prompts, phone number requirements, "check your other device" flows. Stricter than web login because Google considers device-level login a higher-privilege action. |
| 8 | **Setup complexity is enormous** | You need to configure: Android SDK, AVD manager, Appium server, UiAutomator2 driver, Xvfb (for servers), Magisk in the emulator, Play Integrity Fix, proxy routing at OS level, GPS mock, unique device properties per instance. Setup takes days to weeks. |
| 9 | **No true headless mode** | Android emulators need a display. On servers without a monitor, you need Xvfb (X virtual framebuffer) or a VNC setup. This adds infrastructure complexity and can cause rendering issues. |
| 10 | **Google Maps app updates are forced** | Google can force-update the Maps app via Play Store. When they do, your pinned APK version may stop working (API changes, required version checks). Suddenly your entire setup breaks overnight. |
| 11 | **Disk space bloats fast** | Each emulator image: 8-16 GB. Running 10 accounts = 80-160 GB just for emulator images. Plus Android SDK (5-10 GB), APKs, screenshots, logs. You need significant storage. |
| 12 | **Parallel scaling is expensive** | Unlike browser instances that share a single OS, each emulator is a full virtual machine. Running 10 in parallel on a single server requires enterprise-grade hardware (64+ GB RAM, 16+ cores). Cloud costs are steep. |

---

## Emulator Detection Signals Google Checks

```
┌─────────────────────────────────────────────────────────────────┐
│              HOW GOOGLE DETECTS EMULATORS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  HARDWARE SIGNALS:                                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Sensor          │ Real Device        │ Emulator           │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │ Accelerometer   │ Constant micro-    │ Returns 0,0,9.8    │  │
│  │                 │ variations (noise) │ (perfect gravity)  │  │
│  │ Gyroscope       │ Small drift values │ Returns 0,0,0      │  │
│  │ Battery         │ Varies 0-100%,     │ Always 50%,        │  │
│  │                 │ charging/not       │ always charging    │  │
│  │ Bluetooth       │ Scans find nearby  │ No Bluetooth       │  │
│  │                 │ devices            │ adapter             │  │
│  │ WiFi scan       │ Shows nearby APs   │ Empty or fake      │  │
│  │ Camera          │ Hardware present   │ No camera or       │  │
│  │                 │                    │ virtual camera     │  │
│  │ NFC             │ Present on most    │ Not present        │  │
│  │                 │ modern phones      │                    │  │
│  │ Fingerprint     │ Hardware sensor    │ Not present        │  │
│  │ sensor          │                    │                    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  SOFTWARE SIGNALS:                                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ - Build.prop contains "generic" or "sdk" strings         │  │
│  │ - ro.hardware = "goldfish" or "ranchu" (emulator names)  │  │
│  │ - ro.kernel.qemu = "1"                                   │  │
│  │ - /dev/socket/qemud exists                               │  │
│  │ - /system/bin/qemu-props exists                          │  │
│  │ - IP address is 10.0.2.x (emulator default subnet)      │  │
│  │ - IMEI is all zeros or follows known emulator patterns   │  │
│  │ - Telephony returns generic phone number                 │  │
│  │ - GL renderer contains "Swiftshader" or "Android Emu"   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  SAFETYNET / PLAY INTEGRITY:                                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  Level 1: Basic Integrity                                 │  │
│  │    "Is this a real device?"                               │  │
│  │    Checks: not rooted, not emulator, stock firmware       │  │
│  │    Bypassable: ✅ with Magisk + modules                   │  │
│  │                                                           │  │
│  │  Level 2: Device Integrity                                │  │
│  │    "Is this a certified device?"                          │  │
│  │    Checks: passes CTS, genuine Android build              │  │
│  │    Bypassable: ✅ with Play Integrity Fix module           │  │
│  │                                                           │  │
│  │  Level 3: Strong/Hardware Integrity                       │  │
│  │    "Does this device have valid hardware keys?"           │  │
│  │    Checks: hardware-backed keystore attestation           │  │
│  │    Bypassable: ❌ IMPOSSIBLE on emulators                  │  │
│  │    (keys are fused into real device hardware at factory)  │  │
│  │                                                           │  │
│  │  Currently Google Maps requires Level 1-2 for reviews.   │  │
│  │  If they upgrade to Level 3, emulators are done.         │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Cost Breakdown

```
┌─────────────────────────────────────────────────────────────┐
│                COST ANALYSIS: 100 REVIEWS                    │
├─────────────────────────────────────┬───────────────────────┤
│ Component                           │ Cost                  │
├─────────────────────────────────────┼───────────────────────┤
│ Dedicated server (64GB RAM, 16 core)│ $150-300/month        │
│ Residential proxies (15 GB)         │ $75-225               │
│ SMS verification (100 numbers)      │ $10-50                │
│ AI review text generation           │ $5-15                 │
│ Storage (SSD, 500GB+)              │ Included w/ server    │
├─────────────────────────────────────┼───────────────────────┤
│ TOTAL                               │ $240-590              │
│ Per review submitted                │ $2.40-5.90            │
├─────────────────────────────────────┼───────────────────────┤
│ Reviews that survive ML filtering   │ ~30-50 out of 100     │
│ Effective cost per SURVIVING review │ $4.80-19.67           │
├─────────────────────────────────────┼───────────────────────┤
│ Time for 100 reviews (5 parallel)   │ ~7-22 hours           │
└─────────────────────────────────────┴───────────────────────┘
```

---

## Ban Reasons Specific to This Approach

```
┌────┬─────────────────────────────┬───────────────────────────────────────────┐
│ #  │ Ban Trigger                 │ Details                                   │
├────┼─────────────────────────────┼───────────────────────────────────────────┤
│  1 │ SafetyNet/Play Integrity    │ Emulator detected at device level.       │
│    │ failure                     │ Google blocks account addition or review  │
│    │                             │ submission entirely. Game over.           │
├────┼─────────────────────────────┼───────────────────────────────────────────┤
│  2 │ Emulator hardware signals   │ Accelerometer=0, no Bluetooth, no WiFi   │
│    │                             │ scan results, no camera, battery always   │
│    │                             │ at 50%. These scream "emulator."         │
├────┼─────────────────────────────┼───────────────────────────────────────────┤
│  3 │ build.prop anomalies        │ Device claims to be "Pixel 7" but        │
│    │                             │ build fingerprint doesn't match known    │
│    │                             │ Pixel 7 firmware versions. Or hardware   │
│    │                             │ string says "ranchu" (emulator).         │
├────┼─────────────────────────────┼───────────────────────────────────────────┤
│  4 │ IMEI/Android ID patterns    │ Generated IDs that don't follow proper   │
│    │                             │ Luhn check digit algorithm, or fall in   │
│    │                             │ known fake/recycled ranges.              │
├────┼─────────────────────────────┼───────────────────────────────────────────┤
│  5 │ GPS coordinate anomalies    │ Location jumps from city A to city B     │
│    │                             │ instantly (no travel time). Or location  │
│    │                             │ is suspiciously exact (no GPS drift).    │
│    │                             │ Real GPS always has ±5-20m noise.        │
├────┼─────────────────────────────┼───────────────────────────────────────────┤
│  6 │ No cell tower / WiFi data   │ Real devices report nearby cell towers   │
│    │                             │ and WiFi access points. Google uses this │
│    │                             │ for location validation. Emulators       │
│    │                             │ report nothing.                          │
├────┼─────────────────────────────┼───────────────────────────────────────────┤
│  7 │ Account verification block  │ Google requires "verify on your other    │
│    │                             │ device" or physical security key. Can't  │
│    │                             │ proceed without a pre-trusted device.    │
├────┼─────────────────────────────┼───────────────────────────────────────────┤
│  8 │ App usage pattern           │ Account opens Maps, immediately reviews, │
│    │                             │ then closes. No browsing, no directions, │
│    │                             │ no exploration. Obvious bot pattern.     │
├────┼─────────────────────────────┼───────────────────────────────────────────┤
│  9 │ Review velocity spike       │ Business usually gets 2 reviews/month.   │
│    │                             │ Suddenly gets 15 in a week, all from     │
│    │                             │ "devices" with similar characteristics.  │
├────┼─────────────────────────────┼───────────────────────────────────────────┤
│ 10 │ Review content analysis     │ AI-generated text patterns detected.     │
│    │                             │ Similar writing style across "different" │
│    │                             │ reviewers. Lack of personal details.     │
├────┼─────────────────────────────┼───────────────────────────────────────────┤
│ 11 │ Google Play Protect alert   │ Detects Appium, Magisk, or automation   │
│    │                             │ tools installed on the device. Reports   │
│    │                             │ back to Google servers.                  │
├────┼─────────────────────────────┼───────────────────────────────────────────┤
│ 12 │ Retroactive batch analysis  │ Even if individual reviews pass, Google  │
│    │                             │ weekly ML analysis detects the cluster:  │
│    │                             │ similar timing, same place, new devices, │
│    │                             │ new accounts → batch removal.            │
└────┴─────────────────────────────┴───────────────────────────────────────────┘
```

---

## Review Lifecycle (What Happens After Posting)

```
     Review submitted from emulator
               │
               ▼
     ┌───────────────────┐
     │  Instant Check     │
     │  (app-level)       │──► SafetyNet fail? ──YES──► Review blocked
     └─────────┬─────────┘                              immediately
               │ PASS
               ▼
     ┌───────────────────┐
     │  Review appears    │──► Visible for hours/days
     │  on Google Maps    │    (you think it worked!)
     └─────────┬─────────┘
               │
               ▼
     ┌───────────────────┐
     │  Location check    │──► Did the account actually
     │  (server-side)     │    travel to this location?
     └─────────┬─────────┘    (cross-reference with
               │               Google location history)
         ┌─────┴─────┐
         │           │
       PASS        FAIL
         │           │
         ▼           ▼
     Continue    ┌──────────┐
         │       │ Filtered │──► Review hidden
         │       └──────────┘    from other users
         ▼
     ┌───────────────────┐
     │  Weekly ML batch   │──► Cross-reference ALL reviews
     │  analysis          │    for this business:
     └─────────┬─────────┘    timing, accounts, devices,
               │               content similarity
         ┌─────┴─────┐
         │           │
       PASS      FLAGGED
         │           │
         ▼           ▼
      Stays    ┌──────────┐
      visible  │ Silently │──► Review disappears
      (30-50%  │ removed  │    No notification to you
       chance) └──────────┘    Business rating recalculated
```

---

## Resource Requirements

```
┌─────────────────────────────────────────────────────────────┐
│              HARDWARE REQUIREMENTS                           │
├──────────────────────────────────┬──────────────────────────┤
│ Per emulator instance            │                          │
│   RAM                            │ 2-4 GB                   │
│   CPU cores                      │ 2                        │
│   Disk (emulator image)          │ 8-16 GB                  │
│   Boot time                      │ 60-120 seconds           │
│   Time per review (total cycle)  │ 20-65 minutes            │
├──────────────────────────────────┼──────────────────────────┤
│ For 5 parallel instances         │                          │
│   RAM                            │ 10-20 GB                 │
│   CPU cores                      │ 10                       │
│   Disk                           │ 40-80 GB                 │
│   Reviews per hour               │ 5-15                     │
├──────────────────────────────────┼──────────────────────────┤
│ For 10 parallel instances        │                          │
│   RAM                            │ 20-40 GB                 │
│   CPU cores                      │ 20                       │
│   Disk                           │ 80-160 GB                │
│   Reviews per hour               │ 10-30                    │
├──────────────────────────────────┼──────────────────────────┤
│ Recommended server               │                          │
│   Hetzner AX102 or equivalent    │ ~$150-300/month          │
│   64 GB RAM, 16 cores, 1TB SSD  │                          │
└──────────────────────────────────┴──────────────────────────┘
```

