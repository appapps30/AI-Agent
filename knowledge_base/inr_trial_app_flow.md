# Appy Pie INR Trial App — Complete End-to-End Flow

## Overview
This document describes the complete user journey for creating a trial app on Appy Pie's App Builder platform using INR (Indian Rupee) payment. The flow covers landing page navigation, app creation, user authentication, onboarding, payment via Razorpay, and post-purchase app editing. This flow was recorded on April 11, 2026, using a test account (testqa.delhi21@gmail.com) in Razorpay Test Mode.

---

## Step 1: Landing Page — appypie.com
- **URL**: https://www.appypie.com/app-builder/appmaker
- **Page Title**: "App Builder to Build Apps in Minutes without Coding"
- **Description**: The Appy Pie homepage promotes the no-code app builder platform. It highlights that users can create native Android and iOS apps with a cloud-based no-code App Maker Platform.
- **Key UI Elements**:
  - Navigation bar with links: AI Generators, Drag & Drop, Features, Pricing, Customer Stories, About Us, Reseller Program, Blog
  - "Join" button (top-right, purple outline)
  - "Log In" link (top-right)
  - "Create Your App" button (orange/red, center of page)
  - Trust badges: Sodexo, Decathlon, Nike, Accenture, L'Oreal, NHS, Assurant, Southwest, Deloitte
  - Review scores: G2 4.75 (1,388 reviews), Capterra 4.6/5 (1,389 reviews)
  - Trustpilot: 4,424 reviews
  - Cookie consent banner at the bottom
- **Action Taken**: User clicks "Create Your App" button.

---

## Step 2: Enter Business Name — App Builder Creator
- **URL**: https://snappy.appypie.com/app-builder/creator-software/
- **Page Title**: "Enter business name"
- **Subtitle**: "(You can change it later)"
- **Description**: The first step of the app creation wizard asks the user to provide their business name. This is a required field before proceeding.
- **Key UI Elements**:
  - Appy Pie Builder logo (top-left)
  - Text input field: "Enter business name" placeholder
  - "Next" button (blue, centered)
  - Rating badges at the bottom: Capterra 4.6/5, G2 CROWD 4.7/5, unnamed 4.5/5, Trustpilot 4.7/5, GetApp 4.6/5, Software Advice 4.6/5
  - WhatsApp chat icon (bottom-right)
- **Action Taken**: User clicks into the business name field and types a business name, then clicks "Next".

---

## Step 3: Choose Category
- **URL**: https://snappy.appypie.com/app-builder/creator-software/
- **Page Title**: "Choose the category that fits best"
- **Description**: The user must select the business category that best describes their app. This helps Appy Pie customize the app template.
- **Available Categories**:
  - Business
  - Radio/Podcast
  - Restaurant & Food
  - Online Store
  - Events
  - Education
  - Religion/Worship
  - Health & Wellness
  - News & Magazine
  - Location & Places
  - Dating
  - Others
- **Footer Text**: "We're the quickest way to help you develop your app and start making money - without Coding!"
- **Navigation**: "← Go Back" link at bottom-left
- **Action Taken**: User selects "Business >" category.

---

## Step 4: Registration / Sign-Up Page
- **URL**: https://accounts.appypie.com/register?frompage=https%3A%2F%2Fsnappy.appypie.com%2Findex%2Fcommon-session&websitehi...
- **Page Title**: "Create your account" (partially visible due to Google Sign-in popup)
- **Description**: After selecting a category, the user is redirected to the Appy Pie accounts page to register or sign in. A Google Sign-in popup appears automatically.
- **Key UI Elements**:
  - Google Sign-in popup: "Use your Google Account to sign in to appypie.com" with "Continue" button
  - "Sign in with Google" button
  - "Continue with Apple" button
  - "Or" separator
  - Email Address / Mobile Number input field
  - "SIGN UP" button (gray)
  - Other methods: Facebook, Microsoft icons
  - Terms & Conditions and Privacy Policy consent checkbox
  - Left sidebar: "10M+ Happy Clients" with mascot illustrations
  - Trust points: "Trusted by 10 Million+ Businesses Worldwide!", "No Coding Needed, Easy Set Up", "Appy Pie is the Highest Rated No-code Platform"
