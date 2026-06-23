/* ════════════════════════════════════════════
   State
   ════════════════════════════════════════════ */
const state = {
  contacts: [],
  conversations: [],
  currentChatId: null,
  selectedGroupContacts: [],
  userName: 'You',
  userStatus: 'Available',
  callTimer: null,
  callSeconds: 0,
  callType: 'voice',
  recTimer: null,
  recSeconds: 0,
  toastTimer: null,
};

/* ════════════════════════════════════════════
   DOM References
   ════════════════════════════════════════════ */
const $ = (id) => document.getElementById(id);

/* ════════════════════════════════════════════
   Data Loading
   ════════════════════════════════════════════ */
async function loadData() {
  try {
    const res = await fetch('data.json');
    if (!res.ok) throw new Error(res.status);
    const data = await res.json();
    state.contacts = data.contacts;
    state.conversations = data.conversations;
    init();
  } catch (err) {
    const card = $('overlay-login').querySelector('.overlay-card');
    card.innerHTML = `
      <div class="error-state">
        <div style="font-weight:bold;font-size:14px;margin-bottom:12px;">Failed to load data</div>
        <p>Could not fetch <code>data.json</code>.</p>
        <p style="margin-top:8px;">Serve these files with a local server:</p>
        <p><code>python -m http.server</code></p>
        <p style="margin-top:8px;">or use VS Code Live Server extension.</p>
        <p style="margin-top:12px;color:#aaa;">Error: ${err.message}</p>
      </div>
    `;
  }
}

/* ════════════════════════════════════════════
   Initialization
   ════════════════════════════════════════════ */
function init() {
  bindEvents();
  initEmojiPicker();
}

/* ════════════════════════════════════════════
   Event Binding
   ════════════════════════════════════════════ */
