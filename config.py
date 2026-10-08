# -*- coding: utf-8 -*-
"""
Configuration module for Global AI Model Tracker Bot.
Supports Streamlit Community Cloud (st.secrets) and local (.env).
"""

import os
from dotenv import load_dotenv

# Try loading local .env if present
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)

def get_secret(key, default=""):
    """Fetch configuration from Streamlit secrets, environment variable, or fallback default."""
    # 1. Try Streamlit Secrets (if running in Streamlit)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    
    # 2. Try OS environment
    val = os.getenv(key)
    if val:
        return str(val).strip()
        
    return default

# Bot & Channel credentials
BOT_TOKEN = get_secret("BOT_TOKEN", "")
CHANNEL_CHAT_ID = get_secret("CHANNEL_CHAT_ID", "-1004454876267")
CHANNEL_USERNAME = get_secret("CHANNEL_USERNAME", "https://t.me/modeltracker")
CHECK_INTERVAL_SECONDS = int(get_secret("CHECK_INTERVAL_SECONDS", "300"))
# Maximum lookback threshold in hours (Models older than this will NOT be posted)
MAX_AGE_HOURS = int(get_secret("MAX_AGE_HOURS", "48"))

# Database path (Stored in local directory or /tmp if running read-only)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "model_tracker.db")

# 1. RSS and Atom Feeds of Global AI Labs & Major Tech Media
AI_RSS_FEEDS = [
    {
        "name": "Google DeepMind",
        "company": "Google DeepMind",
        "region": "🇺🇸 USA / 🇬🇧 UK",
        "category": "Frontier AI & Science",
        "url": "https://deepmind.google/blog/rss.xml"
    },
    {
        "name": "Google AI & Tech Blog",
        "company": "Google",
        "region": "🇺🇸 USA",
        "category": "Multimodal & Gemini Updates",
        "url": "https://blog.google/technology/ai/rss/"
    },
    {
        "name": "Google Developers AI",
        "company": "Google Developers",
        "region": "🇺🇸 USA",
        "category": "Gemini API & Developer Releases",
        "url": "https://blog.google/technology/developers/rss/"
    },
    {
        "name": "OpenAI News & Announcements",
        "company": "OpenAI",
        "region": "🇺🇸 USA",
        "category": "Frontier Models & ChatGPT",
        "url": "https://openai.com/news/rss.xml"
    },
    {
        "name": "Meta AI Engineering & Research",
        "company": "Meta AI",
        "region": "🇺🇸 USA",
        "category": "Llama & Open Weights",
        "url": "https://engineering.fb.com/category/ai-research/feed/"
    },
    {
        "name": "Microsoft Official Blog",
        "company": "Microsoft AI",
        "region": "🇺🇸 USA",
        "category": "Phi Series & Copilot",
        "url": "https://blogs.microsoft.com/feed/"
    },
    {
        "name": "Hugging Face Blog",
        "company": "Hugging Face",
        "region": "🇺🇸 USA / 🇪🇺 France",
        "category": "Community & Model Breakthroughs",
        "url": "https://huggingface.co/blog/feed.xml"
    },
    {
        "name": "AWS Machine Learning Blog",
        "company": "Amazon AWS",
        "region": "🇺🇸 USA",
        "category": "Amazon Nova & Titan",
        "url": "https://aws.amazon.com/blogs/machine-learning/feed/"
    },
    {
        "name": "Cohere Blog",
        "company": "Cohere",
        "region": "🇨🇦 Canada / 🇺🇸 USA",
        "category": "Enterprise RAG & Embeddings",
        "url": "https://cohere.com/blog/rss.xml"
    },
    {
        "name": "Stability AI News",
        "company": "Stability AI",
        "region": "🇬🇧 UK / 🇺🇸 USA",
        "category": "Stable Diffusion & Generative Media",
        "url": "https://stability.ai/news?format=rss"
    },
    {
        "name": "NVIDIA AI Blogs",
        "company": "NVIDIA",
        "region": "🇺🇸 USA",
        "category": "GPU Acceleration & Foundation Models",
        "url": "https://blogs.nvidia.com/feed/"
    },
    {
        "name": "TechCrunch Artificial Intelligence",
        "company": "Global Tech Media",
        "region": "🌐 Global",
        "category": "AI Launch News & Startups",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/"
    },
    {
        "name": "VentureBeat AI News",
        "company": "VentureBeat",
        "region": "🌐 Global",
        "category": "Enterprise AI & Model Launches",
        "url": "https://venturebeat.com/category/ai/feed/"
    },
    {
        "name": "The Decoder AI News",
        "company": "The Decoder",
        "region": "🌐 Global",
        "category": "Frontier AI Releases & Breaking Models",
        "url": "https://the-decoder.com/feed/"
    },
    {
        "name": "AWS News & Bedrock Releases",
        "company": "Amazon AWS",
        "region": "🇺🇸 USA",
        "category": "Bedrock Claude & Model Launches",
        "url": "https://aws.amazon.com/blogs/aws/feed/"
    }
]

