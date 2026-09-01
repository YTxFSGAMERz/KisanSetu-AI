-- ============================================================
-- KisanSetu AI — Supabase Seed Data (Real Indian APMC Mandis & Official MSP Rates)
-- ============================================================

-- 1. Real APMC Mandis
INSERT INTO procurement_centres (name, code, address, district, state, latitude, longitude, daily_capacity, processing_capacity, avg_processing_minutes, is_active, contact_phone)
VALUES
('Karnal Grain Mandi — Haryana State Agricultural Marketing Board', 'APMC-HR-KNL-001', 'Model Town, Sector 12, Karnal, Haryana 132001', 'Karnal', 'Haryana', 29.6857, 76.9905, 250, 10, 15.0, true, '0184-2256789'),
('Khanna Grain Market — Asia''s Largest Grain Mandi', 'APMC-PB-KHN-002', 'GT Road, Mandi Board Complex, Khanna, Punjab 141401', 'Ludhiana', 'Punjab', 30.7072, 76.2166, 500, 16, 12.0, true, '01628-220145'),
('Lasalgaon APMC Market Yard — Asia''s Largest Onion & Grain Hub', 'APMC-MH-LSG-003', 'Niphad Road, Lasalgaon, Nashik, Maharashtra 422306', 'Nashik', 'Maharashtra', 20.1472, 74.2267, 350, 12, 18.0, true, '02550-266023'),
('Unjha APMC Mandi Yard — National Spices & Oilseeds Centre', 'APMC-GJ-UNJ-004', 'Brahmanwada Road, Unjha, Mehsana, Gujarat 384170', 'Mehsana', 'Gujarat', 23.8037, 72.3922, 300, 10, 16.0, true, '02767-252033'),
('Indore APMC Market (Choithram Mandi)', 'APMC-MP-IND-005', 'Manik Bagh Road, Choithram Circle, Indore, Madhya Pradesh 452014', 'Indore', 'Madhya Pradesh', 22.6868, 75.8459, 400, 14, 14.0, true, '0731-2475890'),
('Sri Ganganagar Krishi Upaj Mandi Samiti', 'APMC-RJ-SGN-006', 'New Mandi Yard, Sri Ganganagar, Rajasthan 335001', 'Sri Ganganagar', 'Rajasthan', 29.9038, 73.8772, 280, 10, 15.0, true, '0154-2470123'),
('Hapur Krishi Utpadan Mandi Samiti', 'APMC-UP-HPR-007', 'Delhi Road, Hapur, Uttar Pradesh 245101', 'Hapur', 'Uttar Pradesh', 28.7306, 77.7759, 320, 11, 16.0, true, '0122-2304560'),
('Gulbarga APMC Yard (Kalaburagi Pulses Hub)', 'APMC-KA-KLB-008', 'Nehru Gunj, Kalaburagi, Karnataka 585104', 'Kalaburagi', 'Karnataka', 17.3297, 76.8343, 220, 8, 17.0, true, '08472-221089'),
('Nizamabad Agricultural Market Yard (e-NAM Model Mandi)', 'APMC-TG-NZB-009', 'Market Yard, Nizamabad, Telangana 503001', 'Nizamabad', 'Telangana', 18.6725, 78.0941, 260, 9, 15.0, true, '08462-234512'),
('Guntur APMC Chilli & Grain Market Yard', 'APMC-AP-GNT-010', 'Mirchi Yard, Chuttugunta, Guntur, Andhra Pradesh 522004', 'Guntur', 'Andhra Pradesh', 16.3067, 80.4365, 300, 12, 16.0, true, '0863-2224578'),
('Muzaffarpur Krishi Utpadan Bazaar Samiti', 'APMC-BR-MZP-011', 'Bazaar Samiti, Saraiya Road, Muzaffarpur, Bihar 842001', 'Muzaffarpur', 'Bihar', 26.1209, 85.3647, 200, 8, 18.0, true, '0621-2245678'),
('Rajkot APMC Bedeswar Market Yard', 'APMC-GJ-RJK-012', 'Marketing Yard, Rajkot-Ahmedabad Highway, Rajkot, Gujarat 360003', 'Rajkot', 'Gujarat', 22.3039, 70.8022, 380, 14, 14.0, true, '0281-2471201')
ON CONFLICT (code) DO NOTHING;

-- 2. Official 2024-2026 CACP MSP Crops
INSERT INTO crops (name, name_hi, name_gu, category, unit, msp_per_quintal, processing_complexity, is_active)
VALUES
('Wheat', 'गेहूँ', 'ઘઉં', 'cereal', 'quintal', 2275.0, 1.0, true),
('Paddy (Common)', 'धान (सामान्य)', 'ડાંગર (સામાન્ય)', 'cereal', 'quintal', 2300.0, 1.1, true),
('Paddy (Grade A)', 'धान (ग्रेड ए)', 'ડાંગર (ગ્રેડ એ)', 'cereal', 'quintal', 2320.0, 1.15, true),
('Mustard / Rapeseed', 'सरसों / तोरिया', 'રાયડો / સરસવ', 'oilseed', 'quintal', 5650.0, 1.2, true),
('Gram (Chickpea)', 'चना', 'ચણા', 'pulse', 'quintal', 5440.0, 1.1, true),
('Arhar / Tur (Pigeon Pea)', 'अरहर / तुअर', 'તુવેર', 'pulse', 'quintal', 7550.0, 1.25, true),
('Moong (Green Gram)', 'मूँग', 'મગ', 'pulse', 'quintal', 8682.0, 1.2, true),
('Urad (Black Matpe)', 'उड़द', 'અડદ', 'pulse', 'quintal', 7400.0, 1.2, true),
('Lentil (Masur)', 'मसूर', 'મસૂર', 'pulse', 'quintal', 6425.0, 1.1, true),
('Maize', 'मक्का', 'મકાઈ', 'cereal', 'quintal', 2225.0, 0.95, true),
('Bajra (Pearl Millet)', 'बाजरा', 'બાજરી', 'cereal', 'quintal', 2625.0, 1.0, true),
('Jowar (Hybrid)', 'ज्वार (हाइब्रिड)', 'જુવાર', 'cereal', 'quintal', 3371.0, 1.0, true),
('Soybean (Yellow)', 'सोयाबीन (पीला)', 'સોયાબીન', 'oilseed', 'quintal', 4892.0, 1.15, true),
('Groundnut (in shell)', 'मूँगफली', 'મગફળી', 'oilseed', 'quintal', 6783.0, 1.3, true),
('Cotton (Medium Staple)', 'कपास (मध्यम रेशा)', 'કપાસ', 'commercial', 'quintal', 7121.0, 1.35, true),
('Cotton (Long Staple)', 'कपास (लंबा रेशा)', 'કપાસ (લાંબો તાર)', 'commercial', 'quintal', 7521.0, 1.4, true),
('Sesamum (Til)', 'तिल', 'તલ', 'oilseed', 'quintal', 9267.0, 1.25, true),
('Sunflower Seed', 'सूरजमुखी बीज', 'સૂર્યમુખી બીજ', 'oilseed', 'quintal', 7280.0, 1.15, true)
ON CONFLICT (name) DO NOTHING;