function bindEvents() {

  /* ── Login flow ── */
  $('btn-send-code').addEventListener('click', () => {
    const phone = $('phone-input').value.trim();
    if (!phone) return;
    $('verify-phone-display').textContent = phone;
    showOverlay('overlay-verify');
  });

  $('btn-verify-back').addEventListener('click', () => showOverlay('overlay-login'));

  $('btn-verify').addEventListener('click', () => {
    if ($('code-input').value.trim().length < 4) return;
    showOverlay('overlay-profile');
  });

  $('resend-link').addEventListener('click', function () {
    this.textContent = 'Sent!';
    setTimeout(() => { this.textContent = 'Resend'; }, 2000);
  });

  $('btn-done-setup').addEventListener('click', () => {
    const name = $('name-input').value.trim();
    if (name) state.userName = name;
    state.userStatus = $('status-input').value.trim() || 'Available';
    enterApp();
  });

  /* ── Sidebar ── */
  $('btn-new-chat').addEventListener('click', () => showView('view-new-chat'));
  $('btn-settings').addEventListener('click', () => { updateSettingsUI(); showView('view-settings'); });
  $('sidebar-user').addEventListener('click', () => { populateProfileEdit(); showView('view-profile-edit'); });
  $('chat-search').addEventListener('input', (e) => renderChatList(e.target.value));

  /* ── Chat ── */
  $('msg-input').addEventListener('input', onMsgInput);
  $('msg-input').addEventListener('keydown', (e) => { if (e.key === 'Enter') sendMessage(); });
  $('send-btn').addEventListener('click', sendMessage);
  $('btn-emoji').addEventListener('click', toggleEmojiPicker);
  $('btn-attach').addEventListener('click', toggleAttachMenu);
  $('attach-photo').addEventListener('click', () => sendMedia('Photo'));
  $('attach-video').addEventListener('click', () => sendMedia('Video'));
  $('attach-document').addEventListener('click', () => sendMedia('Document'));
  $('btn-voice-call').addEventListener('click', () => startCall('voice'));
  $('btn-video-call').addEventListener('click', () => startCall('video'));
  $('btn-chat-info').addEventListener('click', openInfo);
  $('chat-header-info').addEventListener('click', openInfo);

  /* ── Recording ── */
  $('btn-mic').addEventListener('mousedown', startRecording);
  $('btn-mic').addEventListener('mouseup', stopRecording);
  $('btn-mic').addEventListener('touchstart', (e) => { e.preventDefault(); startRecording(); });
  $('btn-mic').addEventListener('touchend', (e) => { e.preventDefault(); stopRecording(); });
  $('btn-cancel-rec').addEventListener('click', cancelRecording);

  /* ── New Chat ── */
  $('btn-back-new-chat').addEventListener('click', () => {
    if (state.currentChatId) showView('view-chat');
    else showView('view-empty');
  });
  $('contact-search').addEventListener('input', (e) => renderContactList(e.target.value));
  $('btn-new-group').addEventListener('click', () => {
    state.selectedGroupContacts = [];
    $('group-search').value = '';
    renderGroupContactList();
    updateGroupSelectedBar();
    showView('view-group-create');
  });

  /* ── Group Create ── */
  $('btn-back-group-create').addEventListener('click', () => showView('view-new-chat'));
  $('group-search').addEventListener('input', (e) => renderGroupContactList(e.target.value));
  $('btn-group-next').addEventListener('click', () => {
    $('group-name-input').value = '';
    $('group-desc-input').value = '';
    showView('view-group-name');
  });
  $('btn-back-group-name').addEventListener('click', () => showView('view-group-create'));
  $('btn-create-group').addEventListener('click', createGroup);

  /* ── Info ── */
  $('btn-back-info').addEventListener('click', () => showView('view-chat'));

  /* ── Settings ── */
  $('btn-back-settings').addEventListener('click', () => {
    if (state.currentChatId) showView('view-chat');
    else showView('view-empty');
  });
  $('settings-profile-card').addEventListener('click', () => { populateProfileEdit(); showView('view-profile-edit'); });
  $('btn-blocked').addEventListener('click', () => showView('view-blocked'));
  $('btn-logout').addEventListener('click', logout);

  /* ── Profile Edit ── */
  $('btn-back-profile-edit').addEventListener('click', () => showView('view-settings'));
  $('btn-save-profile').addEventListener('click', saveProfile);

  /* ── Blocked ── */
  $('btn-back-blocked').addEventListener('click', () => showView('view-settings'));

  /* ── Call ── */
  $('ctrl-mute').addEventListener('click', () => $('ctrl-mute').classList.toggle('active-ctrl'));
  $('ctrl-speaker').addEventListener('click', () => $('ctrl-speaker').classList.toggle('active-ctrl'));
  $('ctrl-end').addEventListener('click', endCall);

  /* ── Toggles ── */
  document.querySelectorAll('[data-toggle]').forEach(el => {
    el.addEventListener('click', () => el.classList.toggle('on'));
  });

  /* ── Close menus on outside click ── */
  $('app').addEventListener('click', (e) => {
    if (!e.target.closest('#attach-menu') && !e.target.closest('#btn-attach')) closeAttachMenu();
    if (!e.target.closest('#emoji-picker') && !e.target.closest('#btn-emoji')) closeEmojiPicker();
  });
}

/* ════════════════════════════════════════════
   Overlay & View Management
   ════════════════════════════════════════════ */
function showOverlay(id) {
  document.querySelectorAll('.overlay').forEach(o => o.classList.add('hidden'));
  if (id) {
    const el = $(id);
    if (el) el.classList.remove('hidden');
  }
}

function enterApp() {
  showOverlay(null);
  $('main-layout').classList.remove('hidden');
  $('sidebar-user').textContent = state.userName[0].toUpperCase();
  renderChatList();
}

