# Generate Psychiatric Patient Certificate

Design and generate a funny certificate for a psychiatric patient in the Dr. Sigmund 2000 game using the nano-banana image generation tool.

## Input

$ARGUMENTS

If no arguments provided, ask the user for: patient name and which persona should sign the certificate.

## Available Personas

Read `config/personas.json` to get the current persona definitions. The known personas are:

1. **Dr. Sigmund 2000** — 90s retro AI therapist, Freudian clichés, Y2K computer jargon, Windows 95 references
2. **Dr. Luna Cosmos** — New-age mystic, astrology, crystals, chakras, cosmic metaphors
3. **Dr. Rex Hardcastle** — Gruff tough-love therapist, sports/military metaphors, no-nonsense
4. **Dr. Pixel** — Gamer therapist, video game terminology, boss battles, leveling up, XP
5. **Dr. Ada Sterling** — Modern clinical CBT therapist, evidence-based, professional, methodical
6. **Captain Whiskers, PhD** — Sophisticated cat therapist, cat puns, naps, warm blankets

## Instructions

### Step 1: Parse Input

Extract from the arguments:
- **Patient name** (required)
- **Persona** (optional — default to Dr. Sigmund 2000)
- **Diagnosis or achievement** (optional — invent a funny one if not provided)
- **Output filename** (optional)

If the patient name is missing, ask the user.

### Step 2: Read Persona Details

Read `config/personas.json` and find the selected persona's full definition including:
- Name, tagline, era, description
- Personality traits and speaking style
- Theme colors

Use these details to craft the certificate content and visual style.

### Step 3: Design the Certificate

Create a detailed image generation prompt for nano-banana. The certificate should be:

**Visual style:**
- Looks like an official-but-absurd framed certificate or diploma
- Matches the persona's era and theme (e.g., 90s clip-art style for Dr. Sigmund, cosmic/galaxy background for Dr. Luna, military-style for Dr. Rex, pixel-art for Dr. Pixel, clean modern for Dr. Ada, paw prints and whiskers for Captain Whiskers)
- Has ornate borders, seals, ribbons, or stamps appropriate to the persona
- Text is legible and centered

**Content to include in the prompt:**
- Title: A funny certificate name in the persona's voice (e.g., "Certificate of Emotional Defragmentation" for Dr. Sigmund, "Cosmic Soul Alignment Diploma" for Dr. Luna, "Mental Toughness Medal of Honor" for Dr. Rex, "Achievement Unlocked: Mental Health+1" for Dr. Pixel, "Cognitive Restructuring Completion Certificate" for Dr. Ada, "Purrfessional Wellness Award" for Captain Whiskers)
- Patient name prominently displayed
- A humorous diagnosis or achievement in the persona's style
- The signing persona's name and title
- A funny date or serial number (e.g., "Issued: Y2K-Safe Date 01/01/2000" for Dr. Sigmund)
- A fake official seal or stamp matching the persona theme

### Step 4: Generate the Certificate Image

Run the nano-banana tool to generate the certificate:

```bash
npx tsx tools/nano-banana.ts -p "<the crafted prompt>" -o "<filename>.png" -f "public/images/certificates"
```

Use a descriptive filename like `certificate-<patient-name>-<persona>.png` (lowercase, hyphens, no spaces).

The prompt should be detailed and specific about the visual layout, style, and all text content. Include instructions like "certificate layout", "ornate border", "official seal", and the specific text to render.

### Step 5: Present the Result

Tell the user:
- The certificate has been generated
- The file path where it was saved
- A text version of the certificate content in the persona's voice, as if they were presenting it to the patient

Write the presentation in character. For example, Dr. Sigmund would say something like: "Congratulations, patient! Your neural pathways have been successfully defragmented. This certificate proves your psyche is now Y2K-compliant."

### Tips for Good Results

- Be very specific about text content in the prompt — Gemini handles text better with explicit instructions
- Mention "certificate", "diploma", or "award" early in the prompt
- Specify the visual era/theme clearly (e.g., "1990s clip-art style", "cosmic purple galaxy", "8-bit pixel art")
- Keep text on the certificate concise — fewer words render more legibly
- If the first generation isn't good, offer to regenerate with a refined prompt
