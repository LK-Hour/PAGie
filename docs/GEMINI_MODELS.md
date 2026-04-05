# 🤖 Available Gemini Models (2026)

Retrieved from Google AI API on 2026-04-05

---

## 📝 GENERATIVE MODELS (For Chat/Text Generation)

### **Best for PAGie:**

#### 1. **gemini-2.5-flash** ⭐ RECOMMENDED
- **Description:** Stable version of Gemini 2.5 Flash, our mid-size multimodal model that supports up to 1 million tokens
- **Released:** June 2025
- **Best for:** Fast responses, large context window, balanced performance
- **Methods:** generateContent, countTokens, createCachedContent, batchGenerateContent

#### 2. **gemini-2.5-pro**
- **Description:** Stable release (June 17th, 2025) of Gemini 2.5 Pro
- **Best for:** Most capable reasoning, complex queries
- **Methods:** generateContent, countTokens, createCachedContent, batchGenerateContent

#### 3. **gemini-2.0-flash** 
- **Description:** Fast and versatile multimodal model for scaling across diverse tasks
- **Released:** January 2025
- **Best for:** Speed and efficiency
- **Methods:** generateContent, countTokens, createCachedContent, batchGenerateContent

#### 4. **gemini-2.0-flash-lite**
- **Description:** Lighter version of Gemini 2.0 Flash
- **Best for:** Even faster responses, lower resource usage
- **Methods:** generateContent, countTokens, createCachedContent, batchGenerateContent

### **Preview/Experimental Models:**

- **gemini-3-pro-preview** - Latest experimental Pro model
- **gemini-3-flash-preview** - Latest experimental Flash model  
- **gemini-3.1-pro-preview** - Newest generation Pro
- **gemini-3.1-flash-lite-preview** - Newest generation Flash Lite

### **Specialized Models:**

- **gemini-2.5-flash-preview-tts** - Text-to-speech optimized
- **gemini-2.5-pro-preview-tts** - Pro version with TTS
- **gemini-2.5-computer-use-preview-10-2025** - Computer interaction
- **deep-research-pro-preview-12-2025** - Deep research tasks

### **Gemma Models (Open Source):**

- gemma-3-1b-it, gemma-3-4b-it, gemma-3-12b-it, gemma-3-27b-it
- gemma-4-26b-a4b-it, gemma-4-31b-it

---

## 🔢 EMBEDDING MODELS (For Text Embeddings)

#### 1. **gemini-embedding-001** ⭐ RECOMMENDED FOR PAGIE
- **Description:** Obtain a distributed representation of a text
- **Best for:** Stable, widely tested embeddings
- **Methods:** embedContent, countTextTokens, countTokens, asyncBatchEmbedContent

#### 2. **gemini-embedding-2-preview**
- **Description:** Multimodal embedding support (text + images)
- **Best for:** Advanced multimodal use cases
- **Methods:** embedContent, countTextTokens, countTokens, asyncBatchEmbedContent

---

## 🎨 OTHER MODELS

### Image Generation:
- **imagen-4.0-generate-001** - Imagen 4
- **imagen-4.0-ultra-generate-001** - Imagen 4 Ultra
- **imagen-4.0-fast-generate-001** - Imagen 4 Fast

### Video Generation:
- **veo-2.0-generate-001** - Veo 2
- **veo-3.0-generate-001** - Veo 3
- **veo-3.1-generate-preview** - Veo 3.1 (latest)

### Audio:
- **gemini-2.5-flash-native-audio-latest** - Native audio processing
- **lyria-3-clip-preview** - Music generation (30s clips)
- **lyria-3-pro-preview** - Music generation (Pro)

### Specialized:
- **aqa** - Attributed Question Answering
- **gemini-robotics-er-1.5-preview** - Robotics

---

## 💡 RECOMMENDATIONS FOR PAGIE

### Current Setup (.env):
```bash
GEMINI_MODEL=gemini-3.0-flash  # ❌ This model doesn't exist!
```

### ✅ Recommended Changes:

**Option 1: Best Performance (Recommended)**
```bash
GEMINI_MODEL=gemini-2.5-flash
```
- Fastest stable model
- 1M token context window
- Best balance of speed/quality
- Released June 2025

**Option 2: Maximum Quality**
```bash
GEMINI_MODEL=gemini-2.5-pro
```
- Most capable reasoning
- Better for complex queries
- Slower but more accurate

**Option 3: Ultra Fast**
```bash
GEMINI_MODEL=gemini-2.0-flash-lite
```
- Fastest responses
- Lower resource usage
- Good for simple queries

**Option 4: Latest Experimental**
```bash
GEMINI_MODEL=gemini-3-flash-preview
```
- Cutting edge features
- May have breaking changes
- Use with caution

### For Embeddings (If Using Google Embeddings):
```bash
EMBEDDING_MODEL=gemini-embedding-001
```

---

## 🚀 Quick Fix for PAGie

Your `.env` currently has:
```bash
GEMINI_MODEL=gemini-3.0-flash
```

**This model doesn't exist!** Change to:
```bash
GEMINI_MODEL=gemini-2.5-flash
```

This will give you the best performance with the latest stable model.

---

## 📊 Model Comparison

| Model | Speed | Quality | Context | Cost | Best For |
|-------|-------|---------|---------|------|----------|
| gemini-2.5-flash | ⚡⚡⚡ | ⭐⭐⭐⭐ | 1M tokens | $ | **General Use** |
| gemini-2.5-pro | ⚡⚡ | ⭐⭐⭐⭐⭐ | 1M tokens | $$ | Complex Reasoning |
| gemini-2.0-flash | ⚡⚡⚡ | ⭐⭐⭐ | 128K tokens | $ | Speed Priority |
| gemini-2.0-flash-lite | ⚡⚡⚡⚡ | ⭐⭐⭐ | 128K tokens | $ | Ultra Fast |
| gemini-3-flash-preview | ⚡⚡⚡ | ⭐⭐⭐⭐ | ? | $ | Experimental |

---

**Generated:** 2026-04-05  
**Total Models Found:** 50 (34 Generative, 2 Embedding, 14 Other)
