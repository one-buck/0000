

| App | Best For | User Base / Reach | Privacy & Security | Key Features | Limitations |
| --- | --- | --- | --- | --- | --- |
| **Signal** | Privacy & security | Growing, niche | **Excellent** (end-to-end encryption, minimal metadata) | Disappearing messages, group calls, stories | Smaller adoption, only works if both parties use Signal |
| **WhatsApp** | Global reach | **2B+ users** | Strong (Signal Protocol, but Meta collects metadata) | Voice/video calls, channels, business tools | Meta ownership raises privacy concerns |
| **Telegram** | Features & communities | Large, global | Mixed (cloud-based, optional encryption) | Channels, bots, 200k+ groups, 4GB file sharing | Encryption not default, privacy weaker than Signal |
| **iMessage** | Apple ecosystem | All iPhone users | Good (encrypted Apple-to-Apple) | Stickers, reactions, SharePlay, RCS support | Limited to Apple devices; degraded UX with Android |
| **Discord** | Community chat | Millions (gamers, groups) | Limited (not privacy-first) | Organized servers, voice channels, integrations | Not ideal for one-to-one messaging |
| **Messenger** | Facebook integration | Huge (Meta users) | Fair (Meta collects data) | Video calls, screen sharing, business bots | Requires Facebook account |
| **WeChat** | China & Asia dominance | 1B+ users | Government surveillance concerns | Payments, mini-apps, social features | Privacy concerns, limited outside Asia |
| **Viber** | International calling | Popular in Europe | End-to-end encryption | Free calls, stickers, communities | Smaller global adoption |
| **Microsoft Teams** | Work collaboration | Enterprise users | Enterprise-level security | Meetings, file sharing, integration with Office | Heavy for casual messaging |
| **Android Messages (Google Messages)** | SMS/RCS standard | Android users | RCS encryption (limited) | SMS fallback, RCS features | Fragmented adoption, weaker than WhatsApp |


---

do a functional low-fidelity messaging app black and white basic icons for the folowing requiremnts:

### Core Screens & Functional Elements

- **Login/Onboarding**
  - Phone number input field
  - SMS verification flow
  - Profile setup (name, optional photo)

- **Chat List Screen**
  - Scrollable list of conversations
  - Each item shows: contact/group name, last message snippet, timestamp, unread badge
  - Floating action button (FAB) to start a new chat

- **Chat Screen**
  - Header: contact/group name, back button, call/video icons
  - Scrollable message thread (supports text, emoji, media, voice notes)
  - Input bar: text field, emoji picker, attachment button, microphone button
  - Send button (active only when text is entered)

- **New Chat / Contact Selection**
  - Search bar for contacts
  - List of contacts with name and avatar
  - Option to create a new group

- **Group Chat Features**
  - Group info screen: name, description, participants list
  - Add/remove participants
  - Admin controls (mute, permissions)

- **Calls**
  - Voice and video call initiation from chat header
  - Call screen: mute, speaker, end call

- **Settings**
  - Profile (name, photo, status)
  - Privacy (last seen, read receipts, blocked contacts)
  - Notifications
  - Storage/data usage

---

### Functional Flows

- **Message Sending**
  - User types → presses send → message appears in thread with timestamp
- **Media Sharing**
  - Tap attachment → choose photo/video/document → preview → send
- **Voice Note**
  - Hold microphone → record → release to send
- **Notifications**
  - Incoming message → push notification with sender + snippet
- **Group Creation**
  - Select multiple contacts → assign group name → create

---

### Notes for Low‑Fidelity Design

- Focus on **boxes, placeholders, and labels** (e.g., “Chat List Item,” “Message Bubble,” “Input Bar”).
- No need for colors, typography, or icons beyond basic functional markers.
- Layout should emphasize **hierarchy of actions**: chat list → chat thread → input → send.


- 