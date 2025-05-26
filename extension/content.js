function createOverlay(box, translation, imageRect, naturalSize, displaySize, originalText) {
  const [x1, y1, x2, y2] = box;

  const scaleX = displaySize.width / naturalSize.width;
  const scaleY = displaySize.height / naturalSize.height;

  const left = imageRect.left + x1 * scaleX;
  const top = imageRect.top + y1 * scaleY;
  const width = (x2 - x1) * scaleX;
  const height = (y2 - y1) * scaleY;

  const div = document.createElement('div');
  div.style.position = 'absolute';

  // Overlay: show translation and original text based on user setting
  let overlayMode = localStorage.getItem('androidext_overlay_mode') || 'english';
  if (window.androidextOverlayMode) overlayMode = window.androidextOverlayMode;
  let overlayHTML = '';
  if (overlayMode === 'both') {
    overlayHTML = `<div style="width:100%;text-align:center;">${translation}</div>`;
    if (originalText && originalText !== translation) {
      overlayHTML += `<div style="font-size:0.7em;opacity:0.7;margin-top:2px;overflow-wrap:break-word;">${originalText}</div>`;
    }
  } else if (overlayMode === 'japanese') {
    overlayHTML = `<div style="width:100%;text-align:center;">${originalText || translation}</div>`;
  } else {
    overlayHTML = `<div style="width:100%;text-align:center;">${translation}</div>`;
  }
  div.innerHTML = overlayHTML;

  // Expand the overlay area by 5px on all sides
  const expand = 5;
  div.style.left = `${left - expand}px`;
  div.style.top = `${top - expand}px`;
  div.style.width = `${width + expand * 2}px`;
  div.style.height = `${height + expand * 2}px`;

  // Check the background color of the underlying image/chatbubble for mostly black/white
  let bgColor = null;
  let textColor = '#000000';
  try {
    const canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.round(width));
    canvas.height = Math.max(1, Math.round(height));
    const ctx = canvas.getContext('2d');
    const el = document.elementFromPoint(left + width / 2, top + height / 2);
    if (el && el.tagName === 'IMG') {
      ctx.drawImage(el, x1, y1, x2 - x1, y2 - y1, 0, 0, canvas.width, canvas.height);
      // Sample a grid of pixels to determine if the region is mostly black or white
      let black = 0, white = 0, total = 0;
      for (let i = 0; i < canvas.width; i += Math.max(1, Math.floor(canvas.width / 6))) {
        for (let j = 0; j < canvas.height; j += Math.max(1, Math.floor(canvas.height / 6))) {
          const d = ctx.getImageData(i, j, 1, 1).data;
          const avg = (d[0] + d[1] + d[2]) / 3;
          if (d[3] < 32) continue; // transparent
          if (avg < 64) black++;
          else if (avg > 192) white++;
          total++;
        }
      }
      if (total > 0) {
        if (black / total > 0.5 && white / total < 0.2) {
          bgColor = '#000000';
          textColor = '#ffffff';
        } else if (white / total > 0.5 && black / total < 0.2) {
          bgColor = '#ffffff';
          textColor = '#000000';
        } else if (black / total > 0.3 && white / total > 0.3) {
          // Mixed: use semi-transparent black with white text
          bgColor = 'rgba(0,0,0,0.7)';
          textColor = '#ffffff';
        } else {
          // Default to light gray
          bgColor = '#f3f3f3';
          textColor = '#000000';
        }
      }
    }
  } catch (e) { /* fallback to default */ }
  div.style.backgroundColor = bgColor || '#ffffff';
  div.style.color = textColor;

  div.style.opacity = '1';
  div.style.mixBlendMode = 'normal';
  div.style.backdropFilter = 'none';
  div.style.filter = 'none';
  div.style.fontFamily = "'Noto Sans JP', sans-serif";
  div.style.display = 'flex';
  div.style.alignItems = 'center';
  div.style.justifyContent = 'center';
  div.style.padding = '2px';
  div.style.border = '0px solid black';
  div.style.zIndex = 9999;
  div.style.pointerEvents = 'auto'; // Make overlay selectable and interactive
  div.style.userSelect = 'text'; // Allow text selection
  div.style.overflow = 'hidden';
  div.style.textAlign = 'center';
  div.style.lineHeight = '1.1';
  div.style.wordBreak = 'break-word';
  div.style.whiteSpace = 'pre-line';
  // Responsive font size based on expanded box height and width, ensuring text fits
  const minFont = 8;
  const maxFont = 32;
  // Create a span to measure text size
  const measureSpan = document.createElement('span');
  measureSpan.textContent = translation;
  measureSpan.style.position = 'absolute';
  measureSpan.style.visibility = 'hidden';
  measureSpan.style.fontFamily = div.style.fontFamily;
  measureSpan.style.fontWeight = div.style.fontWeight;
  measureSpan.style.whiteSpace = 'pre-line';
  measureSpan.style.lineHeight = div.style.lineHeight;
  measureSpan.style.padding = div.style.padding;
  document.body.appendChild(measureSpan);
  let fontSize = maxFont;
  const boxW = width + expand * 2;
  const boxH = height + expand * 2;
  while (fontSize > minFont) {
    measureSpan.style.fontSize = (fontSize + 3) + 'px';
    if (measureSpan.offsetWidth <= boxW && measureSpan.offsetHeight <= boxH) break;
    fontSize -= 1;
  }
  div.style.fontSize = (fontSize + 1) + 'px';
  document.body.removeChild(measureSpan);

  // Store original text for context menu access
  div.dataset.originalText = originalText || translation;
  div.dataset.translationText = translation;

  // Always bring overlay to top and highlight on left click
  div.addEventListener('pointerdown', function(e) {
    if (e.button === 0 || e.button === 2) { // Left or Right click
      e.stopPropagation();
      e.preventDefault();
      // Remove highlight from all overlays
      document.querySelectorAll('.androidext-ocr-overlay').forEach(d => {
        d.style.outline = '';
      });
      // Highlight this overlay
      div.style.outline = '2px solid #4f8cff';
      // Bring to top
      div.style.zIndex = 10001;
      // Mark as selected
      div.classList.add('androidext-selected-ocr-overlay');
      // Remove selection after 2 seconds
      setTimeout(() => {
        div.style.outline = '';
        div.style.zIndex = 9999;
        div.classList.remove('androidext-selected-ocr-overlay');
      }, 2000);
      // Check for overlaps and adjust opacity
      document.querySelectorAll('.androidext-ocr-overlay').forEach(other => {
        if (other !== div) {
          const r1 = div.getBoundingClientRect();
          const r2 = other.getBoundingClientRect();
          if (!(r2.right < r1.left || r2.left > r1.right || r2.bottom < r1.top || r2.top > r1.bottom)) {
            // Overlapping
            div.style.opacity = '0.7';
            other.style.opacity = '0.7';
          } else {
            other.style.opacity = '1';
          }
        }
      });
      // Show context menu on left click
      div.dispatchEvent(new MouseEvent('contextmenu', {
        bubbles: true,
        cancelable: true,
        view: window,
        clientX: e.clientX,
        clientY: e.clientY
      }));
    }
  });

  // Add context menu (right-click) for original/translation/dictionary
  div.addEventListener('contextmenu', function(e) {
    if (e.button === 2) {
      e.stopPropagation();
    };
    div.style.outline = '2px solid #4f8cff';
    e.preventDefault();
    // Remove any existing custom menu
    document.querySelectorAll('.androidext-context-menu').forEach(m => m.remove());
    // Create menu
    const menu = document.createElement('div');
    menu.className = 'androidext-context-menu';
    menu.style.position = 'fixed';
    menu.style.left = e.clientX + 'px';
    menu.style.top = e.clientY + 'px';
    menu.style.background = '#fff';
    menu.style.border = '1px solid #4f8cff';
    menu.style.borderRadius = '6px';
    menu.style.boxShadow = '0 2px 8px #38e8ff55';
    menu.style.zIndex = 20000;
    menu.style.fontFamily = div.style.fontFamily;
    menu.style.fontSize = '14px';
    menu.style.color = '#222';
    menu.style.minWidth = '160px';
    menu.style.cursor = 'pointer';
    menu.style.userSelect = 'none';
    menu.style.padding = '4px 0';
    // Menu items
    const items = [
      { label: null, action: null, isLabel: true }, // Placeholder for original text words
      { label: 'Copy Original', action: () => navigator.clipboard.writeText(div.dataset.originalText || ''), isLabel: false },
      { label: 'Copy Translation', action: () => navigator.clipboard.writeText(div.dataset.translationText || ''), isLabel: false },
      { label: 'Dictionary Lookup', action: async () => {
        const offline = localStorage.getItem('androidext_offline_dict') === '1';
        if (offline) {
          await loadJMDict();
          const result = lookupJMDict(div.dataset.originalText || '');
          alert(result ? JSON.stringify(result) : 'No dictionary entry found.');
        } else {
          const url = `https://jisho.org/search/${encodeURIComponent(div.dataset.originalText || '')}`;
          window.open(url, '_blank');
        }
      }, isLabel: false },
      { label: '🕬 TTS', action: () => {
        // Store original background color
        const originalBg = div.style.backgroundColor;
        speakText(div.dataset.originalText || '', (word) => {
          // Highlight logic: e.g., flash overlay or word
          div.style.backgroundColor = '#eaf3ff';
          setTimeout(() => { 
            div.style.backgroundColor = originalBg;
          }, 500);
        });
      }, isLabel: false }
    ];
    items.forEach(item => {
      const el = document.createElement('div');
      el.textContent = item.label;
      el.style.padding = item.isLabel ? '8px 18px 4px 18px' : '8px 18px';
      el.style.fontWeight = item.isLabel ? 'bold' : 'normal';
      el.style.background = item.isLabel ? '#f5faff' : '';
      if (!item.isLabel) {
        el.onmouseenter = () => el.style.background = '#eaf3ff';
        el.onmouseleave = () => el.style.background = '';
        el.onclick = () => { item.action(); menu.remove(); };
      }
      menu.appendChild(el);
    });
    // Add original text as selectable words
    const originalText = div.dataset.originalText || '';
    if (originalText) {
      const wordContainer = document.createElement('div');
      wordContainer.style.display = 'flex';
      wordContainer.style.flexWrap = 'wrap';
      wordContainer.style.gap = '4px';
      wordContainer.style.padding = '8px 18px 4px 18px';
      wordContainer.style.background = '#f5faff';
      wordContainer.style.fontWeight = 'bold';
      wordContainer.style.userSelect = 'text';
      wordContainer.onmousedown = (ev) => { ev.stopPropagation(); };
      wordContainer.onpointerdown = (ev) => { ev.stopPropagation(); };
      wordContainer.onwheel = (ev) => { ev.stopPropagation(); };
      // Split by spaces (or treat as chars if no spaces)
      const words = originalText.includes(' ') ? originalText.split(/\s+/) : originalText.split('');
      words.forEach(word => {
        const span = document.createElement('span');
        span.textContent = word;
        span.style.cursor = 'pointer';
        span.style.padding = '2px 4px';
        span.style.borderRadius = '4px';
        span.onmouseenter = () => span.style.background = '#eaf3ff';
        span.onmouseleave = () => span.style.background = '';
        span.onclick = (ev) => {
          ev.stopPropagation();
          const url = `https://jisho.org/search/${encodeURIComponent(word)}`;
          window.open(url, '_blank');
        };
        wordContainer.appendChild(span);
      });
      menu.appendChild(wordContainer);
    }
    // Prevent menu from closing on scroll/drag/select inside wordContainer
    menu.onmousedown = (ev) => ev.stopPropagation();
    menu.onpointerdown = (ev) => ev.stopPropagation();
    menu.onwheel = (ev) => ev.stopPropagation();
    document.body.appendChild(menu);
    // Remove menu on click elsewhere
    document.addEventListener('click', function removeMenu() {
      menu.remove();
      document.removeEventListener('click', removeMenu);
    });
  });

  div.classList.add('androidext-ocr-overlay');

  document.body.appendChild(div);
}






