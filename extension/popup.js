document.getElementById('setBtn').addEventListener('click', async () => {
  const endpoint = document.getElementById('endpoint').value;
  await chrome.storage.local.set({ apiEndpoint: endpoint });
  alert('Endpoint saved!');
});

document.getElementById('translateBtn').addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    files: ['content.js']
  });
  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => { window.androidextRunOCR && window.androidextRunOCR(); }
  });
});

// OCR model dropdown logic
const ocrModelSelect = document.getElementById('ocrModel');
if (ocrModelSelect) {
  const savedOcr = localStorage.getItem('androidext_ocr_model') || 'default';
  ocrModelSelect.value = savedOcr;
  ocrModelSelect.addEventListener('change', async () => {
    localStorage.setItem('androidext_ocr_model', ocrModelSelect.value);
  });
}

async function populateOcrModels() {
  const ocrModelSelect = document.getElementById('ocrModel');
  let endpoint = localStorage.getItem('apiEndpoint') || document.getElementById('endpoint').value || 'http://localhost:8000';
  endpoint = endpoint.replace(/\/$/, '');
  try {
    const res = await fetch(endpoint + '/list_ocrmodels');
    const data = await res.json();
    if (data.ocr_models && Array.isArray(data.ocr_models)) {
      ocrModelSelect.innerHTML = data.ocr_models.map(([id, label]) => `<option value="${id}">${label}</option>`).join('');
      const savedOcr = localStorage.getItem('androidext_ocr_model') || 'default';
      if (data.ocr_models.some(([n]) => n === savedOcr)) {
        ocrModelSelect.value = savedOcr;
      }
    }
  } catch (e) {
    ocrModelSelect.innerHTML = '<option value="default">YOLO + manga_ocr (2GB)</option><option value="hal-utokyo/MangaLMM">MangaLMM (HuggingFace) (10-15GB)</option>';
  }

  try {
    const res = await fetch(endpoint + '/current_ocrmodel');
    const data = await res.json();
    if (data.current_ocr_model) {
      ocrModelSelect.value = data.current_ocr_model;
      localStorage.setItem('androidext_ocr_model', data.current_ocr_model);
    }
  } catch (e) {}
}
if (document.getElementById('ocrModel')) populateOcrModels();

window.addEventListener('DOMContentLoaded', function() {
  const addOcrBtn = document.getElementById('addOcrModelBtn');
  if (addOcrBtn) {
    addOcrBtn.onclick = async function() {
      const modelId = prompt('Enter HuggingFace model id (e.g. hal-utokyo/MangaLMM):');
      const modelName = prompt('Enter display name for this model:');
      if (!modelId || !modelName) return;
      let endpoint = localStorage.getItem('apiEndpoint') || document.getElementById('endpoint').value || 'http://localhost:8000';
      endpoint = endpoint.replace(/\/$/, '');
      await fetch(endpoint + '/add_ocr_model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: modelId, name: modelName })
      });
      await populateOcrModels();
    };
  }
});

window.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'ANDROIDEXT_PROGRESS') {
    const { current, total } = event.data;
    const progressElem = document.getElementById('progress-glow');
    if (progressElem) {
      progressElem.textContent = `${current} / ${total}`;
      progressElem.style.display = 'block';
      if (current === total) {
        setTimeout(() => progressElem.style.display = 'none', 1200);
      }
    }
  }
});

