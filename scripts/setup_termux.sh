#!/data/data/com.termux/files/usr/bin/bash
grep -q "termux_sms_bridge.py" ~/.bashrc 2>/dev/null || echo "pgrep -f termux_sms_bridge.py >/dev/null || python ~/termux_sms_bridge.py &" >> ~/.bashrc
echo "Termux SMS Bridge autostart configured!"
