# 🌾 KisanSetu AI — Smart Procurement Management Platform

[![Next.js 16](https://img.shields.io/badge/Frontend-Next.js_16_(TypeScript)-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://kisansetu-sih.vercel.app)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_(Python_3.13)-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://kisansetu-sih.vercel.app)
[![Tests Passing](https://img.shields.io/badge/Tests-13%20Passing-2ea44f?style=for-the-badge&logo=github-actions&logoColor=white)](#-tests)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](#)

> **Smart India Hackathon 2026 — Problem Statement 26032**  
> **Organization:** Ministry of Consumer Affairs, Food & Public Distribution  
> **Department:** Department of Consumer Affairs (DoCA)  
> **Theme:** Smart Automation  
> **🌐 Live Production Web App:** [kisansetu-sih.vercel.app](https://kisansetu-sih.vercel.app) *(Mirror: [kisansetu-india.vercel.app](https://kisansetu-india.vercel.app))*

---

## 🎯 Problem Statement

Farmers across India face **excessive waiting times**, **lack of transparent scheduling**, and **uncertainty regarding crop grading and payment status** at Government procurement centres (Mandis). This results in massive congestion, regional bottlenecks, and distress crop sales.

## ✅ The Solution

**KisanSetu AI** is an end-to-end digital procurement ecosystem bridging farmers, procurement officers, and government authorities through real-time queue automation, dynamic slot allocation algorithms, and instant MSP tracking.

| Feature | Description |
| :--- | :--- |
| 📅 **Smart Slot Booking** | Farmers schedule procurement visits digitally from any mobile device |
| 🤖 **AI Recommendation Engine** | Dynamic algorithm ranks slots by wait time, capacity, and current traffic |
| 🎫 **Digital Token System** | Automated unique queue tokens assigned upon booking confirmation |
| 📡 **Real-Time Websocket Queue** | Zero-refresh live queue tracking powered by bi-directional WebSockets |
| ⚖️ **Digital Procurement Desk** | Officers perform digital grading and emit instant verifiable receipts |
| 💰 **MSP Payment Tracking** | End-to-end transparency tracking payments from `PENDING` → `COMPLETED` |
| 🔔 **Multi-Channel Alerts** | Real-time in-app updates complemented by SMS notifications |
| 📊 **National Analytics Panel** | Regional Mandi congestion heatmaps, daily processing volumes, and payout tracking |

---

## 🎬 Live Interactive Role Portals

Test the platform instantly with single-click server-authenticated demo profiles (zero login manual entries required in demo mode):

| Portal Role | Primary Capabilities | Demo Shortcut URL |
| :--- | :--- | :--- |
| 👨‍🌾 **Farmer Portal** | Slot booking, live digital queue token, MSP payout status | [Launch Farmer Demo](https://kisansetu-sih.vercel.app/login?demo=farmer) |
| 🏛️ **Procurement Officer** | Counter desk queue calling, digital grading, instant receipt generator | [Launch Officer Demo](https://kisansetu-sih.vercel.app/login?demo=officer) |
| 📊 **Government Admin** | Regional congestion heatmaps, daily volumes, national MSP rate metrics | [Launch Admin Demo](https://kisansetu-sih.vercel.app/login?demo=admin) |

> **Security Architecture Note**: In demo mode (`DEMO_MODE=true`), authentication relies on server-side isolated JWT generation. In production, secure JWT authentication with encrypted passwords/OTP is strictly enforced via environment variables.

---

## 🏗️ Architecture & Technology Stack