async function getApiEndpoint() {
  return new Promise((resolve) => {
    if (!chrome?.storage?.local) {
      console.warn('chrome.storage.local not available, using default.');
      return resolve('http://localhost:8000');
    }
    chrome.storage.local.get(['apiEndpoint'], (result) => {
      resolve(result.apiEndpoint || 'http://localhost:8000');
    });
  });
}

async function speakText(text, highlightCallback) {
  try {
    const endpoint = await getApiEndpoint();

    // Get ttsLang from new settings object
    let ttsLang = 'ja';
    try {
      const settings = JSON.parse(localStorage.getItem('androidext_settings') || '{}');
      if (settings.ttsLang) ttsLang = settings.ttsLang;
    } catch {}

    if (window.androidextTTSLang) ttsLang = window.androidextTTSLang;

    const res = await fetch(`${endpoint.replace(/\/$/, '')}/tts_get`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, lang: ttsLang })
    });

    if (!res.ok) {
      let msg = 'TTS backend error';
      try { msg = (await res.json()).error || msg; } catch {}
      throw new Error(msg);
    }

    const wavBlob = await res.blob();
    const audio = new Audio(URL.createObjectURL(wavBlob));
    audio.play().catch(err => {
      console.warn('[TTS] Audio play failed:', err);
      showTTSWarning('Audio playback failed. Try clicking the page first.');
    });

    if (highlightCallback) highlightCallback(text);
  } catch (e) {
    console.warn('[TTS] Backend TTS failed:', e);
    showTTSWarning('TTS failed: ' + (e?.message || e));
  }
}


