# Google Maps Review Bot

An open-source research project exploring automated Google Maps review posting through two distinct approaches: **Browser Automation with AI CAPTCHA Solving** and **Mobile Emulation via Appium**.

This project exists to study and document how review automation works, the anti-bot detection systems Google employs, and the technical challenges involved in replicating human behavior programmatically.

---

## What This Project Does

The bot automates the full review-posting pipeline on Google Maps:

1. **Account Management** - Loads and rotates through multiple Google accounts
2. **Proxy Rotation** - Assigns residential proxies per session to avoid IP correlation
3. **Authentication** - Logs into Google accounts with human-like typing and interaction delays
4. **CAPTCHA Handling** - Detects and solves reCAPTCHA challenges using AI vision models and solver APIs
5. **Review Generation** - Uses OpenAI to generate unique, natural-sounding review text for each account
6. **Review Posting** - Navigates to the target place and submits the review with randomized ratings
7. **Result Tracking** - Logs every attempt with status, screenshots, and metadata

---

## Two Approaches

### 1. Browser Automation + AI CAPTCHA Solver (`browser-ai-captcha/`)

Automates a real browser (Playwright) with stealth patches to log into Gmail accounts and submit Google Maps reviews. When CAPTCHAs appear, an AI-powered solver handles them automatically.

**Tech Stack:** Python, Playwright + stealth plugin, 2Captcha / CapSolver, OpenAI GPT-4 Vision, Residential proxies

```
Account Manager --> Proxy Rotator --> Stealth Browser --> CAPTCHA Solver --> Review Poster
```

**Quick Start:**
```bash
cd browser-ai-captcha
pip install -r requirements.txt
cp .env.example .env          # Add your API keys
cp accounts.json.example accounts.json
python main.py run --place-url "https://maps.google.com/..." --place-name "Coffee Shop"
```

### 2. Mobile Emulation / Appium (`mobile-emulation/`)

Instead of automating a web browser, this approach automates the **Google Maps Android app** running inside Android emulators. Each emulator is configured as a unique "device" with spoofed hardware identifiers, GPS location, and sensor data.

**Tech Stack:** Python, Appium 2.0 + UiAutomator2, Android Emulator (AVD), Magisk + Play Integrity Fix, GPS spoofing via ADB, OpenAI

```
Account Manager --> Device Spoofing --> Emulator Pool --> GPS Spoof --> Maps App --> Review
```

**Quick Start:**
```bash
cd mobile-emulation
pip install -r requirements.txt
cp .env.example .env          # Add your API keys
cp accounts.json.example accounts.json
python main.py setup --name review_bot_avd
python main.py run --place "Coffee Shop" --lat 40.7484 --lon -73.9857
```

---

## Approach Comparison

| Factor | Browser Automation | Mobile Emulation |
|---|---|---|
| **reCAPTCHA v3** | Must deal with invisible behavioral scoring | Not present in native Android app |
| **Detection Surface** | Web fingerprinting (canvas, WebGL, CDP) | Device attestation (SafetyNet/Play Integrity) |
| **Resources per Instance** | 200-500 MB RAM | 2-4 GB RAM + 2 CPU cores |
| **Time per Review** | 5-15 minutes | 20-65 minutes |
| **GPS Spoofing** | Not possible | Built-in via ADB |
| **Setup Complexity** | Low-Medium | High |
| **Detection Rate** | ~50-70% | ~40-60% |

---

## Project Structure

```
google-maps-review-bot/
├── browser-ai-captcha/
│   ├── core/
│   │   ├── account_manager.py    # Account loading and rotation
│   │   ├── browser.py            # Playwright stealth browser setup
│   │   ├── captcha_solver.py     # AI-powered CAPTCHA solving
│   │   ├── google_auth.py        # Google login automation
│   │   ├── human_behavior.py     # Mouse/scroll/typing simulation
│   │   ├── proxy_manager.py      # Proxy rotation
│   │   └── review_poster.py      # Review submission logic
│   ├── utils/
│   │   ├── logger.py             # Logging utility
│   │   └── review_generator.py   # OpenAI review text generation
│   ├── main.py                   # CLI entry point
│   ├── config.py                 # Configuration
│   └── requirements.txt
│
├── mobile-emulation/
│   ├── core/
│   │   ├── account_manager.py    # Account loading and rotation
│   │   ├── device_spoofing.py    # IMEI/Android ID/build.prop spoofing
│   │   ├── emulator_manager.py   # AVD lifecycle management
│   │   ├── google_auth.py        # Google login on Android
│   │   ├── gps_spoofing.py       # GPS coordinate spoofing via ADB
│   │   ├── maps_automation.py    # Google Maps app automation
│   │   └── proxy_manager.py      # Proxy rotation
│   ├── utils/
│   │   ├── logger.py             # Logging utility
│   │   └── review_generator.py   # OpenAI review text generation
│   ├── main.py                   # CLI entry point
│   ├── config.py                 # Configuration
│   └── requirements.txt
│
└── README.md                     # You are here
```

---

## Prerequisites

**Common:**
- Python 3.11+
- OpenAI API key (for review text generation)
- Google accounts (with passwords)
- Residential proxy list (recommended)

**Browser Automation:**
- Playwright (`pip install playwright && playwright install`)

**Mobile Emulation:**
- Android SDK + AVD Manager
- Appium 2.0 + UiAutomator2 driver
- Java 11+ (for Appium)

---

## Configuration

Both approaches use `.env` files for API keys and `accounts.json` for Google account credentials. See the `.env.example` and `accounts.json.example` files in each directory.

---

## Contributing

This is an **open-source project** and contributions are welcome! Whether you want to fix bugs, add features, improve documentation, or share ideas, feel free to get involved.

### How to Contribute

1. **Fork** this repository
2. **Create** a feature branch (`git checkout -b feature/your-feature`)
3. **Commit** your changes (`git commit -m "Add your feature"`)
4. **Push** to the branch (`git push origin feature/your-feature`)
5. **Open** a Pull Request

### Contribution Ideas

- Improve CAPTCHA solving accuracy
- Add support for additional CAPTCHA solver providers
- Better human behavior simulation patterns
- Enhanced device fingerprint spoofing for mobile emulation
- Add support for other review platforms
- Write tests
- Improve error handling and retry logic
- Documentation improvements

All skill levels are welcome. If you're not sure where to start, open an issue and we'll help you find something to work on.

---

## Disclaimer

This project is intended for **educational and research purposes only**. It is designed to study bot detection systems, anti-automation techniques, and the technical challenges of replicating human behavior. Use of this tool to post fake reviews violates Google's Terms of Service and may violate laws in your jurisdiction. The authors take no responsibility for misuse.

---

## License

This project is open source and available under the [MIT License](LICENSE).
