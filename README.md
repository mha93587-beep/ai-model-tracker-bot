# 🚀 Global AI Model Tracker - Telegram RSS & Model Bot

एक शक्तिशाली और स्वचालित **Telegram AI Model Tracker Bot** और **Streamlit Web Dashboard**, जो दुनिया भर की सभी प्रमुख AI कंपनियों (OpenAI, Anthropic, Google DeepMind, Meta, DeepSeek, Qwen/Alibaba, Mistral, Sarvam AI, Krutrim, आदि) के नए मॉडल्स, वर्जन अपडेट्स, API ब्लॉग्स और रिलीज की निगरानी करके सीधे आपके टेलीग्राम चैनल [**@modeltracker**](https://t.me/modeltracker) पर पोस्ट करता है।

यह प्रोजेक्ट पूरी तरह से **Streamlit Community Cloud (Free Hosting)** के लिए अनुकूलित (optimized) है।

---

## 🌟 प्रमुख विशेषताएं (Key Features)

1. **मल्टी-सोर्स इंटेलिजेंस ट्रैकर:**
   - **आधिकारिक RSS / Atom ब्लॉग्स:** Google DeepMind, OpenAI, Anthropic, Meta AI Research, Microsoft AI, Mistral AI, Hugging Face, Amazon AWS AI, Cohere, Stability AI, NVIDIA, TechCrunch AI, VentureBeat।
   - **GitHub रिलीज मॉनिटर:** DeepSeek-R1, DeepSeek-V3, Tencent Hunyuan-Video, Zhipu GLM/CogVideoX, Ollama, vLLM।
   - **Hugging Face Hub API ट्रैकर:** `deepseek-ai`, `Qwen`, `meta-llama`, `mistralai`, `google`, `microsoft`, `sarvamai`, `Krutrim-AI-Labs`, `ai4bharat`, `black-forest-labs`, `stabilityai` आदि द्वारा नए मॉडल अपलोड होते ही तुरंत अलर्ट।

2. **Streamlit Cloud के लिए विशेष ऑप्टिमाइज़ेशन:**
   - `@st.cache_resource` सिंगलटन बैकग्राउंड वर्कर थ्रेड — पेज रीलोड होने पर भी बैकग्राउंड प्रोसेस डुप्लीकेट नहीं होता।
   - `st.secrets` और `.env` दोनों का सपोर्ट — सुरक्षा के लिए टोकन कोड में हार्डकोड नहीं रहता।
   - SQLite डेटाबेस (`model_tracker.db`) डुप्लीकेट पोस्टिंग को रोकता है।

3. **सुंदर वेब कंट्रोल पैनल (Dashboard):**
   - लाइव स्टेटस: 🟢 Worker Active / 🔴 Paused।
   - ⚡ **"Check & Broadcast Now"** बटन: एक क्लिक में तुरंत सभी सोर्सेज स्कैन करके नए मॉडल्स पोस्ट करें।
   - 🔔 **"Send Test Post"** बटन: बॉट और चैनल के कनेक्शन की तुरंत जांच करें।
   - 📜 लाइव ब्रॉडकास्ट लॉग्स और आंकड़े।
   - ➕ कस्टम मॉडल अलर्ट पोस्ट करने का फॉर्म।

---

## 📁 फ़ाइल संरचना (Directory Structure)

```
/storage/emulated/0/antigravity/RamuaRSS/
├── app.py                # Streamlit Web Dashboard & Background Worker
├── tracker.py            # RSS & Hugging Face मॉडल ट्रैकिंग इंजन
├── config.py             # सीक्रेट्स लोड करने व सोर्सेज की लिस्टिंग
├── database.py           # SQLite डुप्लीकेट-रोकथाम और लॉग्स डेटाबेस
├── requirements.txt      # Streamlit Cloud के लिए आवश्यक पैकेजेस
├── .env                  # लोकल एनवायरनमेंट फ़ाइल (सुरक्षित टोकन)
├── .streamlit/
│   ├── secrets.toml      # Streamlit Secrets टेम्पलेट
│   └── config.toml       # Streamlit UI थीम व सर्वर सेटिंग्स
└── README.md             # यह संपूर्ण मार्गदर्शिका
```

---

## ☁️ Streamlit Community Cloud पर 24/7 फ्री होस्ट करने का तरीका

### चरण 1: GitHub पर रिपॉजिटरी बनाएं
1. अपने GitHub अकाउंट ([github.com](https://github.com)) पर जाएं और **"New repository"** बनाएं (नाम: `ai-model-tracker`).
2. इस फ़ोल्डर की सभी मुख्य फ़ाइलें उसमें अपलोड या पुश करें:
   - `app.py`
   - `tracker.py`
   - `config.py`
   - `database.py`
   - `requirements.txt`
   - `.streamlit/config.toml`

*(ध्यान दें: `.env` या `.streamlit/secrets.toml` को गिटहब पर कमिट न करें।)*

### चरण 2: Streamlit Community Cloud पर ऐप बनाएं
1. [share.streamlit.io](https://share.streamlit.io/) पर लॉगिन करें।
2. **"Create app"** / **"New app"** पर क्लिक करें।
3. अपनी रिपॉजिटरी चुनें और Main file path में `app.py` डालें।

### चरण 3: Secrets सेट करें (Bot Token & Channel ID)
1. ऐप डिप्लॉय करने से पहले **"Advanced settings"** -> **"Secrets"** पर क्लिक करें (या डिप्लॉय के बाद **App Settings** -> **Secrets** में जाएं)।
2. नीचे दिए गए सीक्रेट्स कॉपी करके पेस्ट करें:
```toml
BOT_TOKEN = "your_telegram_bot_token_here"
CHANNEL_CHAT_ID = "-1004454876267"
CHANNEL_USERNAME = "https://t.me/modeltracker"
CHECK_INTERVAL_SECONDS = 300
```
3. **"Save"** और **"Deploy"** पर क्लिक करें! आपका ऐप 1-2 मिनट में लाइव हो जाएगा।

### चरण 4: 24/7 ऑलवेज-ऑन (Keep Alive) कैसे रखें?
Streamlit Cloud पर फ्री ऐप्स कुछ दिन तक बिना विज़िटर के रहने पर स्लीप (Sleep) मोड में चले जाते हैं। इसे 24 घंटे लगातार चालू रखने के लिए:
1. किसी भी मुफ़्त अपटाइम मॉनिटर (जैसे [UptimeRobot.com](https://uptimerobot.com) या [cron-job.org](https://cron-job.org)) पर फ्री अकाउंट बनाएं।
2. एक नया HTTP(s) मॉनिटर जोड़ें और उसमें अपने Streamlit App का URL (उदा. `https://your-app.streamlit.app`) डाल दें।
3. मॉनिटरिंग इंटरवल **10 से 15 मिनट** सेट कर दें।
4. अब UptimeRobot आपके ऐप को हर 10 मिनट में पिंग करेगा, जिससे Streamlit Cloud का कंटेनर कभी भी स्लीप मोड में नहीं जाएगा और बैकग्राउंड बॉट हर 5 मिनट में नए AI मॉडल्स को टेलीग्राम चैनल में भेजता रहेगा!

---

## 🧪 लोकल रन / टेस्टिंग (Local Testing)

यदि आप इसे सीधे अपने डिवाइस में चलाकर टेस्ट करना चाहते हैं:
```bash
cd /storage/emulated/0/antigravity/RamuaRSS/
streamlit run app.py
```
यह लोकल पोर्ट `8501` पर डैशबोर्ड खोल देगा।

---

**चैनल:** [https://t.me/modeltracker](https://t.me/modeltracker)  
**बॉट ID:** `-1004454876267`
