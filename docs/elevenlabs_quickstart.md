# ElevenLabs Developer Quickstart

**Source**: ElevenLabs Official Documentation
**Date Saved**: December 1, 2025
**Purpose**: Reference for implementing ElevenLabs API features in Goblin Assistant

---

## Overview

The ElevenLabs API provides a simple interface to state-of-the-art audio models and features. This guide covers the Text to Speech API and other available products.

## Text to Speech API - Quickstart

### Step 1: Create an API Key

- Create API key at: <https://elevenlabs.io/app/settings/api-keys>
- Store as environment variable in `.env`:

```bash
ELEVENLABS_API_KEY=<your_api_key_here>
```

### Step 2: Install SDK

**Python:**
```bash

pip install elevenlabs
pip install python-dotenv
```

**TypeScript/Node.js:**

```bash
npm install @elevenlabs/elevenlabs-js
npm install dotenv
```

**Note**: May need to install [MPV](https://mpv.io/) and/or [ffmpeg](https://ffmpeg.org/) for audio playback.

### Step 3: Basic Implementation

**Python Example:**
```python

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.play import play
import os

load_dotenv()

elevenlabs = ElevenLabs(
  api_key=os.getenv("ELEVENLABS_API_KEY"),
)

audio = elevenlabs.text_to_speech.convert(
    text="The first move is what sets everything in motion.",
    voice_id="JBFqnCBsd6RMkjVDRZzb",  # George voice
    model_id="eleven_multilingual_v2",
    output_format="mp3_44100_128",
)

play(audio)
```

**TypeScript Example:**

```typescript
import { ElevenLabsClient, play } from '@elevenlabs/elevenlabs-js';
import { Readable } from 'stream';
import 'dotenv/config';

const elevenlabs = new ElevenLabsClient();
const audio = await elevenlabs.textToSpeech.convert('JBFqnCBsd6RMkjVDRZzb', {
  text: 'The first move is what sets everything in motion.',
  modelId: 'eleven_multilingual_v2',
  outputFormat: 'mp3_44100_128',
});

const reader = audio.getReader();
const stream = new Readable({
  async read() {
    const { done, value } = await reader.read();
    if (done) {
      this.push(null);
    } else {
      this.push(value);
    }
  },
});

await play(stream);
```

### Step 4: Run the Code

```bash

# Python
python example.py

# TypeScript
npx tsx example.mts
```

## Available ElevenLabs Products

### Core Features

1. **Speech to Text** - Convert spoken audio into text
2. **ElevenLabs Agents** - Deploy conversational voice agents
3. **Music** - Generate studio-quality music
4. **Voice Cloning** - Clone a voice from audio samples
5. **Voice Remixing** - Remix and modify existing voices
6. **Sound Effects** - Generate sound effects from text prompts
7. **Voice Changer** - Transform the voice of an audio file
8. **Voice Isolator** - Isolate background noise from audio
9. **Voice Design** - Generate voices from a single text prompt
10. **Dubbing** - Dub audio/video from one language to another
11. **Forced Alignment** - Generate time-aligned transcripts for audio

## Integration Notes for Goblin Assistant

### Current Implementation Status

✅ **Implemented in Goblin Assistant:**

- Text-to-speech adapter (`/backend/providers/elevenlabs_adapter.py`)
- API key stored in `.env` file
- Routing service integration complete
- Support for standard and streaming generation
- Voice: George (ID: `JBFqnCBsd6RMkjVDRZzb`)
- Model: `eleven_multilingual_v2`
- Format: MP3 44.1kHz 128kbps

### Implementation Details

**Our Adapter vs Official SDK:**

- We use `aiohttp` for async HTTP requests (FastAPI compatible)
- Official SDK uses synchronous `play()` function
- Our adapter returns raw audio bytes for flexibility
- Supports both `.generate()` and `.stream_generate()` methods

**Key Differences:**

```python
# Official SDK
audio = elevenlabs.text_to_speech.convert(
    text="...",
    voice_id="...",
    model_id="...",
    output_format="..."
)

# Our Adapter
result = await adapter.generate(
    messages=[{"role": "user", "content": "..."}],
    voice_id="...",
    model_id="...",
    output_format="..."
)
audio_bytes = result["audio"]
```

### Future Enhancement Opportunities

**Not Yet Implemented:**
1. **Speech to Text** - Could add transcription capabilities
2. **Voice Cloning** - Custom voice creation from user audio
3. **Sound Effects** - Generate UI sound effects or notifications
4. **Voice Changer** - Transform recorded audio
5. **Voice Isolator** - Clean up audio input for better processing
6. **ElevenLabs Agents** - Full conversational AI with voice

### API Endpoints

**Base URL**: `https://api.elevenlabs.io/v1`

**Key Endpoints Used:**
- `POST /text-to-speech/{voice_id}` - Generate audio
- `POST /text-to-speech/{voice_id}/stream` - Stream audio
- `GET /voices` - List available voices
- `GET /voices/{voice_id}` - Get voice details

### Voice Settings

**Available Parameters:**
- `stability`: 0.0-1.0 (default: 0.5)
- `similarity_boost`: 0.0-1.0 (default: 0.75)
- `style`: 0.0-1.0 (default: 0.0)
- `use_speaker_boost`: boolean (default: true)

### Output Formats

**Supported Formats:**
- `mp3_44100_128` - MP3 44.1kHz 128kbps (default, high quality)
- `mp3_44100_192` - MP3 44.1kHz 192kbps (higher quality)
- `pcm_16000` - PCM 16kHz (low latency)
- `pcm_22050` - PCM 22.05kHz
- `pcm_24000` - PCM 24kHz
- `pcm_44100` - PCM 44.1kHz (highest quality)
- `ulaw_8000` - μ-law 8kHz (telephony)

### Models

**Available Models:**
- `eleven_multilingual_v2` - Best quality, 29+ languages (default)
- `eleven_monolingual_v1` - English only, fast
- `eleven_turbo_v2` - Fastest, lower latency

## Authentication

**Header Format:**
```http

xi-api-key: <your_api_key>
Content-Type: application/json
```

**Current Implementation:**

```python
self.headers = {
    "xi-api-key": self.api_key,
    "Content-Type": "application/json"
}
```

## Testing Status

**Test Results** (from `test_elevenlabs.py`):
- ✅ Speech Generation: WORKING (1578ms, 46KB audio)
- ✅ Streaming: WORKING (1127ms, 54 chunks, 43KB)
- ✅ Capabilities: All features available
- ⚠️ Voice Listing: Requires additional API permissions
- ⚠️ Voice Details: Requires additional API permissions

## Resources

- **API Documentation**: https://elevenlabs.io/docs/api-reference/introduction
- **API Keys Dashboard**: https://elevenlabs.io/app/settings/api-keys
- **Models Reference**: https://elevenlabs.io/docs/models
- **Voice Library**: https://elevenlabs.io/voice-library

## Related Files in Goblin Assistant

- `/backend/providers/elevenlabs_adapter.py` - Main adapter implementation
- `/backend/test_elevenlabs.py` - Test suite
- `/backend/.env` - API key storage (ELEVENLABS_API_KEY)
- `/backend/services/routing.py` - Routing service integration
- `/backend/providers/__init__.py` - Provider exports

---

**Implementation Date**: December 1, 2025
**Status**: ✅ Production Ready
**Provider Count**: 10 total (ElevenLabs is the newest addition)