async function getClientIP() {
  try {
    const response = await fetch('https://api.ipify.org?format=json');
    const data = await response.json();
    return data.ip;
  } catch (err) {
    console.warn('Could not fetch IP:', err);
    return 'unknown';
  }
}

function getRealImageUrl(img) {
  // Prefer data-srcset, then srcset, then data-src, then src
  let url = '';
  if (img.getAttribute('data-srcset')) {
    url = img.getAttribute('data-srcset').split(',')[0].trim().split(' ')[0];
  } else if (img.getAttribute('srcset')) {
    url = img.getAttribute('srcset').split(',')[0].trim().split(' ')[0];
  } else if (img.getAttribute('data-src')) {
    url = img.getAttribute('data-src');
  } else {
    url = img.src;
  }
  // If url is relative, resolve to absolute
  if (url && !/^https?:\/\//.test(url)) {
    const a = document.createElement('a');
    a.href = url;
    url = a.href;
  }
  return url;
}


async function processImage(img, currentIndex, totalCount, progressTextElem, endpoint) {
  const imageUrl = getRealImageUrl(img);
  const rect = img.getBoundingClientRect();
  const ip = await getClientIP();

  try {
    const res = await fetch(`${endpoint.replace(/\/$/, '')}/predict_url`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'bypass-tunnel-reminder': 'true'
      },
      body: JSON.stringify({
        image_url: imageUrl,
        client_ip: ip
      })
    });

    const data = await res.json();
    if (data.status !== 'ok') return;

    const naturalSize = { width: img.naturalWidth, height: img.naturalHeight };
    const displaySize = { width: rect.width, height: rect.height };

    data.regions.forEach(region => {
      createOverlay(region.box, region.text, rect, naturalSize, displaySize, region.original_text); // Remains await-able if needed, but not strictly necessary here
    });

    progressTextElem.textContent = `${currentIndex + 1} / ${totalCount}`;
    // Send progress to popup if available
    if (window.__androidext_progress) {
      window.__androidext_progress(currentIndex + 1, totalCount);
    } else {
      window.postMessage({ type: 'ANDROIDEXT_PROGRESS', current: currentIndex + 1, total: totalCount }, '*');
    }
    progressTextElem.style.color = '#fff';
  } catch (e) {
    console.error('Error sending image URL to backend:', e);
  }
}


