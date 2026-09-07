# KisanSetu Notifier

A standalone Python desktop notifier for KisanSetu AI that:

- 🖥️ Sits in the **Windows system tray**
- 🔔 Shows **custom popup notifications** at the bottom-right corner of your screen
- 🚫 **Does NOT use Windows Action Center** — it renders its own PyQt5 window, completely bypassing OS notification settings
- ⚡ Connects to the KisanSetu backend via **WebSocket** (no polling)

---

## Quick Start (Zero Config Needed!)

The notifier **automatically detects credentials and backend URLs from the project root `.env`**. By default, it connects as the demo farmer (`demo.farmer@example.com`) to instantly receive slot confirmations, queue calls, and payment updates.

### 1. Instant Test (No backend needed)
Test the pop-up notification window on your screen right away:
```bash
python kisansetu_notifier/main.py --test
# or
python kisansetu_notifier/popup.py
```

### 2. Run Notifier with Live KisanSetu Backend
```bash
python kisansetu_notifier/main.py
```
*(Or simply run `.\start.bat` from the root folder — it automatically starts Backend, Frontend, and Notifier together!)*

A green KisanSetu icon appears in your system tray and a welcome pop-up will notify you that alerts are live.

---

## SMS via ADB (Android Phone)

To also send real SMS to farmers via your USB-connected Android phone:

### One-time phone setup (~2 minutes)

1. Enable **USB Debugging** on your Android phone  
   *(Settings → About Phone → tap Build Number 7 times → Developer Options → USB Debugging)*

2. Install **Termux** from [F-Droid](https://f-droid.org/en/packages/com.termux/)

3. Install **Termux:API** from [F-Droid](https://f-droid.org/en/packages/com.termux.api/)

4. Open Termux and run:
   ```bash
   pkg install termux-api
   ```

5. Grant SMS permission to **Termux:API** when prompted

6. Plug phone into PC via USB → tap **"Allow USB Debugging"** on the phone

7. Verify on PC:
   ```bash
   adb devices
   # Should show your phone (e.g., "emulator-5554  device")
   ```

8. Test SMS directly:
   ```bash
   adb shell termux-sms-send -n +91XXXXXXXXXX "KisanSetu test SMS"
   ```

### Enable in backend

In `backend/.env`:
```dotenv
SMS_PROVIDER=ADB
```

Restart the backend — SMS will now fire through your phone's SIM automatically on bookings, token calls, and payments.

---

## Tray Menu
 
Right-click the tray icon for:
- **Open KisanSetu Web App** — opens the web app in your default browser (`http://localhost:3000`)
- **🔔 Send Test Notification** — immediately tests a popup card on screen
- **Reconnect** — manually restart the WebSocket connection
- **Quit** — exit the notifier

---

## Popup Events

| Event | Icon | When it fires |
|-------|------|--------------|
| `FARMER_CALLED` | 🔔 | Officer calls a token at the counter |
| `BOOKING_CONFIRMED` | ✅ | A farmer's booking is confirmed |
| `PAYMENT_UPDATED` | 💰 | Payment is sent to a farmer |
| `NOTIFICATION` | 🌾 | General system notifications |
| `QUEUE_UPDATED` | 📋 | Queue state changes (optional) |

Configure which events trigger popups via `NOTIFY_EVENTS` in `notifier.env`.
