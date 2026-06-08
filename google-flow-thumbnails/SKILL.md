---
name: google-flow-thumbnails
description: Generate professional thumbnails, product images, and short videos using Google Flow (labs.google/fx/tools/flow) via Playwright browser automation. Supports Nano Banana Pro, Nano Banana 2, Imagen 4 for images and Veo 3.1 for video. Use when the user wants to create thumbnails, product shots, social media graphics, or video clips through Google Flow.
allowed-tools: Read, Grep, Glob, Bash(ls *), Bash(mv *), Bash(cp *), Bash(mkdir *), mcp__plugin_playwright_playwright__*
---

# Google Flow Thumbnail Generation

Generate professional images and videos using Google Flow's AI models via Playwright browser automation.

## Account & Authentication

- **URL:** https://labs.google/fx/tools/flow
- **Account:** biznomad101@gmail.com
- **Subscription:** Google AI Ultra (25,000 monthly credits)
- **Password:** Knumoney2020!
- **2FA:** Google prompt to Galaxy S24 Ultra (user must tap "Yes")

### Sign-In Flow (when not already signed in)

1. Navigate to `https://labs.google/fx/tools/flow`
2. Click "Create with Flow" button
3. Google account chooser appears — select **biznomad101@gmail.com**
4. If account not listed, click "Use another account", enter email, then password
5. **Passkey bypass:** Google may prompt for passkey first. If so:
   - Before page load, inject `addInitScript` to override `navigator.credentials.get` to reject with `NotAllowedError`
   - Reload the page — this surfaces the presend screen
   - Click "Try another way" → select "Enter your password"
   - Enter password: `Knumoney2020!`
6. **2FA:** Google sends a prompt to user's phone. Wait ~15 seconds for user to tap "Yes"
7. Verify sign-in: look for "ULTRA" badge in top-right corner

### Passkey Bypass Code (inject before navigating to Google sign-in)

```javascript
await page.addInitScript(() => {
  navigator.credentials.get = function(options) {
    return Promise.reject(new DOMException('The operation either timed out or was not allowed.', 'NotAllowedError'));
  };
});
```

## Available Models

### Image Models
| Model | Best For | Credits per Image |
|-------|----------|-------------------|
| **Nano Banana Pro** | Highest quality, photorealistic product shots | Varies |
| **Nano Banana 2** | Fast iteration, stylization, multi-reference editing | 0 (free w/ Ultra) |
| **Imagen 4** | Alternative style, Google's latest image model | Varies |

### Video Models
| Model | Best For | Credits per Video |
|-------|----------|-------------------|
| **Veo 3.1 - Fast** | Quick video generation with audio | 20 |
| **Veo 3.1 - Fast [Lower Priority]** | Lower queue priority, same quality | 20 |
| **Veo 3.1 - Quality** | Best video quality, longer processing | Varies |

## Image Generation Workflow

### Step 1: Create or Open a Project

```
Navigate to: https://labs.google/fx/tools/flow
Click: "+ New project" button (ref pattern: button "add_2 New project")
  OR
Click: an existing project link
```

### Step 2: Configure Settings

Click the model selector button (shows current model like "Nano Banana 2 crop_16_9 x4"):

1. **Mode:** Select "Image" tab (not "Video")
2. **Orientation:**
   - `Landscape` (16:9) — **DEFAULT for thumbnails and ad creatives**
   - `Portrait` (9:16) — for Instagram Stories, TikTok, Pinterest pins
3. **Quantity:** Always set to **x4** (generate 4 variations per prompt to pick the best)
4. **Model:** Use **Nano Banana 2** as the default for all thumbnails and static ad creatives. Only switch to Nano Banana Pro or Imagen 4 if specifically requested.

### Step 3: Enter Prompt & Generate

1. Click the prompt input: textbox with placeholder "What do you want to create?"
2. Type your prompt
3. Click the arrow button (arrow_forward Create) OR press Enter
4. Wait for generation (watch the status area for progress)
5. Generated images appear in the project canvas

### Step 4: Download Generated Images

1. Click on a generated image in the canvas to select it
2. Look for download/save options in the toolbar or right-click context menu
3. Images can also be dragged from the canvas

## Video Generation Workflow