(async () => {
  window.scrollTo({ top: 0, behavior: 'instant' });

  const endpoint = await getApiEndpoint();
  const images = Array.from(document.images).filter(img =>
    img.naturalWidth > 300 && img.naturalHeight > 300 && img.src.startsWith('http')
  );

  if (images.length === 0) return;

  const progressTextElem = document.createElement('div');
  progressTextElem.style.position = 'fixed';
  progressTextElem.style.top = '10px';
  progressTextElem.style.right = '10px';
  progressTextElem.style.background = 'linear-gradient(90deg, #4f8cff, #38e8ff)';
  progressTextElem.style.color = '#fff';
  progressTextElem.style.fontWeight = 'bold';
  progressTextElem.style.fontSize = '16px';
  progressTextElem.style.padding = '7px 16px';
  progressTextElem.style.border = 'none';
  progressTextElem.style.borderRadius = '8px';
  progressTextElem.style.boxShadow = '0 0 12px 2px #38e8ff99';
  progressTextElem.style.zIndex = 10000;
  progressTextElem.style.letterSpacing = '1px';
  progressTextElem.style.textShadow = '0 2px 8px #38e8ff99';
  progressTextElem.style.transition = 'opacity 0.3s';
  document.body.appendChild(progressTextElem);

  for (let i = 0; i < images.length; i++) {
    await processImage(images[i], i, images.length, progressTextElem, endpoint);
  }

  progressTextElem.remove();
  // Hide popup progress at the end
  if (window.__androidext_progress) {
    window.__androidext_progress(images.length, images.length);
  } else {
    window.postMessage({ type: 'ANDROIDEXT_PROGRESS', current: images.length, total: images.length }, '*');
  }
})();