document.addEventListener('DOMContentLoaded', function() {
  const settingsBtn = document.getElementById('settingsBtn');
  const settingsModal = document.getElementById('settingsModal');
  const closeSettings = document.getElementById('closeSettings');
  const saveSettings = document.getElementById('saveSettings');
  const modelSelect = document.getElementById('modelSelect');
  const ttsLang = document.getElementById('ttsLang');

  async function populateModels() {
    let endpoint = localStorage.getItem('apiEndpoint') || document.getElementById('endpoint').value || 'http://localhost:8000';
    endpoint = endpoint.replace(/\/$/, '');
    
    try {
      const currentRes = await fetch(endpoint + '/current_aimodel');
      const currentData = await currentRes.json();
      const currentModel = currentData.current_model;

      const res = await fetch(endpoint + '/list_aimodels');
      const data = await res.json();
      if (data.models && Array.isArray(data.models)) {
        modelSelect.innerHTML = data.models.map(([name, ram]) => 
          `<option value="${name}" ${currentModel === name ? 'selected' : ''}>${name} (${ram})</option>`
        ).join('');
        
        const settings = JSON.parse(localStorage.getItem('androidext_settings') || '{}');
        if (settings.model && data.models.some(([n]) => n === settings.model)) {
          modelSelect.value = settings.model;
        }
      }
    } catch (e) {
      modelSelect.innerHTML = '<option value="cyy0/JaptoEnBetterMTL-2">cyy0/JaptoEnBetterMTL-2 (2GB)</option><option value="Helsinki-NLP/opus-mt-ja-en">Helsinki-NLP/opus-mt-ja-en (1.2GB)</option>';
    }
  }

  const buttonContainer = document.createElement('div');
  buttonContainer.style.display = 'flex';
  buttonContainer.style.alignItems = 'center';
  buttonContainer.style.gap = '5px';
  modelSelect.parentNode.insertBefore(buttonContainer, modelSelect.nextSibling);

  const refreshModelsBtn = document.createElement('button');
  refreshModelsBtn.textContent = '↻';
  refreshModelsBtn.title = 'Refresh model list';
  refreshModelsBtn.className = 'btn';
  refreshModelsBtn.style = "padding:4px 10px;font-size:13px;min-width:unset;width:auto;";
  refreshModelsBtn.onclick = () => populateModels();
  buttonContainer.appendChild(refreshModelsBtn);

  const addModelBtn = document.createElement('button');
  addModelBtn.textContent = '+';
  addModelBtn.title = 'Add new AI model';
  addModelBtn.className = 'btn';
  addModelBtn.style = "padding:4px 10px;font-size:13px;min-width:unset;width:auto;";
  addModelBtn.onclick = async function() {
    const modelId = prompt('Enter model id (e.g. Helsinki-NLP/opus-mt-ja-en):');
    const modelName = prompt('Enter display name for this model:');
    const ramUsage = prompt('Enter RAM usage (e.g. 2GB):');
    if (!modelId || !modelName || !ramUsage) return;
    
    let endpoint = localStorage.getItem('apiEndpoint') || document.getElementById('endpoint').value || 'http://localhost:8000';
    endpoint = endpoint.replace(/\/$/, '');
    try {
      await fetch(endpoint + '/add_aimodel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: modelId, name: modelName, ram: ramUsage })
      });
      await populateModels();
    } catch (e) {
      alert('Failed to add model: ' + e.message);
    }
  };
  buttonContainer.appendChild(addModelBtn);

  populateModels();

  const settings = JSON.parse(localStorage.getItem('androidext_settings') || '{}');
  if (settings.model) modelSelect.value = settings.model;
  if (settings.ttsLang) ttsLang.value = settings.ttsLang;

  settingsBtn.onclick = () => { settingsModal.style.display = 'flex'; };
  closeSettings.onclick = () => { settingsModal.style.display = 'none'; };
  if (saveSettings) {
    saveSettings.onclick = async function() {
      let endpoint = localStorage.getItem('apiEndpoint') || document.getElementById('endpoint').value || 'http://localhost:8000';
      endpoint = endpoint.replace(/\/$/, '');
      const ocrModel = localStorage.getItem('androidext_ocr_model') || 'default';
      
      try {
        const ocrResponse = await fetch(endpoint + '/set_ocr_model', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ocr_model: ocrModel })
        });
        if (!ocrResponse.ok) throw new Error('OCR model update failed');

        const aiResponse = await fetch(endpoint + '/set_aimodel', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ model: modelSelect.value })
        });
        if (!aiResponse.ok) {
          const errorData = await aiResponse.json();
          throw new Error(errorData.message || 'AI model update failed');
        }

        const verifyResponse = await fetch(endpoint + '/current_aimodel');
        const verifyData = await verifyResponse.json();
        if (verifyData.current_model !== modelSelect.value) {
          throw new Error('Model change verification failed');
        }

        localStorage.setItem('androidext_settings', JSON.stringify({
          model: modelSelect.value,
          ttsLang: ttsLang.value,
        }));

        settingsModal.style.display = 'none';
        window.postMessage({ 
          type: 'ANDROIDEXT_SETTINGS_UPDATE', 
          settings: {
            model: modelSelect.value,
            ttsLang: ttsLang.value,
          }
        }, '*');

        console.log('Settings updated successfully');
      } catch (e) {
        console.error('Error updating settings:', e);
        alert('Failed to update settings: ' + e.message);
      }
    };
  }

  modelSelect.onchange = async function() {
    const selectedOption = modelSelect.options[modelSelect.selectedIndex];
    if (!selectedOption) return;
    
    if (!confirm(`Are you sure you want to switch to this model?\n\nAI models take a lot of RAM. Make sure your system can handle:\n\n${selectedOption.textContent}`)) {
      const settings = JSON.parse(localStorage.getItem('androidext_settings') || '{}');
      modelSelect.value = settings.model || modelSelect.options[0].value;
    }
  };
});
