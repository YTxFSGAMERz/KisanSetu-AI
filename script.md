# 🎤 KisanSetu AI — Presentation Script
**Smart India Hackathon 2026 · Problem Statement SIH26032**

---

> ### 🎭 Speaker Key
> | Symbol | Speaker | Role |
> |:---:|---|---|
> | 👑 **[FARHAN]** | Farhan | **Main Presenter** |
> | 💜 **[PRACHI]** | Prachi Pandey | **Co-Leader** |
> | 🔵 **[VEDANT]** | Vedant | Member |
> | 🟢 **[MITANSH]** | Mitansh Soliya | Member |
> | 🟠 **[RUDRA]** | Rudra | Member |
> | 🔴 **[AJAY]** | Ajay Patra | Member |

> **Total slides:** 6 | **Suggested total time:** 7–8 minutes + Q&A

---

## 🟩 SLIDE 1 — Title Page

### 👑 [FARHAN]
*(Walk up confidently, stand centre-stage, make eye contact with the panel)*

> "Good [morning / afternoon], respected judges and honoured guests.
>
> My name is Farhan. I am the team leader of **KisanSetu AI** — Team ID **SIH2026-APP-7729**, competing under **Problem Statement SIH26032** for Smart India Hackathon 2026.
>
> The theme is **Smart Automation**, and the problem we are solving is something that affects every farmer in India — long waiting times and complete uncertainty about procurement status at government Mandis.
>
> Before I begin, a quick introduction to my team."

### 💜 [PRACHI] *(Step forward)*

> "I am Prachi Pandey, co-leader of the team. Alongside me are our members — Vedant, Mitansh, Rudradev, and Ajay. Together, we designed, built, and deployed this platform end-to-end."

### 👑 [FARHAN]

> "Let's get into it."

---

## 🟧 SLIDE 2 — End-to-End Workflow & Solution Overview

### 👑 [FARHAN]
*(Gesture towards the slide. Speak with energy.)*

> "India has over 7,000 APMC Mandis. Every harvest season, millions of farmers drive their tractors there — sometimes travelling hours — only to wait in line for 12, 24, even 48 hours. They don't know when their turn is. They don't know the procurement schedule. And once their crop is sold, they have zero visibility on whether their MSP payment has gone through.
>
> That is the problem. And **KisanSetu AI** is our solution — one digital bridge for every Mandi."

### 💜 [PRACHI]
*(Take over smoothly — gesture to the bullet points on the left side)*

> "Our platform covers the **entire procurement lifecycle** — five key pillars:
>
> **First — Smart Slot Booking.** Farmers select their centre, crop, and preferred time. Our engine automatically ranks the less-congested options so they pick the best slot.
>
> **Second — Digital Token.** A unique digital token replaces the physical queue. The farmer can track their position from home — no need to sit at the Mandi.
>
> **Third — Live Queue.** WebSockets keep both the farmer's screen and the officer's screen in sync in real time — the moment a token is called, everyone knows.
>
> **Fourth — Digital Procurement.** The officer grades the crop, records the procurement, and generates the receipt — all in one digital workflow. Zero paper.
>
> **Fifth — Payment Visibility.** Farmers can track their payment status from Pending to Completed without making a single extra trip to the Mandi."

### 🔵 [VEDANT]
*(Point to the system flow diagram on the right)*

> "And if you look at the system flow — it's a clean, linear pipeline:
>
> Farmer logs in → books an AI-ranked slot → receives a digital token → follows the live queue → the officer calls and grades → procurement is recorded → payment is tracked.
>
> The architecture underneath is a classic layered system: the user layer, the Next.js web app, the FastAPI backend with real-time WebSockets, the smart engine, the PostgreSQL data layer, and finally — notifications and analytics on top."

---

## 🟨 SLIDE 3 — Technical Approach

### 🟢 [MITANSH]
*(Speak clearly and confidently — this is the technical slide)*

> "Let me walk you through our technical design.
>
> Our **frontend** is built with **Next.js 16** and TypeScript, styled with Tailwind CSS — fast, server-rendered, and mobile-responsive.
>
> The **backend** runs on **FastAPI with Python 3.13**, using async SQLAlchemy 2.0 and Pydantic v2 for fully typed, asynchronous API handling.
>
> For **real-time updates**, we use **WebSockets** — every token call, queue position change, and alert is pushed live to both the farmer and officer screens without any page refresh.
>
> The **AI Smart Engine** is our custom-built scoring system. It calculates predicted wait times and congestion scores based on queue length, processing time, and active counters — and ranks open slots accordingly. It's fully explainable — no black box.
>
> The **data layer** uses PostgreSQL and Supabase in production, and SQLite for local development.
>
> **Security** is JWT-based with three role levels — Farmer, Officer, and Admin — each seeing only what they need.
>
> And for **deployment**, we use Docker Compose locally, with the frontend hosted live on Vercel."

---

## 🟦 SLIDE 4 — Feasibility & Viability

### 🟠 [RUDRA]
*(Speak with conviction — judges look for this)*

> "Now — is this actually feasible in the real world? Absolutely. Let me explain why.
>
> Our entire stack is **open-source** — FastAPI, Next.js, PostgreSQL, WebSockets. No proprietary licences. No expensive cloud services. This dramatically reduces implementation cost for any state government or APMC board.
>
> The backend is **modular** — async SQLAlchemy with separate routers and services. That means each part — queue, procurement, payments, analytics — can be maintained or upgraded independently.
>
> Our smart engine uses **explainable scoring** — wait-time calculation and congestion ranking that works without any large training dataset or ML infrastructure. It runs right on our backend.
>
> And the whole system is **Docker Compose deployable** — a Mandi operator can run this with one command."