// --- First Setup Modal (only on first install) ---
(async function showFirstSetupModalIfNeeded() {
  let shown = false;
  // Prefer chrome.storage.local if available
  if (window.chrome && chrome.storage && chrome.storage.local) {
    chrome.storage.local.get(['androidext_firstsetup_shown'], (result) => {
      if (!result.androidext_firstsetup_shown) {
        shown = true;
        showFirstSetupModal();
        chrome.storage.local.set({ androidext_firstsetup_shown: true });
      }
    });
  } else {
    // Fallback to localStorage
    if (!localStorage.getItem('androidext_firstsetup_shown')) {
      shown = true;
      showFirstSetupModal();
      localStorage.setItem('androidext_firstsetup_shown', '1');
    }
  }


  function showFirstSetupModal() {
    const modal = document.createElement('div');
    modal.id = 'androidext-firstsetup-modal';
    modal.style.position = 'fixed';
    modal.style.top = '0';
    modal.style.left = '0';
    modal.style.width = '100vw';
    modal.style.height = '100vh';
    modal.style.background = 'rgba(0,0,0,0.35)';
    modal.style.display = 'flex';
    modal.style.alignItems = 'center';
    modal.style.justifyContent = 'center';
    modal.style.zIndex = '2147483647';
    modal.innerHTML = `
      <div style="background: #fff; border-radius: 16px; box-shadow: 0 4px 32px #38e8ff55; padding: 36px 48px; min-width: 320px; max-width: 90vw; text-align: center; font-family: 'Noto Sans JP', sans-serif;">
        <div style="font-size: 2em; font-weight: bold; color: #4f8cff; margin-bottom: 18px;">First Time?</div>
        <div style="font-size: 1.1em; color: #222;">Make sure you stay scrolled at top for textboxes to not get offset</div>
      </div>
    `;
    document.body.appendChild(modal);
    setTimeout(() => {
      modal.style.transition = 'opacity 0.5s';
      modal.style.opacity = '0';
      setTimeout(() => { modal.remove(); }, 500);
    }, 3200);
  }
})();

function showTTSWarning(msg) {
  // Show a non-intrusive warning at the top right
  let warn = document.getElementById('androidext-tts-warn');
  if (!warn) {
    warn = document.createElement('div');
    warn.id = 'androidext-tts-warn';
    warn.style.position = 'fixed';
    warn.style.top = '16px';
    warn.style.right = '16px';
    warn.style.background = '#fffbe8';
    warn.style.color = '#d12c2c';
    warn.style.fontWeight = 'bold';
    warn.style.fontSize = '15px';
    warn.style.padding = '10px 18px';
    warn.style.border = '1px solid #ffe0a0';
    warn.style.borderRadius = '8px';
    warn.style.boxShadow = '0 2px 8px #ffe0a055';
    warn.style.zIndex = 2147483647;
    warn.style.transition = 'opacity 0.5s';
    document.body.appendChild(warn);
  }
  warn.textContent = msg;
  warn.style.opacity = '1';
  setTimeout(() => {
    warn.style.opacity = '0';
    setTimeout(() => { if (warn.parentNode) warn.parentNode.removeChild(warn); }, 800);
  }, 3200);
}
