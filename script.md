# 🎤 KisanSetu AI — Presentation Script
**Smart India Hackathon 2026 · Problem Statement 26032**

---

> ### 🎭 Speaker Key
> | Symbol | Speaker | Role |
> |:---:|---|---|
> | 👑 **[FARHAN]** | YTxFSGAMERz | **Team Leader — Main Presenter** |
> | 💜 **[PRACHI]** | Prachi Pandey | **Co-Leader** |
> | 🔵 **[VEDANT]** | Vedant | **Member** |
> | 🟢 **[MITANSH]** | Mitansh Soliya | **Member** |
> | 🟠 **[RUDRA]** | Rudradev | **Member** |
> | 🔴 **[AJAY]** | Ajay Patra | **Member** |

---

## 🟩 SLIDE 1 — Title Slide

### 👑 [YOU] *(Stand confidently. Make eye contact with the judges.)*

> *"Good [morning/afternoon], respected judges and honoured guests.*
>
> *My name is [Your Name], and I am the team leader of **KisanSetu AI.***
>
> *Our Team ID is **SIH2026-APP-7729**, and we are presenting our solution for **Problem Statement 26032** under the Ministry of Consumer Affairs, Food & Public Distribution.*
>
> *The theme is **Smart Automation** — and today, we will show you how we automated the most painful part of a farmer's life: waiting at the Mandi.*
>
> *Before I begin, let me introduce my incredible team —"*

### 💜 [PRACHI] *(Step forward briefly)*

> *"I am Prachi, co-leader of the team. Alongside me are Vedant, Mitansh, Rudradev, and Ajay — together we built, tested, and deployed this platform in a live production environment.*
>
> *You can visit it right now at **kisansetu-sih.vercel.app**."*

### 👑 [YOU]

> *"Let's begin."*

---

## 🟧 SLIDE 2 — Problem → Solution

### 👑 [YOU]

> *"So — what exactly is the problem?*
>
> *Millions of Indian farmers drive their tractors to government Mandis every harvest season. They arrive hoping to sell their crop at the Minimum Support Price. But what greets them?*
>
> *Hours. Sometimes 12 hours. Sometimes 48 hours — of just… waiting. Waiting in the sun, with a tractor full of perishable grain, with no idea when their turn will come.*
>
> *There are **three core pain points** here:*
>
> ***One** — Long waiting times. Farmers queue for 12 to 48 hours at peak harvest.*
>
> ***Two** — No visibility. There is no way to know procurement schedules before even arriving.*
>
> ***Three** — Payment uncertainty. Once the crop is sold, farmers have no way to track if or when their MSP payment will arrive.*
>
> *These aren't minor inconveniences. This is a systemic failure affecting crores of farmers across India."*

### 💜 [PRACHI]

> *"And this is exactly what KisanSetu AI solves.*
>
> *We built a single, end-to-end digital platform — and I mean end-to-end.*
>
> *Farmers can now **book procurement slots from home**, from their mobile phone. Our **AI engine** analyses congestion and wait times and recommends the best slot for them.*
>
> *Once booked, they receive a **Digital Token** — unique, like A001 or A042.*
>
> *At the Mandi, they see **real-time live queue updates** powered by WebSockets — no manual refresh, no guessing.*
>
> *The officer grades the crop **digitally** on our platform, and a receipt is auto-generated.*
>
> *And every step of the **MSP payment** — from Pending to Processing to Completed — is tracked live by the farmer.*
>
> *One platform. Zero paperwork. Zero waiting blindly."*

---

## 🟨 SLIDE 3 — End-to-End Farmer Journey

### 🔵 [VEDANT]