### 💜 [PRACHI]
*(Shift to the Challenges and Solutions panel on the right)*

> "We also thought hard about the challenges we'd face in the field:
>
> **Challenge 1 — Long queues and uncertainty?**
> We solve it with slot booking and live digital tokens. Farmers don't queue blindly anymore.
>
> **Challenge 2 — Congestion varies by centre?**
> Our engine ranks slots dynamically using real queue length, processing time, and active counters — so recommendations adapt to each Mandi's actual conditions.
>
> **Challenge 3 — Network interruptions?**
> We've kept the core workflow lightweight and fully functional in local development — so even poor connectivity doesn't break the experience.
>
> **Challenge 4 — Scaling across thousands of Mandis?**
> Our plan is a phased rollout — pilot selected centres, integrate their data, validate, and then expand state-by-state."

---

## 🟩 SLIDE 5 — Impact & Benefits

### 🔴 [AJAY]
*(This is an impactful slide — deliver it with energy)*

> "Let's talk about what this actually means for people on the ground.
>
> For **farmers** — they reserve their slot before they even leave home. They follow their token remotely. No wasted travel. No uncertainty. Fewer repeat visits to the Mandi just to check on payment status.
>
> For **officers** — a structured token flow means they can process farmers in sequence, efficiently. No physical crowd management. No paperwork hunting.
>
> For **Mandi administrators** — queue data gives them visibility into staffing needs, peak times, and capacity — so they can plan better.
>
> And for **the government** — every transaction is digital. Every record is traceable. That's a foundation for audit, accountability, and policy decisions."

### 👑 [FARHAN]
*(Point to the three impact indicators and wrap up the slide)*

> "The target impact numbers:
>
> **7,000+ Mandis** — our target scale across India.
> **23% estimated reduction** in farmer wait times.
> **Lakhs of farmers** reached through the digital workflow.
>
> Socially — fewer repeat trips, clearer queue expectations.
> Economically — better Mandi throughput and full payment visibility.
> For governance — digital records and queue analytics that don't exist anywhere today."

---

## 📚 SLIDE 6 — Research & References

### 👑 [FARHAN]
*(Keep this brief — it's a closing/credibility slide)*

> "Our solution is grounded in verified, government-backed research.
>
> We referenced the official SIH portal, the e-NAM national agriculture market platform, the FCI Annual Report 2024–25 which documents MSP procurement and bank payments, the FCI Procurement Action Plan for centre operations and quality checks, and the Department of Consumer Affairs as our primary government source.
>
> The full source code, architecture, API design, seed data, and tests are available on our GitHub repository. And the live demo is deployed right now at **kisansetu-sih.vercel.app** — you can open it on your phone during this presentation.
>
> Everything we've described today is live, tested, and working in production."

### 👑 [FARHAN] + 💜 [PRACHI] + ALL MEMBERS
*(All stand together, face the panel)*

> "Thank you.
>
> We are Team KisanSetu AI — Team ID SIH2026-APP-7729 — solving Problem Statement SIH26032.
>
> Smart Procurement. Smart Queues. Empowered Farmers.
>
> We're happy to take your questions."

---

## 🙋 Q&A — Likely Judge Questions & Answers

> Decide who answers before the presentation!

---

### 👑 [FARHAN] handles:

**Q: Is this actually live, or is it just a prototype?**
> "It's live in production. Visit kisansetu-sih.vercel.app right now. You can log in with a demo farmer account and go through the complete flow — slot booking, token, live queue, procurement, payment — all working."

**Q: How is this different from e-NAM or existing government portals?**
> "e-NAM handles price discovery and online trading. It does not handle the physical queue at the Mandi on procurement day. KisanSetu AI solves the last mile — the actual day a farmer shows up, the actual queue, the actual token, the actual receipt. No existing government platform does this end-to-end."

**Q: What happens to farmers who don't have smartphones?**
> "Notifications can be sent via SMS to any feature phone. The token number and queue status can be communicated through the Mandi helper desk. The digital workflow on the officer's side still works — the farmer just needs their token number, not necessarily the app."

---

### 💜 [PRACHI] handles:

**Q: What AI model powers the slot recommendation?**
> "We built a custom, explainable three-layer scoring algorithm — no external AI model. Layer one predicts wait time from queue length, processing time per farmer, crop complexity, and active counters. Layer two computes a congestion score from 0 to 100. Layer three ranks all open slots and returns the top recommendations with plain-language reasons. It runs entirely on our FastAPI backend."

**Q: How do you plan to scale to 7,000 Mandis?**
> "Phased rollout — start with a pilot of 10 to 15 Mandis in one district. Validate the workflow, collect data, fix edge cases, then expand state-by-state. The database layer uses PostgreSQL with read-replica support, so horizontal scaling is built in."

---

### 🟢 [MITANSH] / 🔵 [VEDANT] handle:

**Q: What is the infrastructure cost?**
> "For the pilot, zero. Vercel free tier for the frontend, Supabase free tier for the database, GitHub Actions for CI/CD. At scale, a standard cloud PostgreSQL instance and Vercel Pro would be needed — easily within any state government's IT budget."

**Q: How many tests do you have, and are they passing?**
> "We have 13 tests covering core API routes, the smart engine, and queue state transitions. All 13 are passing as of today."

---

### 🟠 [RUDRA] handles:

**Q: Can you explain the AI algorithm simply?**
> "Think of it like choosing a lane at a toll booth. We check how many vehicles are ahead, how fast that booth is processing, and how busy it's been today. We do the same for each Mandi slot and tell the farmer which 'lane' will get them through fastest — with the reason written in plain language."

---

*Script prepared for KisanSetu AI · SIH 2026 · Team ID: SIH2026-APP-7729 · 6 Slides*