function showView(id) {
  closeEmojiPicker();
  closeAttachMenu();
  cancelRecording();
  document.querySelectorAll('.panel-view').forEach(v => v.classList.remove('active'));
  $(id).classList.add('active');

  if (id === 'view-new-chat') { $('contact-search').value = ''; renderContactList(); }
  if (id === 'view-chat' && state.currentChatId) renderChat();
}

/* ════════════════════════════════════════════
   Chat List
   ════════════════════════════════════════════ */
function renderChatList(filter = '') {
  const el = $('chat-list');
  const fl = filter.toLowerCase();
  let html = '';

  state.conversations.forEach(conv => {
    let name, initial;
    if (conv.type === 'individual') {
      const c = state.contacts.find(ct => ct.id === conv.contactId);
      if (!c) return;
      name = c.name; initial = c.initial;
    } else {
      name = conv.name; initial = name[0];
    }
    if (fl && !name.toLowerCase().includes(fl)) return;

    const last = conv.messages[conv.messages.length - 1];
    if (!last) return;
    let preview;
    if (last.type === 'media') preview = '[' + last.mediaType + ']';
    else if (last.type === 'voice') preview = '[Voice] ' + last.duration;
    else preview = (last.from === 'me' ? 'You: ' : (conv.type === 'group' ? last.from + ': ' : '')) + last.text;

    const isActive = conv.id === state.currentChatId;

    html += `
      <div class="chat-item${isActive ? ' active' : ''}" data-conv-id="${conv.id}">
        <div class="avatar">${initial}</div>
        <div class="chat-item-body">
          <div class="chat-item-name">${name}${conv.type === 'group' ? ' (group)' : ''}</div>
          <div class="chat-item-preview">${preview}</div>
        </div>
        <div class="chat-item-meta">
          ${last.time}
          ${conv.unread > 0 ? '<div class="unread-badge">' + conv.unread + '</div>' : ''}
        </div>
      </div>`;
  });

  el.innerHTML = html;

  el.querySelectorAll('.chat-item').forEach(item => {
    item.addEventListener('click', () => openChat(parseInt(item.dataset.convId)));
  });
}

/* ════════════════════════════════════════════
   Open & Render Chat
   ════════════════════════════════════════════ */
function openChat(convId) {
  state.currentChatId = convId;
  const conv = getConv(convId);
  if (!conv) return;
  conv.unread = 0;

  let name, initial;
  if (conv.type === 'individual') {
    const c = state.contacts.find(ct => ct.id === conv.contactId);
    name = c.name; initial = c.initial;
  } else {
    name = conv.name; initial = name[0];
  }

  $('chat-name').textContent = name;
  $('chat-avatar').textContent = initial;

  renderChatList($('chat-search').value);
  showView('view-chat');
}

function renderChat() {
  const conv = getConv(state.currentChatId);
  if (!conv) return;
  const el = $('chat-messages');
  let html = '';

  conv.messages.forEach(msg => {
    const isSent = msg.from === 'me';
    const cls = isSent ? 'sent' : 'received';

    if (msg.type === 'media') {
      html += `
        <div class="msg-row ${cls}">
          <div>
            <div class="msg-media">[${msg.mediaType}]</div>
            <div class="msg-time">${msg.time}</div>
          </div>
        </div>`;
    } else if (msg.type === 'voice') {
      let bars = '';
      for (let i = 0; i < 24; i++) {
        bars += `<div class="voice-bar" style="height:${Math.floor(Math.random() * 14) + 4}px;"></div>`;
      }
      html += `
        <div class="msg-row ${cls}">
          <div>
            <div class="msg-voice">
              <svg viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              <div class="voice-bars">${bars}</div>
              <span>${msg.duration}</span>
            </div>
            <div class="msg-time">${msg.time}</div>
          </div>
        </div>`;
    } else {
      const sender = (!isSent && conv.type === 'group')
        ? `<div class="msg-sender">${msg.from}</div>` : '';
      html += `
        <div class="msg-row ${cls}">
          <div class="msg-bubble">
            ${sender}${msg.text}
            <div class="msg-time">${msg.time}</div>
          </div>
        </div>`;
    }
  });

  el.innerHTML = html;
  requestAnimationFrame(() => { el.scrollTop = el.scrollHeight; });
}