> *"Let me walk you through the complete farmer journey — seven steps, zero paperwork.*
>
> ***Step 1: Register** — The farmer signs up on the platform from their mobile.*
>
> ***Step 2: Select Centre** — They choose their nearest APMC Mandi from our database of 15 live centres.*
>
> ***Step 3: Book Slot** — Our AI engine presents the best available time slots, ranked by predicted wait time and congestion.*
>
> ***Step 4: Get Token** — Instantly, a unique digital queue token is assigned — like A023 or B105.*
>
> ***Step 5: Live Queue** — On the day of procurement, the farmer can see their real-time position in the queue — live, on their phone.*
>
> ***Step 6: Procurement** — The officer at the Mandi calls the token digitally, grades the crop on the platform, and confirms the weight.*
>
> ***Step 7: Payment** — The MSP payment is calculated, a digital J-Form receipt is generated, and the farmer tracks the Direct Benefit Transfer in real-time.*
>
> *Seven steps. No paper. No uncertainty. Fully live at kisansetu-sih.vercel.app today."*

---

## 🟦 SLIDE 4 — Live Product: Discover & Book

### 👑 [YOU]

> *"Now — and this is the part I love — we are not going to show you mockups. We are going to show you the **real, deployed product**.*
>
> *This is the landing page of KisanSetu AI — live, right now, on the internet.*
>
> *When a farmer taps on 'Book a Slot,' they are taken to our AI recommendation screen.*
>
> *See this — the engine has analysed every open slot across the Mandi. It flags its own top pick — labelled **'Best Slot'** — with approximately zero minutes of predicted wait time, low congestion, and the exact reasoning shown to the farmer in plain language.*
>
> *The farmer doesn't need to understand algorithms. They just tap the green recommendation and confirm.*
>
> *That's it. Slot booked. Token assigned. In under a minute."*

---

## 🟩 SLIDE 5 — Live Product: Farmer Experience

### 🟢 [MITANSH]

> *"Here is the Farmer Dashboard — a real account, real data.*
>
> *You can see the farmer — Rajesh Verma — can view all his active bookings, his queue token, the expected wait time, and his upcoming slots at a glance.*
>
> *And this next screen — this is the Live Queue view. Rajesh holds **Token A023**.*
>
> *He can see exactly where he stands in the queue — in real time. The moment the officer calls A022, Rajesh's screen updates — automatically, instantly, via WebSocket.*
>
> *No phone calls to the Mandi. No driving there to check. Rajesh stays home, and the queue comes to him.*
>
> *Real names, real tokens, real rupee amounts — this is not a demo environment. This is production."*

---

## 🟥 SLIDE 6 — Live Product: Officer Desk

### 🔴 [AJAY]

> *"Now let's look at the other side — the officer's desk.*
>
> *When the officer is ready for the next farmer, they tap **'Call Next'** on the Officer Queue screen. The token is called, and every farmer in the queue sees their position update live.*
>
> *The officer then records the crop details — variety, weight, grade — all digitally, on our platform.*
>
> *Once confirmed, the system auto-generates a **Digital J-Form Receipt**.*
>
> *Look at this — Receipt RCP-DOCA-8779248. Rajesh Verma. 50 Quintals of Wheat. Grade A. Payment amount: **Rs. 1,13,750** via Direct Benefit Transfer.*
>
> *This receipt is tamper-proof, timestamped, and permanently stored. No more handwritten forms that can be altered. No more unauthorised deductions.*
>
> *The officer's entire workflow — from queue management to grading to receipt — happens in one place."*

---

## 🟪 SLIDE 7 — Government Control Room

### 💜 [PRACHI]

> *"And for the government — we built a national control room.*
>
> *The **National KPI Dashboard** gives Ministry officers and DoCA administrators a real-time bird's-eye view of procurement activity across all Mandis.*
>
> *They can see total bookings, payment rates, queue congestion heatmaps, and processing volumes — all live.*
>
> *But we went one step further. We integrated **live Agmarknet data** — the Government of India's own agricultural market data feed.*
>
> *Our platform automatically benchmarks the prices being paid at each Mandi against the official MSP. If a Mandi is paying below MSP, the system **flags it automatically** — giving the government instant visibility into compliance.*
>
> *This is not just a farmer-facing app. This is a governance tool."*

---

## 🟫 SLIDE 8 — Technical Architecture

### 👑 [YOU]