### Additional Video Settings
- **Mode tabs:** "Frames" (start/end frame control) or "Ingredients" (reference images)
- **Start/End frames:** Click "Start" or "End" to set keyframes for video direction
- **Swap button:** swap_horiz to swap start and end frames

### Steps
1. Switch to "Video" tab in model selector
2. Select video model (Veo 3.1 recommended)
3. Optionally set Start/End frames for camera control
4. Enter prompt describing the scene/action
5. Click Create — each video costs ~20 credits

## Project Management

- **Rename project:** Click the project name textbox at top-left, type new name
- **Search within project:** Click search icon in toolbar, type search terms
- **Add external media:** Click "add Add Media" to upload reference images
- **Scenebuilder:** Click "play_movies Scenebuilder" for multi-scene video composition
- **Sort & Filter:** Click "filter_list Sort & Filter" to organize assets
- **Delete project:** From home screen, click "delete Delete project" on any project card

## Thumbnail Prompt Engineering

### For YouTube Thumbnails (Landscape 16:9)
```
Professional YouTube thumbnail for [TOPIC], bold vibrant colors,
high contrast, clean composition with rule of thirds, cinematic
lighting, photorealistic product placement, attention-grabbing,
no text overlay needed
```

### For Product Shots
```
Professional product photography of [PRODUCT], studio lighting,
clean white/gradient background, hero shot angle, commercial
quality, soft shadows, lifestyle context, magazine-worthy
```

### For Social Media Graphics (Portrait 9:16)
```
Eye-catching Instagram story graphic featuring [SUBJECT],
vertical composition, bold colors, modern aesthetic, lifestyle
photography style, aspirational mood, premium feel
```

### For Ad Creatives (Landscape 16:9)
```
Digital advertisement creative for [PRODUCT/BRAND], clean modern
design, product center-frame, complementary color palette,
professional commercial photography, aspirational lifestyle
```

## UI Element Reference (Playwright Selectors)

These are the key interactive elements by role/name:

| Element | Selector Pattern |
|---------|-----------------|
| Create with Flow (landing) | `button "Create with Flow"` |
| New Project | `button "add_2 New project"` |
| Prompt Input | `textbox` with placeholder "What do you want to create?" |
| Model Selector | Button showing current model (e.g., "Nano Banana 2 crop_16_9 x2") |
| Create/Submit | `button "arrow_forward Create"` |
| Go Back | `button "arrow_back Go Back"` |
| Add Media | `button "add Add Media"` |
| Scenebuilder | `button "play_movies Scenebuilder"` |
| Image tab | `tab "image Image"` |
| Video tab | `tab "videocam Video"` |
| Landscape | `tab "crop_16_9 Landscape"` |
| Portrait | `tab "crop_9_16 Portrait"` |
| Quantity x1-x4 | `tab "x1"` through `tab "x4"` |
| Project Name | `textbox "Editable text"` |
| Profile/Account | `button "ULTRA User profile image"` |

## Troubleshooting

- **Passkey dialog blocks sign-in:** Use the `addInitScript` override shown above to bypass WebAuthn
- **Wrong Google account:** Check for account chooser; select biznomad101@gmail.com specifically
- **"Loading..." stuck:** Wait up to 10 seconds, then reload the page
- **Credits exhausted:** Check credit balance via profile button (ULTRA badge). Ultra plan gives 25,000 monthly credits
- **Generation fails:** Try a different model or simplify the prompt. Some prompts may be blocked by safety filters
- **Multiple browser tabs:** Flow may open in a new tab. Use `browser_tabs` to manage tabs

## Default Settings (ALWAYS USE THESE)

- **Model:** Nano Banana 2
- **Quantity:** x4 (always generate 4 variations)
- **Mode:** Image
- **Orientation:** Landscape (16:9) for thumbnails and ad creatives; Portrait (9:16) only if explicitly requested

## Example: Generate a Vicelle Product Thumbnail

```
1. Navigate to https://labs.google/fx/tools/flow
2. Click "+ New project"
3. Click model selector → ensure "Image" mode, "Landscape", "x4", "Nano Banana 2"
4. Type prompt: "Professional product photography of a jar of sea moss gel
   with tropical fruits, studio lighting, clean marble surface, hero shot
   angle, commercial quality, soft shadows, premium health supplement branding"
5. Click Create (arrow button)
6. Wait for generation (~10-30 seconds)
7. 4 variations appear — select the best ones and download
```