- **Action Taken**: User dismisses the Google popup and navigates to the login page.

---

## Step 5: Login Page
- **URL**: https://accounts.appypie.com/login?lang=en&frompage=https%3A%2F%2Fsnappy.appypie.com%2Findex%2Fcommon-session
- **Page Title**: "Log in to your account"
- **Subtitle**: "Don't have an account? Sign up"
- **Description**: The user logs in with existing credentials. The email is pre-filled as testqa.delhi21@gmail.com.
- **Key UI Elements**:
  - "Sign in with Google" button
  - "Continue with Apple" button
  - "Or" separator
  - Email field (pre-filled: testqa.delhi21@gmail.com)
  - Password field (masked input)
  - "LOGIN" button (dark/black)
  - "Login with OTP" link
  - "Forgot password" link
  - Other methods: Facebook, Microsoft icons
  - Left sidebar: same "10M+ Happy Clients" branding
- **Action Taken**: User enters password and clicks "LOGIN".

---

## Step 6: Onboarding — Usage Purpose
- **URL**: https://snappy.appypie.com/app-builder/creator-software
- **Page Title**: "How do you plan to use Appy Pie?"
- **Subtitle**: "We use your answers to personalize your experience"
- **Description**: Post-login onboarding questionnaire. The user must select their intended usage purpose. This helps Appy Pie tailor the experience.
- **Options**:
  1. **For Work** — "For my business or work" (shown with a briefcase-style card in light yellow)
  2. **For Personal Use** — "For personal project & experiment" (shown with folder/person icon in light purple)
  3. **For Education** — "As a student or educator" (shown with book icon in light pink)
- **Key UI Elements**:
  - Three large selectable cards with icons
  - "Continue →" button (bottom-right, blue/purple)
  - WhatsApp chat icon (bottom-right)
- **Action Taken**: User selects "For Work" and clicks "Continue →".

---

## Step 7: Onboarding — Referral Source
- **URL**: https://snappy.appypie.com/app-builder/creator-software
- **Page Title**: "How did you hear about us?"
- **Subtitle**: "Optional (but appreciated)"
- **Description**: Optional survey question asking the user how they discovered Appy Pie. This is for marketing analytics purposes.
- **Options** (shown as selectable cards with icons):
  1. Friend or colleague
  2. Newsletter, blog, or podcast
  3. Google or other search
  4. TikTok
  5. Instagram or Facebook
  6. YouTube
  7. LinkedIn
  8. Twitter/X
  9. AI tool
  10. Other
- **Key UI Elements**:
  - Grid of selectable cards (3 columns × 4 rows)
  - "← Back" button (bottom-left)
  - "Continue →" button (bottom-right)
- **Action Taken**: User clicks "Continue →" (may or may not have selected an option).

---

## Step 8: Upgrade / Pricing Page
- **URL**: https://snappy.appypie.com/user/app/upgrade-app/11a13ac80301
- **Page Title**: "Buy Now and Start Testing Your App!"
- **Description**: The user is presented with the Basic Plan pricing page. In this test flow, the price is ₹5 (INR) in test mode.
- **Plan Details — WHAT'S INCLUDED**:
  - Native App
  - Responsive Website
  - Custom Domain
  - Business Email by Google
  - Publish App to Google Play
  - Access to all Basic Features
  - 500/Mo Push Notifications
  - 24/7 Customer care
- **Plan Name**: GET A BASIC PLAN
- **Price**: ₹5 (test mode pricing)
- **CTA Button**: "Subscribe Now" (blue)
- **Security Badges**: SSL Secure Payment, PCI DSS, McAfee Secure, Verified by Visa, MasterCard SecureCode
- **Action Taken**: User clicks "Subscribe Now".

---

## Step 9: Razorpay Checkout — Loading
- **URL**: https://checkout.appypie.com/index/pay
- **Description**: The checkout page loads the Razorpay payment gateway. A "Test Mode" ribbon/banner is visible in the top-right corner, indicating this is a test/sandbox environment.
- **Key UI Elements**:
  - Gray overlay/loading screen
  - "Test Mode" red ribbon in top-right corner
  - WhatsApp icon (bottom-right)
