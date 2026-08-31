# Complete Guide: Setting Up `tel:` Links in Windows for Android & iPhone

This guide explains step-by-step how to configure Windows 10/11 so that clicking any `tel:` phone link (in a browser, CRM system, email, or application) automatically triggers a call using your **Android** or **iPhone** device via Microsoft **Phone Link**.

---

## 📋 Table of Contents
1. [Overview & Prerequisites](#overview--prerequisites)
2. [Setting Up `tel:` Link with Android](#setting-up-tel-link-with-android)
3. [Setting Up `tel:` Link with iPhone (iOS)](#setting-up-tel-link-with-iphone-ios)
4. [Configuring Windows `tel:` Default Protocol Handler](#configuring-windows-tel-default-protocol-handler)
5. [Browser & CRM Integration Setup](#browser--crm-integration-setup)
6. [Testing Your Setup](#testing-your-setup)
7. [Troubleshooting & FAQs](#troubleshooting--faqs)

---

## 1. Overview & Prerequisites

### How It Works
When you click a link formatted like `<a href="tel:+18005550199">Call Us</a>`, Windows checks its **Default Apps by Protocol** registry for the `TEL` link protocol handler. When mapped to **Phone Link**, Windows sends the telephone number to your connected mobile phone over Bluetooth to initiate the dialer.

### Requirements
* **Windows Version**:
  * **Android**: Windows 10 (with latest updates) or Windows 11.
  * **iPhone**: Windows 11 (Build 22621 or higher required for iOS support).
* **PC Requirements**: Bluetooth enabled on your computer.
* **Mobile Requirements**:
  * **Android**: Android 7.0 (Nougat) or newer.
  * **iPhone**: iOS 14.0 or newer.

---

## 2. Setting Up `tel:` Link with Android

### Step 1: Install Apps
1. **Windows PC**: Open the **Microsoft Store**, search for **Phone Link**, and ensure it is updated to the latest version.
2. **Android Phone**: Open **Google Play Store**, search for **Link to Windows** (by Microsoft), and install/update it. *(Note: On Samsung and Surface Duo devices, Link to Windows is built-in under Quick Settings).*

### Step 2: Pair PC and Android Phone
1. Launch **Phone Link** on your Windows PC and click **Android**.
2. A QR code will appear on your PC screen.
3. Open **Link to Windows** on your Android phone and tap **Link your phone and PC** -> **Continue**.
4. Scan the QR code on your PC screen using your phone camera.
5. Sign in with the same **Microsoft Account** on both devices if prompted.
6. Grant required permissions on your phone (Contacts, Phone Calls, SMS, Notifications).

### Step 3: Enable Bluetooth Calling
1. In the Windows **Phone Link** app, click the **Calls** tab on the top menu.
2. Click **Get Started** / **Set up calls**.
3. A Bluetooth pairing request will pop up on both your PC and phone. Confirm that the PIN numbers match and accept pairing.
4. Allow permission on your phone for **Call Logs** and **Bluetooth Audio Sharing**.

---

## 3. Setting Up `tel:` Link with iPhone (iOS)

> ⚠️ **Note**: iPhone integration with Phone Link requires **Windows 11** and Bluetooth on your PC.

### Step 1: Install Apps
1. **Windows PC**: Open **Phone Link** on Windows 11.
2. **iPhone**: Open the **Apple App Store**, search for **Link to Windows**, and install it.

### Step 2: Pair PC and iPhone via Bluetooth
1. Launch **Phone Link** on your PC and select **iPhone**.
2. A QR code will display on your screen.
3. Open the **Link to Windows** app on your iPhone and scan the QR code.
4. Turn on **Bluetooth** on your iPhone.
5. Accept the Bluetooth pairing prompt on both your iPhone and PC.

### Step 3: Grant iOS Permissions (Crucial for Calling)
1. On your iPhone, open **Settings** -> **Bluetooth**.
2. Find your PC's name in the device list and tap the **(i)** info icon next to it.
3. Toggle **ON** the following settings:
   * **Show Notifications**
   * **Sync Contacts**
4. Open Phone Link on your PC and complete the setup wizard.

---

## 4. Configuring Windows `tel:` Default Protocol Handler

Once your phone is connected to Phone Link, you must assign **Phone Link** as the default handler for `tel:` links in Windows.

### For Windows 11:
1. Press `Win + I` to open **Settings**.
2. Go to **Apps** -> **Default apps**.
3. Scroll down to the bottom and click **Choose defaults by link type** (or type `TEL` into the search bar under *Set defaults for applications*).
4. Find the **TEL** entry (URL:TEL / Phone Link).
5. Click on the existing default app (e.g., Chrome, Skype, or FaceTime) and select **Phone Link**.
6. Click **Set default**.

### For Windows 10:
1. Press `Win + I` to open **Settings**.
2. Go to **Apps** -> **Default apps**.
3. Scroll to the bottom and click **Choose default apps by protocol**.
4. Scroll down the left column until you find **TEL** (URL:tel).
5. Click the app currently listed next to **TEL** and choose **Phone Link** from the popup menu.

---

## 5. Browser & CRM Integration Setup

### Web Browsers (Google Chrome / Microsoft Edge / Firefox)
When you click a `tel:` link in a web page or CRM system, browsers may display a prompt asking for permission:
1. When you click a phone link (e.g., `<a href="tel:+18005550199">...</a>`), your browser will show a prompt:
   * *"Open Phone Link?"* or *"Allow website to open tel links?"*
2. Check the box **"Always allow [domain] to open links of this type in the associated app"**.
3. Click **Open Phone Link**.

### Formatting Phone Links in HTML / CRM Templates
To ensure phone numbers are clickable in your web applications or CRM, format them using standard HTML `tel:` protocol:

```html
<!-- Standard tel link format -->
<a href="tel:+18005550199">+1 (800) 555-0199</a>

<!-- E.164 international format is recommended -->
<a href="tel:+13055550123" class="phone-link">
  <i class="fa fa-phone"></i> Call Customer
</a>
```

---

## 6. Testing Your Setup

You can test whether the `tel:` protocol works without opening a browser:

1. Press `Win + R` on your keyboard to open the **Run** dialog box.
2. Type: `tel:+18005550199` and press **Enter**.
3. **Expected Behavior**:
   * Windows launches **Phone Link**.
   * Phone Link automatically opens the dialer pre-filled with `+18005550199`.
   * Click the green **Call** button in Phone Link (or hit Enter) to dial out through your connected Android or iPhone.

---

## 7. Troubleshooting & FAQs

### Q1: When I click `tel:`, Skype/Teams/Chrome opens instead of Phone Link.
* **Fix**: Re-check **Default Apps by Protocol** in Windows Settings (Section 4). Ensure `TEL` is explicitly set to **Phone Link**.

### Q2: Phone Link opens, but the call button is grayed out or fails.
* **Fix**:
  1. Ensure Bluetooth is enabled on both PC and mobile device.
  2. Unpair and re-pair Bluetooth on both devices.
  3. On Android: Ensure battery saver isn't restricting **Link to Windows**.
  4. On iPhone: Ensure **Sync Contacts** and **Show Notifications** are enabled under iPhone Bluetooth settings for the paired PC.

### Q3: Can I make calls without my phone being nearby?
* No. Phone Link routes audio and cellular signals through your connected phone via Bluetooth and Wi-Fi. Your phone must be powered on and within Bluetooth range.

### Q4: Does iPhone support receiving incoming call audio on PC?
* Yes, Windows 11 Phone Link supports both placing outgoing calls and receiving incoming calls for iPhone over Bluetooth hands-free profile (HFP).