/* ════════════════════════════════════════════
   Send Message
   ════════════════════════════════════════════ */
function onMsgInput() {
  const hasText = $('msg-input').value.trim().length > 0;
  $('send-btn').classList.toggle('disabled', !hasText);
  $('btn-mic').classList.toggle('hidden', hasText);
}

function sendMessage() {
  const text = $('msg-input').value.trim();
  if (!text) return;
  const conv = getConv(state.currentChatId);
  if (!conv) return;
  conv.messages.push({ from: 'me', text, time: nowTime() });
  $('msg-input').value = '';
  onMsgInput();
  renderChat();
  renderChatList($('chat-search').value);

  if (conv.type === 'individual') {
    setTimeout(() => simulateReply(conv), 1500 + Math.random() * 2000);
  }
}

function simulateReply(conv) {
  const replies = ['Got it!', 'Sure thing.', 'Sounds good!', 'Let me think about it.', 'OK!', 'Thanks!', 'Will do.', 'Hmm, maybe later.', 'Absolutely.', 'On it.'];
  const reply = replies[Math.floor(Math.random() * replies.length)];

  if (state.currentChatId !== conv.id) {
    conv.unread = (conv.unread || 0) + 1;
    const c = state.contacts.find(ct => ct.id === conv.contactId);
    if (c) showToast(c.name, reply);
  }

  conv.messages.push({ from: 'them', text: reply, time: nowTime() });

  if (state.currentChatId === conv.id) {
    renderChat();
  }
  renderChatList($('chat-search').value);
}

function sendMedia(type) {
  closeAttachMenu();
  const conv = getConv(state.currentChatId);
  if (!conv) return;
  conv.messages.push({ from: 'me', type: 'media', mediaType: type, time: nowTime() });
  renderChat();
  renderChatList($('chat-search').value);
}

/* ════════════════════════════════════════════
   Emoji Picker
   ════════════════════════════════════════════ */
function initEmojiPicker() {
  const emojis = ['😊','😂','❤️','👍','🎉','🔥','😍','🤔','😅','👋','💪','😎','🥳','😢','🙏','💯','✅','❌','⭐','🌙','😤','🤝','😏','🫡','🥺','💀','🤣','❤️‍🔥','🫶','😎'];
  const grid = $('emoji-grid');
  emojis.forEach(e => {
    const span = document.createElement('span');
    span.textContent = e;
    span.addEventListener('click', () => {
      $('msg-input').value += e;
      onMsgInput();
      closeEmojiPicker();
      $('msg-input').focus();
    });
    grid.appendChild(span);
  });
}

function toggleEmojiPicker() {
  $('emoji-picker').classList.toggle('open');
  closeAttachMenu();
}
function closeEmojiPicker() { $('emoji-picker').classList.remove('open'); }

/* ════════════════════════════════════════════
   Attachment Menu
   ════════════════════════════════════════════ */
function toggleAttachMenu() {
  $('attach-menu').classList.toggle('open');
  closeEmojiPicker();
}
function closeAttachMenu() { $('attach-menu').classList.remove('open'); }

/* ════════════════════════════════════════════
   Voice Recording
   ════════════════════════════════════════════ */