- **Action Taken**: Page loads and Razorpay modal appears.

---

## Step 10: Razorpay Payment — Contact Details
- **URL**: https://checkout.appypie.com/index/pay
- **Description**: The Razorpay payment modal requests contact details before proceeding to payment.
- **Key UI Elements**:
  - Left panel: "Monthly Basic" plan name with Appy Pie logo, Price Summary ₹5, "Using as testqa.delhi21@gmail.com"
  - Right panel: "Payment Options" header with close (×) button
  - Recommended: UPI option with payment provider icons
  - UPI QR tab showing QR code
  - Contact details modal overlay:
    - Title: "Contact details"
    - Subtitle: "Enter mobile & email to continue"
    - Phone field: +91 country code, number 9891347174
    - Email field: testqa.delhi21@gmail.com
    - "Continue" button (black)
  - "Secured by Razorpay" footer
  - "Test Mode" ribbon
- **Action Taken**: User enters contact details and clicks "Continue".

---

## Step 11: Razorpay Payment — UPI QR Code
- **URL**: https://checkout.appypie.com/index/pay
- **Description**: After entering contact details, the full Razorpay payment interface appears showing payment options.
- **Key UI Elements**:
  - Left panel: Monthly Basic, Price Summary ₹5, "Using as +91 98913 47174"
  - Right panel — Payment Options:
    - Recommended tab: UPI option with provider icons
    - UPI QR tab (selected): Shows a scannable QR code
    - "Scan the QR using any UPI App" instruction
    - UPI app icons below QR code (PhonePe, Google Pay, Paytm, etc.)
    - Cards option also available
    - Timer: 11:53 countdown
  - "By proceeding, I agree to Razorpay's Privacy Notice · Edit Preferences"
  - "Secured by Razorpay" footer
  - "Test Mode" ribbon
- **Action Taken**: User completes UPI payment (in test mode, this is simulated).

---

## Step 12: Payment Successful
- **URL**: https://checkout.appypie.com/index/pay
- **Description**: Payment confirmation screen showing successful transaction.
- **Key UI Elements**:
  - Left panel: Monthly Basic, Price Summary ₹5, "Using as +91 98913 47174"
  - Right panel (green background):
    - "You will be redirected in 2 seconds"
    - "Payment Successful" heading
    - Large green checkmark icon
    - Transaction details:
      - Plan: Monthly Basic — ₹5
      - Date: Apr 11, 2026, 9:51 AM
      - Method: UPI
      - Transaction ID: pay_Sc3GnljqG3HGm4 (with copy icon)
    - "Visit razorpay.com/support for queries"
    - "Secured by Razorpay" footer
  - "Test Mode" ribbon
- **Action Taken**: Page auto-redirects after 2 seconds.

---

## Step 13: Trial Success — Loading
- **URL**: https://snappy.appypie.com/app/trialsuccess
- **Description**: After payment, the user is redirected to a trial success page that shows a loading spinner while the app is being provisioned.
- **Key UI Elements**:
  - Appy Pie Builder logo (top-left)
  - "Welcome" text (top-right)
  - Colorful loading spinner (center)
- **Action Taken**: Page loads automatically and redirects to the business dashboard.

---

## Step 14: Business Dashboard
- **URL**: https://snappy.appypie.com/user/app/business-dashboard/MTFhMTNhYzgwMzAx
- **Description**: The business dashboard shows the newly created app and trial details.
- **Key UI Elements**:
  - App info: name "app", BID: 11a13ac80301, Business Created Date: 2026-04-11
  - App card: "app — Customize and enhance your App" with "Manage App →" button (blue)
  - "What's included with your trial" section:
    1. **Get Website** — website/template icon with checkmark
    2. **Get Domain** — www domain icon with checkmark
    3. **Get Business Email** — email/message icon with checkmark
  - "Connect With Expert" link (top-right)
  - "Welcome" dropdown (top-right)
  - Language selector: "English" (top-right)
  - Delete icon (trash can, top-right of app card)
- **Action Taken**: User clicks "Manage App →".

