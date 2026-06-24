# Messenger UI

A client-side messaging wireframe built with vanilla HTML, CSS, and JavaScript. No build step, no framework, no dependencies beyond a Lucide icon CDN script.

---

## Quick Start

You must serve the files over HTTP — `file://` will block the partial fetches.

```bash
cd ui/
python -m http.server
# then open http://localhost:8000
```

Any static file server works (VS Code Live Server, `npx serve`, etc.).

---

## File Structure

```
ui/
├── index.html          Shell page — just mount points, no real content
├── loader.js           Fetches all partials then boots app.js
├── app.js              All application logic and state
├── styles.css          All styles (variables, components, layout)
├── data.json           Seed data — contacts and conversations
└── partials/           One file per UI section (edit these)
    ├── toast.html              Notification toast (bottom-right)
    ├── overlays.html           Login → Verify → Profile Setup → Call screen
    ├── sidebar.html            Left column: avatar, search, chat list
    ├── view-empty.html         Default panel (no chat open)
    ├── view-chat.html          Active chat: header, messages, input bar
    ├── view-new-chat.html      Contact picker for starting a new chat
    ├── view-group.html         Group creation — step 1 (members) + step 2 (name)
    ├── view-info.html          Contact / group info panel
    ├── view-settings.html      Settings: privacy, notifications, storage, account
    ├── view-profile-edit.html  Edit name and status
    └── view-blocked.html       Blocked contacts list
```

---

## How It Works

### Boot sequence

```
index.html  →  loader.js  →  fetches all partials in parallel
                           →  injects HTML into mount points
                           →  appends app.js as a <script> tag
                           →  app.js calls loadData()  →  init()
```

### View navigation

All panel views (`view-*`) live in the DOM simultaneously. Only one is visible at a time, controlled by CSS class `active`:

```js
showView('view-chat')      // makes view-chat active, hides all others
showOverlay('overlay-call') // shows a full-screen overlay
```

### State

Everything lives in the single `state` object at the top of `app.js`:

| Key | Type | Description |
|-----|------|-------------|
| `contacts` | `Contact[]` | Loaded from `data.json` |
| `conversations` | `Conversation[]` | Loaded from `data.json` |
| `currentChatId` | `number \| null` | ID of the open conversation |
| `selectedGroupContacts` | `number[]` | Contact IDs selected during group creation |
| `userName` | `string` | The logged-in user's display name |
| `userStatus` | `string` | The logged-in user's status text |
| `callTimer` | timer ref | Active call timer interval |
| `recTimer` | timer ref | Active voice recording timer interval |
| `toastTimer` | timer ref | Toast auto-dismiss timeout |

---

## Data Shape

Edit `data.json` to change contacts and seed conversations.

### Contact

```json
{
  "id": 1,
  "name": "Alice Morgan",
  "initial": "A",
  "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Alice&backgroundColor=b6e3f4",
  "status": "online",
  "statusText": "At the office"
}
```

`status` accepts: `"online"` | `"away"` | `"offline"`

### Conversation

```json
{
  "id": 1,
  "type": "individual",
  "contactId": 1,
  "unread": 3,
  "messages": [
    { "from": "them", "text": "Hey!", "time": "9:15 AM" },
    { "from": "me",   "type": "voice", "duration": "0:12", "time": "9:25 AM" },
    { "from": "them", "type": "media", "mediaType": "Photo", "time": "9:26 AM" }
  ]
}
```

For group conversations, replace `"type": "individual"` + `contactId` with:

```json
{
  "type": "group",
  "name": "Project Team",
  "participants": [1, 2, 3]
}
```

Message `from` field:
- `"me"` — sent message (right-aligned, black bubble)
- `"them"` — received in 1-on-1 chat (left-aligned, white bubble)
- `"Alice Morgan"` — full contact name for group messages (shows sender label)

---

## Who Owns What

| File | Who edits it |
|------|--------------|
| `partials/overlays.html` | Auth / onboarding team |
| `partials/sidebar.html` | Navigation / layout team |
| `partials/view-chat.html` | Messaging team |
| `partials/view-new-chat.html` | Contacts team |
| `partials/view-group.html` | Groups team |
| `partials/view-info.html` | Contacts / groups team |
| `partials/view-settings.html` | Settings team |
| `partials/view-profile-edit.html` | Profile team |
| `partials/view-blocked.html` | Safety / moderation team |
| `styles.css` | Design system team |
| `app.js` | Core logic team |
| `data.json` | Backend / API team (replace with real API calls) |

---

## Key Functions in app.js

| Function | What it does |
|----------|-------------|
| `loadData()` | Fetches `data.json`, populates state, calls `init()` |
| `init()` | Binds all events, initialises emoji picker, runs `lucide.createIcons()` |
| `showView(id)` | Switches the active panel view |
| `showOverlay(id)` | Shows a full-screen overlay (login, call, etc.) |
| `renderChatList(filter)` | Re-renders the sidebar chat list |
| `openChat(convId)` | Opens a conversation and renders it |
| `renderChat()` | Re-renders the message list for the current chat |
| `sendMessage()` | Appends a message to state and re-renders |
| `simulateReply(conv)` | Fires a fake reply after a delay (dev only) |
| `openInfo()` | Builds and shows the contact/group info panel |
| `startCall(type)` | Shows the call overlay (`'voice'` or `'video'`) |
| `showToast(contact, msg)` | Shows the notification toast |
| `createGroup()` | Creates a new group conversation from the selected contacts |

---

## Styling

`styles.css` uses CSS custom properties defined in `:root`. Change the design tokens here — do not hardcode colour or spacing values elsewhere.

```css
--black        /* primary text and actions  */
--white        /* backgrounds               */
--gray-50 … --gray-800   /* neutral scale  */
--status-online / away / offline
--radius-sm … --radius-pill
--shadow-xs … --shadow-lg
--transition / --transition-md
```

Icons are [Lucide](https://lucide.dev) loaded from CDN (`unpkg.com/lucide`). Use `<i data-lucide="icon-name"></i>` in any partial, then call `lucide.createIcons()` after injecting HTML. This is already called in `init()` and `showView()`.

---

## Adding a New View

1. Create `partials/view-myfeature.html` — follow the same pattern as existing views (panel-header + content area).
2. Add a mount point in `index.html`:
   ```html
   <div id="partial-view-myfeature"></div>
   ```
3. Register it in `loader.js`:
   ```js
   { id: 'partial-view-myfeature', file: 'partials/view-myfeature.html' },
   ```
4. Add navigation in `app.js`:
   ```js
   showView('view-myfeature');
   ```

---

## Replacing Seed Data with a Real API

All data access goes through `state.contacts` and `state.conversations`. To wire up a real backend, replace the `loadData()` function in `app.js`:

```js
async function loadData() {
  const [contacts, conversations] = await Promise.all([
    fetch('/api/contacts').then(r => r.json()),
    fetch('/api/conversations').then(r => r.json()),
  ]);
  state.contacts = contacts;
  state.conversations = conversations;
  init();
}
```

Everything else will continue to work as-is.