function startRecording() {
  if ($('msg-input').value.trim()) return;
  state.recSeconds = 0;
  $('rec-indicator').classList.add('active');
  $('send-btn').classList.add('hidden');
  $('btn-emoji').classList.add('hidden');
  $('btn-attach').classList.add('hidden');

  const wave = $('rec-wave');
  wave.innerHTML = '';
  for (let i = 0; i < 30; i++) {
    const bar = document.createElement('div');
    bar.className = 'rec-wave-bar';
    bar.style.animationDelay = (Math.random() * 0.5) + 's';
    wave.appendChild(bar);
  }

  state.recTimer = setInterval(() => {
    state.recSeconds++;
    const m = Math.floor(state.recSeconds / 60);
    const s = state.recSeconds % 60;
    $('rec-indicator').querySelector('span').textContent = m + ':' + String(s).padStart(2, '0');
  }, 1000);
}

function stopRecording() {
  if (!$('rec-indicator').classList.contains('active')) return;
  clearInterval(state.recTimer);
  resetRecordingUI();

  if (state.recSeconds > 0) {
    const conv = getConv(state.currentChatId);
    if (!conv) return;
    const m = Math.floor(state.recSeconds / 60);
    const s = state.recSeconds % 60;
    conv.messages.push({ from: 'me', type: 'voice', duration: m + ':' + String(s).padStart(2, '0'), time: nowTime() });
    renderChat();
    renderChatList($('chat-search').value);
  }
}

function cancelRecording() {
  clearInterval(state.recTimer);
  resetRecordingUI();
}

function resetRecordingUI() {
  $('rec-indicator').classList.remove('active');
  $('send-btn').classList.remove('hidden');
  $('btn-emoji').classList.remove('hidden');
  $('btn-attach').classList.remove('hidden');
  onMsgInput();
}

/* ════════════════════════════════════════════
   Contact List (New Chat)
   ════════════════════════════════════════════ */
function renderContactList(filter = '') {
  const el = $('contact-list');
  const fl = filter.toLowerCase();
  let html = '';

  state.contacts
    .filter(c => !fl || c.name.toLowerCase().includes(fl))
    .forEach(c => {
      html += `
        <div class="contact-item" data-contact-id="${c.id}">
          <div class="avatar-sm">${c.initial}</div>
          <div class="chat-item-name">${c.name}</div>
        </div>`;
    });

  el.innerHTML = html || '<div class="empty-state"><span>No contacts found</span></div>';

  el.querySelectorAll('.contact-item').forEach(item => {
    item.addEventListener('click', () => openChatFromContact(parseInt(item.dataset.contactId)));
  });
}

function openChatFromContact(contactId) {
  let conv = state.conversations.find(c => c.type === 'individual' && c.contactId === contactId);
  if (!conv) {
    conv = { id: Date.now(), type: 'individual', contactId, unread: 0, messages: [] };
    state.conversations.unshift(conv);
  }
  openChat(conv.id);
}

/* ════════════════════════════════════════════
   Group Creation
   ════════════════════════════════════════════ */
function renderGroupContactList(filter = '') {
  const el = $('group-contact-list');
  const fl = filter.toLowerCase();
  let html = '';

  state.contacts
    .filter(c => !fl || c.name.toLowerCase().includes(fl))
    .forEach(c => {
      const checked = state.selectedGroupContacts.includes(c.id);
      html += `
        <div class="contact-item${checked ? ' selected' : ''}" data-gc-id="${c.id}">
          <div class="contact-check${checked ? ' checked' : ''}"></div>
          <div class="avatar-sm">${c.initial}</div>
          <div class="chat-item-name">${c.name}</div>
        </div>`;
    });

  el.innerHTML = html;

  el.querySelectorAll('.contact-item').forEach(item => {
    item.addEventListener('click', () => toggleGroupContact(parseInt(item.dataset.gcId)));
  });
}

function toggleGroupContact(id) {
  const idx = state.selectedGroupContacts.indexOf(id);
  if (idx > -1) state.selectedGroupContacts.splice(idx, 1);
  else state.selectedGroupContacts.push(id);
  renderGroupContactList($('group-search').value);
  updateGroupSelectedBar();
}

function updateGroupSelectedBar() {
  const n = state.selectedGroupContacts.length;
  $('group-selected-count').textContent = n + ' selected';
  $('group-selected-bar').classList.toggle('visible', n > 0);
}

