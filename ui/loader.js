/* ════════════════════════════════════════════
   loader.js — Partial HTML loader
   Fetches each HTML partial, injects it into its
   placeholder div, then boots app.js once all
   partials are ready.

   Partial map: placeholder-id → file path
   ════════════════════════════════════════════ */
const PARTIALS = [
  { id: 'partial-toast',            file: 'partials/toast.html' },
  { id: 'partial-overlays',         file: 'partials/overlays.html' },
  { id: 'partial-sidebar',          file: 'partials/sidebar.html' },
  { id: 'partial-view-empty',       file: 'partials/view-empty.html' },
  { id: 'partial-view-chat',        file: 'partials/view-chat.html' },
  { id: 'partial-view-new-chat',    file: 'partials/view-new-chat.html' },
  { id: 'partial-view-group',       file: 'partials/view-group.html' },
  { id: 'partial-view-info',        file: 'partials/view-info.html' },
  { id: 'partial-view-settings',    file: 'partials/view-settings.html' },
  { id: 'partial-view-profile-edit',file: 'partials/view-profile-edit.html' },
  { id: 'partial-view-blocked',     file: 'partials/view-blocked.html' },
];

async function loadPartials() {
  await Promise.all(
    PARTIALS.map(async ({ id, file }) => {
      const res  = await fetch(file);
      const html = await res.text();
      document.getElementById(id).innerHTML = html;
    })
  );
}

async function boot() {
  try {
    await loadPartials();
  } catch (err) {
    document.getElementById('app').innerHTML = `
      <div style="display:flex;align-items:center;justify-content:center;height:100%;font-family:system-ui;">
        <div style="text-align:center;color:#666;padding:40px;">
          <div style="font-weight:700;font-size:15px;margin-bottom:12px;">Could not load UI partials</div>
          <p>You must serve this project with a local HTTP server.</p>
          <p style="margin-top:8px;font-family:monospace;background:#f4f4f4;padding:6px 12px;display:inline-block;">python -m http.server</p>
          <p style="margin-top:8px;color:#aaa;font-size:12px;">Error: ${err.message}</p>
        </div>
      </div>`;
    return;
  }

  /* Dynamically load app.js after DOM is ready */
  const script = document.createElement('script');
  script.src = 'app.js';
  document.body.appendChild(script);
}

boot();
