# 🎯 Standalone Handicapper Training Device

This is a **100% standalone, isolated training device** designed for personal handicapping practice and virtual bankroll tracking.

It operates in its own directory (`training_device/`), uses its own isolated database (`training_device/db/training_simulator.db`), and runs on its own dedicated web port (`8502`), ensuring **zero interference or integration with your main application**.

---

## 🚀 Quickstart Guide

### 1. Launch the Standalone Training Device
Run the following command from your terminal:

```bash
python -m streamlit run training_device/app.py --server.port 8502
```

Then open your browser to: **`http://localhost:8502`**

---

## 💡 Key Features

- **💰 Virtual Bankroll Manager**: Start with $1,000 (or custom balance) of fake money.
- **🎟️ Manual Bet Slip**: 100% manual wager control (Win, Place, Exacta, Trifecta).
- **⚡ Free Real-Time Feeds**: Connects to TAB Australia API & Equibase public charts at **$0.00 cost**.
- **📊 Settlement & PnL Analytics**: Auto-settle wagers against official Equibase & TAB results and track equity growth curves.
- **🔄 Account Reset**: Reset virtual bankroll back to $1,000 anytime.
