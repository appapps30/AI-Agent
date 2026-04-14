"""
INR Trial Flow Orchestrator — Stage-aware engine for the complete
Appy Pie INR Trial App creation flow including Razorpay payment.

Stages:
  LANDING -> BUSINESS_NAME -> CATEGORY -> REGISTRATION -> LOGIN ->
  ONBOARDING_PURPOSE -> ONBOARDING_REFERRAL -> PRICING -> RAZORPAY_CHECKOUT ->
  PAYMENT_SUCCESS -> TRIAL_LOADING -> BUSINESS_DASHBOARD -> APP_SETUP ->
  APP_DASHBOARD -> EDITOR_LOADING -> EDITOR -> ADD_FEATURES -> SAVE_DONE
"""


class INRTrialStage:
    LANDING = "landing"
    BUSINESS_NAME = "business_name"
    CATEGORY = "category"
    COLOR_SCHEME = "color_scheme"
    DEVICE_SELECT = "device_select"
    REGISTRATION = "registration"
    LOGIN = "login"
    APP_PURPOSE = "app_purpose"
    TEAM_SIZE = "team_size"
    UPGRADE_PROMPT = "upgrade_prompt"
    ONBOARDING_PURPOSE = "onboarding_purpose"
    ONBOARDING_REFERRAL = "onboarding_referral"
    PRICING = "pricing"
    RAZORPAY_CHECKOUT = "razorpay_checkout"
    PAYMENT_SUCCESS = "payment_success"
    TRIAL_LOADING = "trial_loading"
    BUSINESS_DASHBOARD = "business_dashboard"
    APP_SETUP = "app_setup"
    APP_DASHBOARD = "app_dashboard"
    EDITOR_LOADING = "editor_loading"
    EDITOR = "editor"
    ADD_FEATURES = "add_features"
    SAVE_DONE = "save_done"
    UNKNOWN = "unknown"