> *"Let me take a minute to talk about how we built this — because the technical depth here is real.*
>
> *Our **Frontend** is built with Next.js 16, TypeScript, and Tailwind CSS — with App Router for fast, server-rendered pages, and a WebSocket client for live queue updates.*
>
> *Our **Backend** is FastAPI on Python 3.13, with SQLAlchemy 2.0 async ORM and Pydantic v2 for type-safe data validation. Authentication is JWT-based.*
>
> *For the **Database**, we use SQLite in development and PostgreSQL in production, managed through Supabase CLI. We have a zero-downtime database store.*
>
> *Our **Infrastructure** runs on Docker Compose for local development, GitHub Actions for CI/CD, and Vercel for deployment.*
>
> *The numbers: **11 route modules, 11 ORM models, 2 WebSocket channels** — one for queue updates per centre, one for targeted farmer alerts.*
>
> *And **13 out of 13 tests passing** — right now, in our test suite."*

---

## 🟦 SLIDE 9 — Smart Recommendation Engine

### 🟠 [RUDRADEV]

> *"Now let me explain what makes KisanSetu AI actually 'smart' — the Recommendation Engine.*
>
> *It operates in three layers:*
>
> ***Layer 1: Predict Wait Time.***
> *We calculate the expected wait based on the current queue length, the average processing time per farmer, the complexity of the crop being processed, and the number of active counters at the Mandi. This gives us a predicted wait time in minutes.*
>
> ***Layer 2: Compute Congestion Score.***
> *We combine three signals — how full the slot is relative to capacity, how busy the queue is relative to the daily target, and the predicted wait time. These are weighted to produce a congestion score between 0 and 100.*
>
> ***Layer 3: Rank and Recommend Top 3.***
> *Each slot gets a final score based on occupancy, predicted wait, and congestion. The system returns the **top 3 slots** with a human-readable reason — like 'Low congestion, ~15 min estimated wait.'*
>
> *The congestion is labelled simply: Low, Moderate, High, or Very High — so even a first-time smartphone user understands exactly which slot to pick.*
>
> *The farmer gets intelligence. Without needing to understand any of the math."*

---

## 🟨 SLIDE 10 — Feasibility & Risk Mitigation

### 🔵 [VEDANT]

> *"A common question at this stage is — okay, this looks great in a hackathon. But will it actually work in the real world?*
>
> *Here is why it will.*
>
> *Our tech stack is **entirely open-source and free-tier deployable** — Vercel and Supabase, zero cost for initial rollout.*
>
> *A **one-click launcher** boots the backend, frontend, and notifier daemon concurrently — even a non-technical Mandi operator can set it up.*
>
> *Our **GitHub Actions pipeline** auto-refreshes 14-day slot schedules every week via cron — so future slots never expire, and there is no manual database maintenance.*
>
> *And the system is designed to **scale to 7,000+ APMC Mandis** across India through PostgreSQL read-replicas and caching.*
>
> *Now, we also anticipated the real challenges —*
>
> ***Challenge: Low smartphone penetration in rural areas.***
> *Solution: Multi-channel SMS via ADB USB bridge and MSG91 DLT — reaching any farmer on a 2G phone.*
>
> ***Challenge: Internet or server downtime at remote Mandis.***
> *Solution: A resilient dual-layer store — local SQLite and Next.js store — ensuring 100% offline uptime.*
>
> ***Challenge: Farmer adoption and digital literacy.***
> *Solution: Hindi and Gujarati regional UI, bilingual audio token calls, and Mandi helper desks for assisted onboarding.*
>
> *We didn't just build for the best case. We built for the field."*

---

## 🟩 SLIDE 11 — Impact & Benefits

### 💜 [PRACHI]

> *"Let's talk impact — real, measurable impact.*
>
> *Our internal simulation shows a **23.3% average reduction in wait times** — from 241 minutes down to 185 minutes. That's nearly an hour saved per farmer per visit.*
>
> *We're targeting **7,000+ APMC Mandis** across India — scalable via PostgreSQL read-replicas.*
>
> *Right now, our prototype covers **15 Mandis, 19 crops**, with all **13 tests passing** — zero paper receipts.*
>
> *The **social impact** is significant:*
> *— We eliminate those 12 to 48 hour tractor roadblocks at peak harvest.*
> *— We prevent post-harvest spoilage that happens when grain sits open in queue delays.*
>
> *The **economic impact** is equally powerful:*
> *— Our tamper-proof digital J-Form receipts stop unauthorised deductions that farmers suffer today.*
> *— DBT tracking prevents middleman and commission-agent leakage — every rupee goes directly to the farmer.*
>
> *And for **government**:*
> *— Ministry officers get a real-time national KPI dashboard — something that simply doesn't exist today.*
> *— A paperless audit trail from weighbridge to bank, verifiable instantly.*
>
> *This isn't just a better app. This is a new layer of trust between the Indian farmer and the Indian state."*