---

## Step 15: Setting Up Your App
- **URL**: https://snappy.appypie.com/user/app/business-dashboard/MTFhMTNhYzgwMzAx
- **Description**: A modal overlay appears while the app is being set up and configured.
- **Key UI Elements**:
  - Modal dialog:
    - Loading spinner
    - "Setting Up Your App" heading
    - "Almost ready..." subtext
  - Background: Business dashboard (same as Step 14, slightly blurred)
- **Action Taken**: Automatic — modal dismisses when setup is complete.

---

## Step 16: App Dashboard — Welcome User
- **URL**: https://snappy.appypie.com/user/app/11a13ac80301
- **Description**: The main app management dashboard after the app is set up. Shows app details, plan information, and trial expiry.
- **Key UI Elements**:
  - Left Sidebar Navigation:
    - Home (selected)
    - My apps
    - Users
    - Advertisement & Marketing (expandable)
    - Analytics
    - Integrations
    - Miscellaneous (expandable)
    - testqa.delhi21 (user profile, expandable)
    - Change Language (English)
    - Connect With Expert
    - Billing Info
    - Logout
  - Main Content:
    - Breadcrumb: "Business Dashboard / app"
    - "Welcome User" heading
    - App card: name "app", BID: 11a13ac80301, "Basic Monthly" plan
    - Trial notice (red text): "(Your trial period expires on 18 Apr 2026 UTC)"
    - "Upgrade Now" link
    - "Edit App" button (blue, with pencil icon)
    - Three-dot menu (⋮)
  - Action Cards:
    1. **Test Your App** — "Preview and test your application on real devices" with "Test on Mobile" button
    2. **Publish your app** — "Deploy your app to Google Play and App Store" with "Publish Now" button
- **Action Taken**: User clicks "Edit App".

---

## Step 17: App Editor — Loading
- **URL**: https://snappy.appypie.com/appmakr/creator-software/build
- **Description**: The app editor loads, showing a colorful loading spinner while initializing the editor environment.
- **Action Taken**: Automatic — editor loads.

---

## Step 18: App Editor — Home Page
- **URL**: https://snappy.appypie.com/appmakr/creator-software/build
- **Description**: The full app editor interface where users can customize their app pages, sections, and content.
- **Key UI Elements**:
  - Top bar: "← App Manager" link, "Editor — Page: Home", Undo/Redo buttons, "Save" button (blue)
  - Left Sidebar — Pages:
    - Home (selected)
    - About Us
    - Contact
    - Appointment
  - Main Editor Area (Website/Desktop view):
    - Header: "Innovate Your Business: Elevate Your Success Story"
    - Body text: "Welcome to Business Solutions Hub, where innovation meets success. Explore a comprehensive suite of tools and insights designed to elevate your business and drive unparalleled success."
    - "Get Started" button (teal/green)
    - Business images section
    - Additional content block: "You might envision the birth of a business or the evolution of a cherished pastime into something more..."
  - Context menu (right-click on section):
    - "EDIT SECTION" button
    - Up/Down arrows, Copy, Delete icons
    - "REMOVE" button (red)
- **Action Taken**: User explores the editor, right-clicks on a section to see editing options.

---

## Step 19: Add Features Dialog
- **URL**: https://snappy.appypie.com/appmakr/creator-software/build
- **Description**: The "Add Features" modal allows users to add new pages/features to their app.
- **Key UI Elements**:
  - Modal header: "Edit Feature" tab, "Add Features" heading, Close (×) button
  - Left sidebar categories:
    - All (selected)
    - Business & Commerce
    - Information & Content
    - Multimedia & Social Interaction
    - Education
    - Location & Services
  - Feature list (right side):
    - About Us
    - App Sheet
    - Auction (gold/premium badge)
    - Audio
    - Blog
    - Chat
    - Codepage (gold/premium badge)
    - Add Folder
  - Search field: "Search feature" with magnifying glass icon
  - Right preview panel: Shows phone mockup with "Appointment" feature and "Form Builder" widget
  - Pages sidebar (behind modal): Home, About Us, Contact, Appointment with Add Features (+) button