# Stage detection rules (checked in order — first match wins)
STAGE_RULES = [
    {
        "stage": INRTrialStage.PAYMENT_SUCCESS,
        "url_contains": ["checkout.appypie.com"],
        "page_keywords": ["payment successful", "transaction id", "redirected"],
    },
    {
        "stage": INRTrialStage.RAZORPAY_CHECKOUT,
        "url_contains": ["checkout.appypie.com"],
        "page_keywords": ["razorpay", "payment", "upi", "contact details", "subscribe", "pay"],
    },
    {
        "stage": INRTrialStage.PRICING,
        "url_contains": ["snappy.appypie.com/user/app/upgrade"],
        "page_keywords": ["buy now", "subscribe now", "basic plan", "what's included", "pricing"],
    },
    {
        "stage": INRTrialStage.TRIAL_LOADING,
        "url_contains": ["snappy.appypie.com/app/trialsuccess"],
        "page_keywords": ["welcome", "loading", "trial"],
    },
    {
        "stage": INRTrialStage.APP_SETUP,
        "url_contains": ["snappy.appypie.com/user/app/business-dashboard"],
        "page_keywords": ["setting up", "almost ready"],
    },
    {
        "stage": INRTrialStage.BUSINESS_DASHBOARD,
        "url_contains": ["snappy.appypie.com/user/app/business-dashboard"],
        "page_keywords": ["manage app", "what's included", "business dashboard", "get website", "get domain"],
    },
    {
        "stage": INRTrialStage.APP_DASHBOARD,
        "url_contains": ["snappy.appypie.com/user/app/"],
        "page_keywords": ["welcome user", "edit app", "test your app", "publish", "trial period"],
    },
    {
        "stage": INRTrialStage.SAVE_DONE,
        "url_contains": ["snappy.appypie.com/appmakr"],
        "page_keywords": ["congratulations", "scan the qr", "publish your app", "publish now"],
    },
    {
        "stage": INRTrialStage.ADD_FEATURES,
        "url_contains": ["snappy.appypie.com/appmakr"],
        "page_keywords": ["add features", "edit feature", "search feature", "business & commerce"],
    },
    {
        "stage": INRTrialStage.EDITOR,
        "url_contains": ["snappy.appypie.com/appmakr"],
        "page_keywords": ["editor", "page:", "save", "app manager"],
    },
    {
        "stage": INRTrialStage.EDITOR_LOADING,
        "url_contains": ["snappy.appypie.com/appmakr"],
        "page_keywords": ["loading"],
    },
    {
        "stage": INRTrialStage.ONBOARDING_PURPOSE,
        "url_contains": ["snappy.appypie.com/app-builder"],
        "page_keywords": ["how do you plan to use", "for work", "for personal", "for education"],
    },
    {
        "stage": INRTrialStage.ONBOARDING_REFERRAL,
        "url_contains": ["snappy.appypie.com/app-builder"],
        "page_keywords": ["how did you hear", "friend or colleague", "google or other", "newsletter"],
    },
    {
        "stage": INRTrialStage.DEVICE_SELECT,
        "url_contains": ["snappy.appypie.com/app-builder", "snappy.appypie.com/appbuilder"],
        "page_keywords": ["select which device", "android", "ios", "device to test"],
    },
    {
        "stage": INRTrialStage.COLOR_SCHEME,
        "url_contains": ["snappy.appypie.com/app-builder", "snappy.appypie.com/appbuilder"],
        "page_keywords": ["pick a color", "color scheme", "deep ocean", "go green", "cheerful cherry",
                          "dynamic sunburst", "carbon mystique", "techno grey"],
    },
    {
        "stage": INRTrialStage.CATEGORY,
        "url_contains": ["snappy.appypie.com/app-builder", "snappy.appypie.com/appbuilder"],
        "page_keywords": ["choose the category", "restaurant", "radio/podcast", "online store", "education", "events"],
    },
    {
        "stage": INRTrialStage.APP_PURPOSE,
        "url_contains": ["snappy.appypie.com/app-builder", "snappy.appypie.com/appbuilder"],
        "page_keywords": ["what's the main thing", "want this app to do", "sell products", "manage internal operations"],
    },
    {
        "stage": INRTrialStage.TEAM_SIZE,
        "url_contains": ["snappy.appypie.com/app-builder", "snappy.appypie.com/appbuilder"],
        "page_keywords": ["how many people", "work in your organization", "just me", "2-10", "51-500"],
    },
    {
        "stage": INRTrialStage.UPGRADE_PROMPT,
        "url_contains": ["snappy.appypie.com/app-builder", "snappy.appypie.com/appbuilder"],
        "page_keywords": ["almost ready", "upgrade now", "gain full access"],
    },
    {
        "stage": INRTrialStage.BUSINESS_NAME,
        "url_contains": ["snappy.appypie.com/app-builder", "snappy.appypie.com/appbuilder"],
        "page_keywords": ["enter business name", "you can change it later"],
    },
    {
        "stage": INRTrialStage.LOGIN,
        "url_contains": ["accounts.appypie.com/login"],
        "page_keywords": ["log in", "login", "password", "don't have an account"],
    },
    {
        "stage": INRTrialStage.REGISTRATION,
        "url_contains": ["accounts.appypie.com/register", "accounts.appypie.com"],
        "page_keywords": ["create your account", "sign up", "create account"],
    },
    {
        "stage": INRTrialStage.LANDING,
        "url_contains": ["appypie.com"],
        "page_keywords": ["create your app", "app builder", "app maker", "no-code"],
    },
]