function createGroup() {
  const name = $('group-name-input').value.trim();
  if (!name) return;

  const conv = {
    id: Date.now(),
    type: 'group',
    name,
    description: $('group-desc-input').value.trim(),
    participants: [...state.selectedGroupContacts],
    unread: 0,
    messages: [{ from: 'me', text: 'Created group "' + name + '"', time: nowTime() }]
  };
  state.conversations.unshift(conv);
  renderChatList();
  openChat(conv.id);
}

/* ════════════════════════════════════════════
   Info Screen
   ════════════════════════════════════════════ */
function openInfo() {
  const conv = getConv(state.currentChatId);
  if (!conv) return;
  const el = $('info-content');
  const footer = $('info-footer');
  footer.innerHTML = '';

  if (conv.type === 'individual') {
    const c = state.contacts.find(ct => ct.id === conv.contactId);
    if (!c) return;
    $('info-title').textContent = c.name;
    el.innerHTML = `
      <div class="info-header">
        <div class="avatar-lg">${c.initial}</div>
        <div class="panel-header-name" style="font-size:18px;">${c.name}</div>
        <div class="panel-header-status">Available</div>
      </div>
      <div class="section-label">Options</div>
      <div class="settings-item"><span class="settings-label">Mute Notifications</span><div class="toggle" data-toggle></div></div>
      <div class="settings-item"><span class="settings-label">Starred Messages</span><svg viewBox="0 0 24 24" style="width:16px;height:16px;stroke:#999;fill:none;stroke-width:1.5;"><polyline points="9 18 15 12 9 6"/></svg></div>
      <div class="settings-item"><span class="settings-label" style="font-weight:bold;">Block ${c.name}</span></div>`;

    el.querySelectorAll('[data-toggle]').forEach(t => t.addEventListener('click', () => t.classList.toggle('on')));

  } else {
    $('info-title').textContent = 'Group Info';
    let pHtml = '';
    conv.participants.forEach(pid => {
      const c = state.contacts.find(ct => ct.id === pid);
      if (!c) return;
      pHtml += `
        <div class="group-participant">
          <div class="avatar-sm">${c.initial}</div>
          <div class="group-participant-name">${c.name}</div>
          ${pid === conv.participants[0] ? '<span class="group-role">Admin</span>' : ''}
        </div>`;
    });
    pHtml += `
      <div class="group-participant">
        <div class="avatar-sm">${state.userName[0].toUpperCase()}</div>
        <div class="group-participant-name">${state.userName} (You)</div>
        <span class="group-role">Admin</span>
      </div>`;

    el.innerHTML = `
      <div class="info-header">
        <div class="avatar-lg">${conv.name[0]}</div>
        <div class="panel-header-name" style="font-size:18px;">${conv.name}</div>
        <div class="panel-header-status">${conv.participants.length + 1} participants</div>
        ${conv.description ? '<div class="info-desc">' + conv.description + '</div>' : ''}
      </div>
      <div class="section-label">Participants</div>
      ${pHtml}
      <div class="settings-item">
        <svg viewBox="0 0 24 24" style="width:18px;height:18px;stroke:#111;fill:none;stroke-width:1.5;flex-shrink:0;"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        <span class="settings-label">Add Participant</span>
      </div>
      <div class="section-label">Group Settings</div>
      <div class="settings-item"><span class="settings-label">Mute Notifications</span><div class="toggle" data-toggle></div></div>
      <div class="settings-item"><span class="settings-label">Only Admins Can Send</span><div class="toggle" data-toggle></div></div>
      <div class="settings-item"><span class="settings-label">Edit Group Name</span><svg viewBox="0 0 24 24" style="width:16px;height:16px;stroke:#999;fill:none;stroke-width:1.5;"><polyline points="9 18 15 12 9 6"/></svg></div>`;

    el.querySelectorAll('[data-toggle]').forEach(t => t.addEventListener('click', () => t.classList.toggle('on')));

    footer.innerHTML = '<button class="btn btn-full btn-danger" id="btn-leave-group">Leave Group</button>';
    $('btn-leave-group').addEventListener('click', leaveGroup);
  }

  showView('view-info');
}