- **Action Taken**: User browses available features.

---

## Step 20: Editor — About Us Page (Loading)
- **URL**: https://snappy.appypie.com/appmakr/creator-software/build
- **Description**: The editor switches to display the "About Us" page, showing a loading spinner while content loads.
- **Key UI Elements**:
  - Top bar: Mobile/Desktop toggle, "Editor — Page: About Us", Undo/Redo, "Save" button (red/active state)
  - Left sidebar: Pages list (Home, About Us, Contact, Appointment) with Add Features (+) button
  - Main area: Loading spinner
- **Action Taken**: Page content loads.

---

## Step 21: Congratulations — App Saved
- **URL**: https://snappy.appypie.com/appmakr/creator-software/build
- **Description**: After saving changes, a congratulations modal appears with a QR code for testing the app on a mobile device.
- **Key UI Elements**:
  - Modal dialog:
    - "Congratulations" heading
    - "You can see the reflection of your latest updates on your app. Scan the QR code below to view your updated app."
    - QR code image (scannable)
    - Divider: "What's Next"
    - App icon with "APP" text and upload arrow
    - "Publish your App" heading
    - "Launch your app on Google Play Store and the App Store, and make it accessible for users to download instantly."
    - "Publish Now" link
    - "DON'T SHOW THIS AGAIN" checkbox
    - "Done" button (blue)
  - Background: Editor showing About Us page with team member "Sarah Johnson, Director"
  - Left sidebar with pages including the newly added "About Us" page
- **Action Taken**: User clicks "Done" to dismiss the modal.

---

## Key URLs in the Flow
| Step | URL | Purpose |
|------|-----|---------|
| 1 | https://www.appypie.com/app-builder/appmaker | Landing page |
| 2-3 | https://snappy.appypie.com/app-builder/creator-software/ | App creation wizard |
| 4 | https://accounts.appypie.com/register | Registration |
| 5 | https://accounts.appypie.com/login | Login |
| 6-7 | https://snappy.appypie.com/app-builder/creator-software | Onboarding |
| 8 | https://snappy.appypie.com/user/app/upgrade-app/{BID} | Upgrade/pricing |
| 9-12 | https://checkout.appypie.com/index/pay | Razorpay checkout |
| 13 | https://snappy.appypie.com/app/trialsuccess | Trial success |
| 14-15 | https://snappy.appypie.com/user/app/business-dashboard/{encoded_BID} | Business dashboard |
| 16 | https://snappy.appypie.com/user/app/{BID} | App dashboard |
| 17-21 | https://snappy.appypie.com/appmakr/creator-software/build | App editor |

---

## Test Account Details
- **Email**: testqa.delhi21@gmail.com
- **Phone**: +91 9891347174
- **Business ID (BID)**: 11a13ac80301
- **Plan**: Basic Monthly
- **Price**: ₹5 (Test Mode)
- **Payment Gateway**: Razorpay (Test Mode)
- **Payment Method**: UPI
- **Transaction ID**: pay_Sc3GnljqG3HGm4
- **Trial Expiry**: 18 Apr 2026 UTC
- **Business Created**: 2026-04-11

---

## App Structure (Post-Creation)
The app is created with the following default pages:
1. **Home** — Business landing page with hero section, images, and CTA
2. **About Us** — Team information with member profiles (e.g., Sarah Johnson, Director)
3. **Contact** — Contact information page
4. **Appointment** — Appointment booking/scheduling feature

---

## Key Observations
- The flow uses Razorpay in **Test Mode** (indicated by the red "Test Mode" ribbon on the checkout page).
- The INR trial price is **₹5** for the Basic Monthly plan.
- The trial period lasts **7 days** (created April 11, expires April 18, 2026).
- The onboarding questionnaire has two screens: usage purpose (required) and referral source (optional).
- Google Sign-in popup appears automatically on the registration page.
- The app editor supports both mobile and desktop preview modes.
- Features can be added from categorized lists (Business & Commerce, Information & Content, etc.).
- After saving, a QR code is generated for mobile testing.
- Security badges on the payment page include SSL, PCI DSS, McAfee, Visa Verified, and MasterCard SecureCode.
