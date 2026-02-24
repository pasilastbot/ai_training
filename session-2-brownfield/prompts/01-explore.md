# Prompt 01: Explore Suroi Codebase

**When to use:** PART 2 — REHEARSAL step (after cloning Suroi)
**Goal:** Use AI to understand an unfamiliar 114k LOC codebase

---

## Step 1: Understand the monorepo structure

```
@codebase What is the overall structure of this project?

Identify:
1. What are the workspace packages?
2. Where are the entry points for client and server?
3. What are the main dependencies?
4. How does the build system work?
```

---

## Step 2: Find the game loop

```
@server/src/game.ts

Explain the game loop:
1. What function runs every tick?
2. How often does it tick?
3. What gets updated each tick?
4. How are entities managed (created, updated, destroyed)?
```

---

## Step 3: Map your chosen subsystem

Pick your subsystem and use ONE of these prompts:

### If you chose Game Loop & Entities:
```
@server/src/game.ts
@server/src/objects/

What entity types exist? How are they created and destroyed?
Show me the inheritance hierarchy of game objects.
```

### If you chose Weapons & Inventory:
```
@common/src/definitions/
@server/src/inventory/

How are weapons defined? What data does each weapon have?
How does the damage calculation work?
```

### If you chose Networking:
```
@server/src/server.ts
@client/src/game.ts

What protocol does client-server communication use?
What messages are sent from server to client and vice versa?
```

### If you chose Map Generation:
```
@server/src/map.ts
@common/src/definitions/obstacles.ts

How are maps generated? What's the algorithm?
How are obstacles placed? What types exist?
```

### If you chose Rendering:
```
@client/src/rendering/

What rendering engine is used? How is the scene graph structured?
How are game objects rendered? How does the camera work?
```

---

## What you should know after this step

- [ ] You can describe the monorepo structure (client/server/common)
- [ ] You know where the main entry points are
- [ ] You understand the basics of your chosen subsystem
- [ ] You've identified 2-3 key files for your subsystem