function leaveGroup() {
  const idx = state.conversations.findIndex(c => c.id === state.currentChatId);
  if (idx > -1) state.conversations.splice(idx, 1);
  state.currentChatId = null;
  renderChatList();
  showView('view-empty');
}

/* ════════════════════════════════════════════
   Calls
   ════════════════════════════════════════════ */
function startCall(type) {
  state.callType = type;
  const conv = getConv(state.currentChatId);
  if (!conv) return;
  let name, initial;
  if (conv.type === 'individual') {
    const c = state.contacts.find(ct => ct.id === conv.contactId);
    name = c.name; initial = c.initial;
  } else {
    name = conv.name; initial = name[0];
  }

  $('call-avatar').textContent = initial;
  $('call-name').textContent = name;
  $('call-status').textContent = type === 'video' ? 'Video Calling...' : 'Calling...';
  $('call-timer').classList.add('hidden');
  $('ctrl-mute').classList.remove('active-ctrl');
  $('ctrl-speaker').classList.remove('active-ctrl');

  showOverlay('overlay-call');

  setTimeout(() => {
    if (!$('overlay-call').classList.contains('hidden')) {
      $('call-status').textContent = type === 'video' ? 'Video Connected' : 'Connected';
      state.callSeconds = 0;
      $('call-timer').classList.remove('hidden');
      state.callTimer = setInterval(() => {
        state.callSeconds++;
        const m = Math.floor(state.callSeconds / 60);
        const s = state.callSeconds % 60;
        $('call-timer').textContent = String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
      }, 1000);
    }
  }, 2000);
}

function endCall() {
  clearInterval(state.callTimer);
  $('overlay-call').classList.add('hidden');
}

/* ════════════════════════════════════════════
   Settings
   ════════════════════════════════════════════ */
function updateSettingsUI() {
  $('settings-name').textContent = state.userName;
  $('settings-avatar').textContent = state.userName[0].toUpperCase();
  $('settings-status').textContent = state.userStatus;
}

function populateProfileEdit() {
  $('edit-name').value = state.userName;
  $('edit-status').value = state.userStatus;
}

function saveProfile() {
  const name = $('edit-name').value.trim();
  if (name) state.userName = name;
  state.userStatus = $('edit-status').value.trim() || 'Available';
  $('sidebar-user').textContent = state.userName[0].toUpperCase();
  showView('view-settings');
  updateSettingsUI();
}

function logout() {
  state.currentChatId = null;
  showOverlay('overlay-login');
  $('main-layout').classList.add('hidden');
  $('phone-input').value = '';
  $('code-input').value = '';
}

/* ════════════════════════════════════════════
   Toast Notification
   ════════════════════════════════════════════ */
function showToast(name, msg) {
  clearTimeout(state.toastTimer);
  const toast = $('toast');
  toast.querySelector('.toast-avatar').textContent = name[0].toUpperCase();
  toast.querySelector('.toast-name').textContent = name;
  toast.querySelector('.toast-msg').textContent = msg;
  toast.classList.add('show');
  state.toastTimer = setTimeout(() => toast.classList.remove('show'), 3500);
}

/* ════════════════════════════════════════════
   Helpers
   ════════════════════════════════════════════ */
function getConv(id) {
  return state.conversations.find(c => c.id === id);
}

function nowTime() {
  const d = new Date();
  return d.getHours() + ':' + String(d.getMinutes()).padStart(2, '0');
}

/* ════════════════════════════════════════════
   Boot
   ════════════════════════════════════════════ */
loadData();