# 2. GitHub Releases Atom Feeds for Fast Model Launch Alerts
GITHUB_RELEASE_FEEDS = [
    {
        "name": "DeepSeek R1 Releases",
        "company": "DeepSeek (China)",
        "region": "🇨🇳 China",
        "category": "Open-Weights Reasoning Models",
        "url": "https://github.com/deepseek-ai/DeepSeek-R1/releases.atom"
    },
    {
        "name": "DeepSeek V3 Releases",
        "company": "DeepSeek (China)",
        "region": "🇨🇳 China",
        "category": "MoE Frontier Models",
        "url": "https://github.com/deepseek-ai/DeepSeek-V3/releases.atom"
    },
    {
        "name": "Tencent Hunyuan-Video",
        "company": "Tencent (China)",
        "region": "🇨🇳 China",
        "category": "Open-Weights Video Generation",
        "url": "https://github.com/Tencent/HunyuanVideo/releases.atom"
    },
    {
        "name": "Zhipu AI GLM-4 / CogVideoX",
        "company": "Zhipu AI (China)",
        "region": "🇨🇳 China",
        "category": "Video & Multimodal Models",
        "url": "https://github.com/THUDM/CogVideo/releases.atom"
    },
    {
        "name": "Ollama Model Runner Releases",
        "company": "Ollama",
        "region": "🇺🇸 USA",
        "category": "Local Model Execution",
        "url": "https://github.com/ollama/ollama/releases.atom"
    },
    {
        "name": "vLLM Inference Engine Releases",
        "company": "vLLM Project",
        "region": "🇺🇸 USA",
        "category": "High-Throughput Model Serving",
        "url": "https://github.com/vllm-project/vllm/releases.atom"
    }
]

# 3. Top AI Organizations to Monitor on Hugging Face API for New Model Releases
HF_TRACKED_ORGS = [
    {"org": "deepseek-ai", "company": "DeepSeek", "country": "🇨🇳 China"},
    {"org": "Qwen", "company": "Alibaba Cloud / Qwen", "country": "🇨🇳 China"},
    {"org": "meta-llama", "company": "Meta AI", "country": "🇺🇸 USA"},
    {"org": "mistralai", "company": "Mistral AI", "country": "🇪🇺 France"},
    {"org": "google", "company": "Google DeepMind / Gemma", "country": "🇺🇸 USA"},
    {"org": "microsoft", "company": "Microsoft AI / Phi", "country": "🇺🇸 USA"},
    {"org": "sarvamai", "company": "Sarvam AI", "country": "🇮🇳 India"},
    {"org": "krutrim-ai-labs", "company": "Krutrim", "country": "🇮🇳 India"},
    {"org": "ai4bharat", "company": "AI4Bharat", "country": "🇮🇳 India"},
    {"org": "black-forest-labs", "company": "Black Forest Labs (FLUX)", "country": "🇩🇪 Germany"},
    {"org": "stabilityai", "company": "Stability AI", "country": "🇬🇧 UK / 🇺🇸 USA"},
    {"org": "BAAI", "company": "BAAI (Beijing Academy of AI)", "country": "🇨🇳 China"},
    {"org": "CohereLabs", "company": "Cohere", "country": "🇨🇦 Canada"},
    {"org": "nvidia", "company": "NVIDIA", "country": "🇺🇸 USA"},
    {"org": "apple", "company": "Apple", "country": "🇺🇸 USA"},
    {"org": "tiiuae", "company": "TII Falcon", "country": "🇦🇪 UAE"}
]
