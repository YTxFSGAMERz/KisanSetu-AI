# KisanSetu Notifier

A standalone Python desktop notifier for KisanSetu AI that:

- 🖥️ Sits in the **Windows system tray**
- 🔔 Shows **custom popup notifications** at the bottom-right corner of your screen
- 🚫 **Does NOT use Windows Action Center** — it renders its own PyQt5 window, completely bypassing OS notification settings
- ⚡ Connects to the KisanSetu backend via **WebSocket** (no polling)

---

## Setup

### 1. Install dependencies

```bash
cd kisansetu_notifier
pip install -r requirements.txt
```

### 2. Configure

Edit `notifier.env` with your KisanSetu login:

```dotenv
KISANSETU_API_URL=http://localhost:8000
KISANSETU_WS_URL=ws://localhost:8000
KISANSETU_EMAIL=your_email@example.com
KISANSETU_PASSWORD=your_password
KISANSETU_USER_ID=1   # your user ID
```

### 3. Run

```bash
python main.py
```

A KisanSetu icon appears in the system tray. Trigger any event in the frontend (booking, token call, payment) and a popup will appear at the bottom-right of your screen.

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
- **Open KisanSetu** — opens the web app in your browser
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