# Stage-specific prompts for the LLM
STAGE_PROMPTS = {
    INRTrialStage.LANDING: """## Current Stage: LANDING PAGE
You are on the Appy Pie homepage (appypie.com/app-builder/appmaker).

**Your task:** Click "Create Your App" button to start the flow.
  Try: button:has-text("Create Your App"), a:has-text("Create Your App"), #createAppBtn
  If not found: look for any orange/red button with "Create" text.""",

    INRTrialStage.APP_PURPOSE: """## Current Stage: APP PURPOSE SELECTION
You see "What's the main thing you want this app to do?" with multiple option cards.

**Your task:** Select "Sell Products & Services Online" (or any visible option), then click "Continue".
  1. Click an option: {{"action": "click", "selector": "div:has-text(\\"Sell Products\\")", "description": "selecting Sell Products purpose"}}
     If fails try: any visible card option on the page.
  2. Then click Continue: {{"action": "click", "selector": "button:has-text(\\"Continue\\")", "description": "clicking Continue"}}
     Or: a:has-text("Continue")

**Pick any option. The goal is to proceed past this page.**""",

    INRTrialStage.TEAM_SIZE: """## Current Stage: TEAM SIZE
You see "How many people work in your organization?" with size options.

**Your task:** Select "2-10" and click Continue.
  1. Click "2-10": {{"action": "click", "selector": "text=\\"2-10\\"", "description": "selecting 2-10 team size"}}
  2. Click Continue: {{"action": "click", "selector": "button:has-text(\\"Continue\\")", "description": "clicking Continue"}}""",

    INRTrialStage.UPGRADE_PROMPT: """## Current Stage: UPGRADE PROMPT
You see "Your App is Almost Ready!" with a trial/upgrade button.

**Your task:** Click "Start My 7-days Trial" or "Upgrade Now" to proceed.
  {{"action": "click", "selector": "button:has-text(\\"Start My 7-days Trial\\")", "description": "clicking Start My 7-days Trial"}}
  If fails try: a:has-text("Start My 7-days Trial"), button:has-text("Upgrade Now"), a:has-text("Upgrade Now"), .btn-primary""",

    INRTrialStage.BUSINESS_NAME: """## Current Stage: ENTER BUSINESS NAME
You see "Enter business name" page.

**Check past actions:**
- If NOT yet filled: {{"action": "fill", "selector": "input[placeholder*='Enter business name']", "value": "{app_name}", "description": "entering business name"}}
- If already filled: {{"action": "click", "selector": "a:has-text(\\"Next\\")", "description": "clicking Next"}}

**NEVER fill twice. After filling once, click Next.**""",

    INRTrialStage.CATEGORY: """## Current Stage: CHOOSE CATEGORY
You see "Choose the category that fits best".

**Your task:** Click on "Business >" category.
  {{"action": "click", "selector": "a:has-text(\\"Business\\")", "description": "selecting Business category"}}
  If that fails try any other visible category.""",

    INRTrialStage.COLOR_SCHEME: """## Current Stage: PICK COLOR SCHEME
You see "Pick a color scheme you like" with Light/Dark toggle and 6 options.

**Your task:** Click on any color scheme card. Try "DEEP OCEAN" first:
  {{"action": "click", "selector": "a:has-text(\\"DEEP OCEAN\\")", "description": "selecting Deep Ocean color scheme"}}
  If fails try: clicking any visible color card, or a:has-text("GO GREEN"), a:has-text("TECHNO GREY")""",

    INRTrialStage.DEVICE_SELECT: """## Current Stage: SELECT DEVICE
You see "Select which device to test your app on" with Android and iOS options.

**Your task:** Click Android:
  {{"action": "click", "selector": "a:has-text(\\"Android\\")", "description": "selecting Android device"}}
  If fails try any device card visible.""",

    INRTrialStage.REGISTRATION: """## Current Stage: REGISTRATION / SIGN UP
You see the "Create your account" page with "Already have an account? Login" link.

**Your task:** Click the "Login" link (small text near "Already have an account?") to go to the login page.

Try these selectors in order:
  1. {{"action": "click", "selector": "a:has-text(\\"Login\\")", "description": "clicking Login link"}}
  2. {{"action": "click", "selector": "a:has-text(\\"Log in\\")", "description": "clicking Log in link"}}
  3. {{"action": "click", "selector": "a[href*='login']", "description": "clicking login href link"}}

**Do NOT sign up. Do NOT click "Sign in with Google" or "Continue with Apple".**
**Do NOT fill the email field here. Click Login first to go to the login page.**""",

    INRTrialStage.LOGIN: """## Current Stage: LOGIN
You see "Log in to your account" page.

**IMPORTANT: The email field ID is #testing (NOT #email). The password field appears AFTER entering email.**

**Check past actions and do the NEXT step:**

1. If email NOT filled: {{"action": "fill", "selector": "#testing", "value": "{email}", "description": "entering email in login field"}}
   If #testing fails try: input[placeholder*="Email"], input[placeholder*="Enter Email"], input[name="testing"]

2. If email filled, click LOGIN to reveal password field:
   {{"action": "click", "selector": "button:has-text(\\"LOGIN\\")", "description": "clicking Login to reveal password field"}}

3. If password field now visible (input[type="password"]):
   {{"action": "fill", "selector": "input[type=\\"password\\"]", "value": "{password}", "description": "entering password"}}

4. Click LOGIN again to submit:
   {{"action": "click", "selector": "button:has-text(\\"LOGIN\\")", "description": "submitting login"}}

**Credentials:** Email: {email} | Password: {password}
**NEVER click "Sign in with Google". Use email/password login.
NEVER fill password into the email field. Email goes in #testing, password goes in input[type="password"].**""",

    INRTrialStage.ONBOARDING_PURPOSE: """## Current Stage: ONBOARDING — USAGE PURPOSE
You see "How do you plan to use Appy Pie?"

**Your task:** Select "For Work" and click Continue.
  1. Click "For Work" card: {{"action": "click", "selector": "div:has-text(\\"For Work\\")", "description": "selecting For Work"}}
  2. Click Continue: {{"action": "click", "selector": "button:has-text(\\"Continue\\")", "description": "clicking Continue"}}""",

    INRTrialStage.ONBOARDING_REFERRAL: """## Current Stage: ONBOARDING — REFERRAL SOURCE
You see "How did you hear about us?" (Optional).

**Your task:** Just click Continue to skip.
  {{"action": "click", "selector": "button:has-text(\\"Continue\\")", "description": "skipping referral question"}}""",

    INRTrialStage.PRICING: """## Current Stage: PRICING / UPGRADE PAGE
You see "Buy Now and Start Testing Your App!" with Basic Plan at ₹5.

**Your task:** Click "Subscribe Now" button.
  {{"action": "click", "selector": "button:has-text(\\"Subscribe Now\\")", "description": "clicking Subscribe Now for Basic Plan"}}
  If fails try: a:has-text("Subscribe Now"), .subscribe-btn""",

    INRTrialStage.RAZORPAY_CHECKOUT: """## Current Stage: RAZORPAY CHECKOUT
The Razorpay payment modal is shown.

**Check what's visible and do the next step:**

- If "Contact details" modal visible (asking for phone/email):
  Fill phone if empty: {{"action": "fill", "selector": "input[type='tel']", "value": "9891347174", "description": "entering phone number"}}
  Then click Continue: {{"action": "click", "selector": "button:has-text(\\"Continue\\")", "description": "continuing past contact details"}}

- If UPI QR code is shown: Wait for payment to complete.
  {{"action": "wait", "duration": 5000, "description": "waiting for payment processing"}}

- If payment options shown: Select UPI or Cards as needed.

**This is Razorpay Test Mode — payment will be simulated.**""",

    INRTrialStage.PAYMENT_SUCCESS: """## Current Stage: PAYMENT SUCCESSFUL
You see "Payment Successful" with a green checkmark.

**Your task:** Wait for auto-redirect (2 seconds).
  {{"action": "wait", "duration": 3000, "description": "waiting for redirect after payment success"}}""",

    INRTrialStage.TRIAL_LOADING: """## Current Stage: TRIAL SUCCESS — LOADING
You see a loading spinner after payment. The app is being provisioned.

**Your task:** Wait for loading to complete.
  {{"action": "wait", "duration": 5000, "description": "waiting for trial setup to complete"}}""",

    INRTrialStage.BUSINESS_DASHBOARD: """## Current Stage: BUSINESS DASHBOARD
You see the business dashboard with your app card and trial details.

**Your task:** Click "Manage App" to proceed.
  {{"action": "click", "selector": "a:has-text(\\"Manage App\\")", "description": "clicking Manage App"}}
  If fails try: button:has-text("Manage App"), a:has-text("Manage")""",

    INRTrialStage.APP_SETUP: """## Current Stage: APP SETUP
A "Setting Up Your App" modal is shown with loading spinner.

**Your task:** Wait for setup to complete.
  {{"action": "wait", "duration": 5000, "description": "waiting for app setup"}}""",

    INRTrialStage.APP_DASHBOARD: """## Current Stage: APP DASHBOARD
You see "Welcome User" with app details and trial expiry info.

**Your task:** Click "Edit App" to open the editor.
  {{"action": "click", "selector": "button:has-text(\\"Edit App\\")", "description": "clicking Edit App"}}
  If fails try: a:has-text("Edit App"), .edit-app-btn""",

    INRTrialStage.EDITOR_LOADING: """## Current Stage: EDITOR LOADING
The app editor is loading with a spinner.

**Your task:** Wait for editor to load.
  {{"action": "wait", "duration": 7000, "description": "waiting for editor to load"}}""",

    INRTrialStage.EDITOR: """## Current Stage: APP EDITOR
The editor is loaded showing "Editor — Page: Home" with pages sidebar.

**Check past actions:**

- If NOT yet clicked Save:
  {{"action": "click", "selector": "button:has-text(\\"Save\\")", "description": "clicking Save button"}}
  If fails try: button.publish-btn, a:has-text("Save"), button.btn-success

- If Save was clicked, return done:
  {{"action": "done", "description": "INR Trial flow complete: Landing → Business Name → Category → Login → Onboarding → Payment → Dashboard → Editor → Saved"}}

**Do NOT click on the app content/preview area.**""",

    INRTrialStage.SAVE_DONE: """## Current Stage: CONGRATULATIONS — APP SAVED
You see "Congratulations" modal with QR code.

**Your task:** Click "Done" button and return done.
  {{"action": "click", "selector": "button:has-text(\\"Done\\")", "description": "clicking Done on congratulations modal"}}
  Then: {{"action": "done", "description": "INR Trial flow complete!"}}""",

    INRTrialStage.ADD_FEATURES: """## Current Stage: ADD FEATURES
The "Add Features" dialog is open.

**Your task:** Close this dialog and go back to Save.
  {{"action": "click", "selector": "button:has-text(\\"×\\")", "description": "closing Add Features dialog"}}
  Or press Escape: {{"action": "press_enter", "description": "pressing Escape to close"}}""",

    INRTrialStage.UNKNOWN: """## Current Stage: UNKNOWN
Could not determine stage. Analyze the page and URL.

**If URL contains appypie.com:** Look for buttons, forms, or links to proceed.
**If URL does NOT contain appypie.com:** Navigate back:
  {{"action": "navigate", "url": "https://www.appypie.com/app-builder/appmaker", "description": "returning to landing page"}}

**NEVER navigate to domains other than appypie.com, accounts.appypie.com, snappy.appypie.com, or checkout.appypie.com.**""",
}