---

## 📚 SLIDE 12 — References

### 👑 [YOU] *(Briefly, as a transition)*

> *"Our solution is grounded in verified government data.*
>
> *We referenced the official SIH 2026 problem statement from sih.gov.in, APMC and MSP policy from the Food Corporation of India, CACP Minimum Support Prices for 2024 to 2026, and tech stack references for FastAPI, Next.js, Supabase, and WebSocket standards.*
>
> *The live app and the full open-source code are available right now — the links are on screen.*
>
> *Everything we've shown you today — every screen, every number — is live."*

---

## 🎤 SLIDE 13 — Thank You

### 👑 [YOU] *(Pause. Look at the judges. Speak from the heart.)*

> *"India has 140 million farming families. Each one of them faces the Mandi every harvest season. Each one of them deserves to know — in advance — when to go, how long to wait, and when their payment will arrive.*
>
> *KisanSetu AI gives them that certainty.*
>
> *Smart Procurement. Smart Queues. Empowered Farmers.*
>
> *We are Team KisanSetu AI. Team ID SIH2026-APP-7729. Problem Statement 26032.*
>
> *Thank you."*

### 💜 [PRACHI + ALL MEMBERS] *(Stand together)*

> *"Thank you."*

---

## 🙋 Q&A — Likely Judge Questions

> Be ready for these — assign who answers before the presentation.

### 👑 [YOU] handles:

**Q: How is this different from existing e-Mandi solutions?**
> "Existing e-Mandi portals handle crop registration — not queue management. We handle the last mile: the actual day of procurement, the actual queue, the actual token, the actual receipt. No existing system does all of this in a single live platform."

**Q: How do you handle farmers without smartphones?**
> "Our multi-channel SMS system sends token numbers and queue updates to any 2G feature phone via MSG91 DLT. The farmer doesn't need a smartphone — just a mobile number."

**Q: Is this actually deployed, or just a demo?**
> "This is live in production. Visit kisansetu-sih.vercel.app right now. Log in with a demo farmer account and you'll see real data, real queue tokens, real receipts."

---

### 💜 [PRACHI] handles:

**Q: What AI model did you use?**
> "We didn't use an external AI model. We built a custom three-layer scoring algorithm — wait time prediction, congestion scoring, and slot ranking — tuned specifically for the procurement context. It's lightweight, interpretable, and runs entirely on our backend."

**Q: How do you plan to onboard Mandis at scale?**
> "Each Mandi only needs an officer login and a stable internet connection. Our one-click setup script handles the rest. For offline Mandis, our dual-layer store ensures the system continues to function."

---

### 🔵 [VEDANT] / 🟢 [MITANSH] handle:

**Q: What is the infrastructure cost?**
> "Zero for initial deployment. Vercel free tier handles the frontend. Supabase free tier handles the database. GitHub Actions handles CI/CD. The total infrastructure cost for a pilot across 10 Mandis is Rs. 0."

**Q: How many tests does your backend have, and are they all passing?**
> "We have 13 tests covering our core API routes, recommendation engine, and queue state machine. All 13 are passing as of today."

---

### 🟠 [RUDRADEV] handles:

**Q: Can you explain the algorithm in simple terms?**
> "Imagine you're choosing a lane at a toll booth. We check how many cars are ahead of you, how fast the toll booth is processing, and how congested that lane has been today. We do the same thing for each Mandi slot, and we tell the farmer which lane — which slot — will get them through fastest."

---

*Script prepared for KisanSetu AI · Smart India Hackathon 2026 · Team ID: SIH2026-APP-7729*