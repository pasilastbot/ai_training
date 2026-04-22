# Lunch Selection Agent

An AI agent for finding lunch restaurants, extracting daily menus, and providing personalized recommendations based on user preferences and past selections.

## Features

- **Restaurant Discovery**: Search for lunch restaurants in any city using Google Search
- **Menu Extraction**: Fetch today's lunch menu from restaurant websites using Gemini's url_context
- **Preference Management**: Track liked/disliked cuisines, dietary restrictions, allergies
- **Selection History**: Record and rate past lunch choices
- **Smart Recommendations**: Get personalized suggestions that respect your preferences and offer variety

## Quick Start

### CLI Mode

```bash
# Interactive chat
python lunch_selection_agent.py --chat

# Single query
python lunch_selection_agent.py "Find me lunch in Helsinki"

# With default city
python lunch_selection_agent.py --city Tampere "What's good for lunch today?"
```

### API Mode

```bash
# Start FastAPI server
uvicorn api.main:app --reload --port 8002
```

API available at http://localhost:8002/docs

### UI Mode

```bash
# Start Flask UI
python ui/app.py
```

Open http://localhost:5002 in your browser.

## Structure

```
lunch-selection-agent/
├── lunch_selection_agent.py    # Main CLI agent
├── agent_env.py                # Environment loader
├── ui/
│   └── app.py                  # Flask web interface
├── api/
│   └── main.py                 # FastAPI REST API
├── tools/
│   ├── store_restaurant.py     # Save restaurant to DB
│   ├── retrieve_restaurants.py # Query restaurants
│   └── store_selection.py      # Record lunch choices
├── skills/
│   ├── restaurant-discovery.md # Finding restaurants
│   ├── menu-extraction.md      # Extracting menus
│   └── preference-learning.md  # Managing preferences
├── subagents/
│   ├── restaurant_search.py    # Uses google_search + google_maps
│   └── menu_extractor.py       # Uses url_context
├── memory/
│   ├── memory.py               # Memory access CLI
│   ├── *_schema.json           # Data schemas
│   └── data/                   # JSON storage
└── requirements.txt
```

## Usage Examples

### Find Restaurants

```
You: Find lunch places in Tampere
Agent: [Searches using Google] Found 8 restaurants in Tampere:
       1. Ravintola Näsinneula - Finnish, Nordic
       2. Plevna - Brewpub, European
       ...
```

### Get Menu

```
You: What's the menu at Ravintola Näsinneula today?
Agent: [Fetches website] Today's lunch menu:
       - Salmon soup (€14) - G, L
       - Reindeer steak (€18)
       - Vegetable risotto (€12) - V, G
```

### Set Preferences

```
You: I'm vegetarian and I don't like spicy food
Agent: Got it! I've noted your preferences:
       - Dietary restrictions: vegetarian
       - Spice tolerance: none
```

### Get Recommendation

```
You: What should I have for lunch?
Agent: Based on your preferences, I recommend:
       🎯 Vegetable risotto at Ravintola Näsinneula (€12)
       - Vegetarian ✓
       - You haven't had Italian this week
       - 4.5⭐ average rating at this restaurant
```

### Record Selection

```
You: I had the salmon soup at Kuu, it was excellent!
Agent: Noted! Recorded your selection:
       - Salmon soup at Ravintola Kuu
       - Rating: 5⭐ (inferred from "excellent")
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Gemini API key |
| `GOOGLE_AI_STUDIO_KEY` | Alt | Alternative Gemini key |

## Memory Data

Data is stored locally in `memory/data/`:

- `restaurants.json` - Discovered restaurants
- `preferences.json` - User food preferences  
- `selections.json` - Lunch history with ratings

## Recommendation Logic

The agent considers:
1. **Dietary restrictions** (HARD FILTER - never violates)
2. **Liked cuisines** (+20 score)
3. **Disliked cuisines** (-30 score)
4. **Price preference** (+10 if matches)
5. **Implicit preferences** (learned from ratings)
6. **Variety** (avoids recent selections)