import random

RANDOM_BUSINESS_NAMES = [
    "Bellas Bakery", "QuickFix Auto Repair", "GreenLeaf Landscaping",
    "Urban Bites Cafe", "Sparkle Cleaners", "Peak Fitness Studio",
    "Sunrise Yoga Center", "Golden Gate Realty", "BlueWave Surf Shop",
    "FreshMart Grocers", "Paws and Claws Pet Spa", "CloudNine Travel",
    "Iron Horse Gym", "Pixel Perfect Studio", "Savory Spoon Restaurant",
    "TechHub Solutions", "Blossom Flower Shop", "Cozy Corner Books",
    "Swift Courier Services", "Harbor View Dental", "NexGen Portal",
    "BrightPath Tools", "UrbanPulse Hub", "DataSync Manager",
    "InnovateMart Hub", "SmartConnect Pro", "FlexiStore Platform",
]


class INRTrialOrchestrator:
    def __init__(self, app_name: str = None, email: str = None, password: str = None):
        self.app_name = app_name or random.choice(RANDOM_BUSINESS_NAMES)
        self.email = email or "testqa.delhi21@gmail.com"
        self.password = password or "Test@12345"
        self.current_stage = INRTrialStage.UNKNOWN
        self.stage_history: list[str] = []

    def detect_stage(self, url: str, page_text: str = "") -> str:
        """Detect current flow stage from URL and visible page text."""
        url_lower = url.lower()
        text_lower = page_text.lower()

        for rule in STAGE_RULES:
            url_match = any(u in url_lower for u in rule["url_contains"])
            keyword_match = any(kw in text_lower for kw in rule["page_keywords"])

            if url_match and keyword_match:
                self.current_stage = rule["stage"]
                if not self.stage_history or self.stage_history[-1] != self.current_stage:
                    self.stage_history.append(self.current_stage)
                return self.current_stage

        # Fallback: URL-only matching
        if "checkout.appypie.com" in url_lower:
            self.current_stage = INRTrialStage.RAZORPAY_CHECKOUT
        elif "accounts.appypie.com/login" in url_lower:
            self.current_stage = INRTrialStage.LOGIN
        elif "accounts.appypie.com" in url_lower:
            self.current_stage = INRTrialStage.REGISTRATION
        elif "trialsuccess" in url_lower:
            self.current_stage = INRTrialStage.TRIAL_LOADING
        elif "business-dashboard" in url_lower:
            self.current_stage = INRTrialStage.BUSINESS_DASHBOARD
        elif "upgrade-app" in url_lower:
            self.current_stage = INRTrialStage.PRICING
        elif "appmakr" in url_lower:
            self.current_stage = INRTrialStage.EDITOR
        elif "snappy.appypie.com/user/app" in url_lower:
            self.current_stage = INRTrialStage.APP_DASHBOARD
        elif "snappy.appypie.com" in url_lower:
            self.current_stage = INRTrialStage.BUSINESS_NAME
        elif "appypie.com" in url_lower:
            self.current_stage = INRTrialStage.LANDING
        else:
            self.current_stage = INRTrialStage.UNKNOWN

        if not self.stage_history or self.stage_history[-1] != self.current_stage:
            self.stage_history.append(self.current_stage)

        return self.current_stage

    def get_stage_prompt(self) -> str:
        """Get the LLM prompt for the current stage with credentials injected."""
        template = STAGE_PROMPTS.get(self.current_stage, STAGE_PROMPTS[INRTrialStage.UNKNOWN])
        return template.format(
            app_name=self.app_name,
            email=self.email,
            password=self.password,
        )

    def get_progress_summary(self) -> str:
        """Human-readable progress summary."""
        stage_names = {
            INRTrialStage.LANDING: "Landing",
            INRTrialStage.BUSINESS_NAME: "Biz Name",
            INRTrialStage.CATEGORY: "Category",
            INRTrialStage.COLOR_SCHEME: "Color",
            INRTrialStage.DEVICE_SELECT: "Device",
            INRTrialStage.REGISTRATION: "Register",
            INRTrialStage.LOGIN: "Login",
            INRTrialStage.APP_PURPOSE: "Purpose",
            INRTrialStage.TEAM_SIZE: "Team Size",
            INRTrialStage.UPGRADE_PROMPT: "Upgrade",
            INRTrialStage.ONBOARDING_PURPOSE: "Onboard",
            INRTrialStage.ONBOARDING_REFERRAL: "Referral",
            INRTrialStage.PRICING: "Pricing",
            INRTrialStage.RAZORPAY_CHECKOUT: "Razorpay",
            INRTrialStage.PAYMENT_SUCCESS: "Paid",
            INRTrialStage.TRIAL_LOADING: "Trial",
            INRTrialStage.BUSINESS_DASHBOARD: "Biz Dash",
            INRTrialStage.APP_SETUP: "Setup",
            INRTrialStage.APP_DASHBOARD: "App Dash",
            INRTrialStage.EDITOR_LOADING: "Loading",
            INRTrialStage.EDITOR: "Editor",
            INRTrialStage.SAVE_DONE: "Saved",
        }
        total = len(stage_names)
        done = len(self.stage_history)
        current = stage_names.get(self.current_stage, "Unknown")
        history = [stage_names.get(s, s) for s in self.stage_history]

        return (
            f"Progress: {done}/{total} stages | "
            f"Current: {current} | "
            f"Path: {' -> '.join(history)}"
        )
