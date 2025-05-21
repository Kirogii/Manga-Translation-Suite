function createOverlay(box, text, imageRect, naturalSize, displaySize) {
  const [x1, y1, x2, y2] = box;

  const scaleX = displaySize.width / naturalSize.width;
  const scaleY = displaySize.height / naturalSize.height;

  const left = imageRect.left + x1 * scaleX;
  const top = imageRect.top + y1 * scaleY;
  const width = (x2 - x1) * scaleX;
  const height = (y2 - y1) * scaleY;

  const div = document.createElement('div');
  div.textContent = text;
  div.style.position = 'absolute';
  div.style.left = `${left}px`;
  div.style.top = `${top}px`;
  div.style.width = `${width}px`;
  div.style.height = `${height}px`;
  div.style.backgroundColor = '#ffffff';
  div.style.color = '#000000';
  div.style.opacity = '1';
  div.style.mixBlendMode = 'normal';
  div.style.backdropFilter = 'none';
  div.style.filter = 'none';
  div.style.fontFamily = "'Noto Sans JP', sans-serif";
  div.style.fontSize = '14px';

  div.style.display = 'flex';
  div.style.alignItems = 'center';
  div.style.justifyContent = 'center';

  div.style.padding = '2px';
  div.style.border = '0px solid black';
  div.style.zIndex = 9999;
  div.style.pointerEvents = 'none';

  document.body.appendChild(div);
}

async function processImage(img, currentIndex, totalCount, progressTextElem) {
  const imageUrl = img.src;
  const rect = img.getBoundingClientRect();

  try {
    const res = await fetch('http://localhost:8000/predict_url', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_url: imageUrl })
    });

    const data = await res.json();
    if (data.status !== 'ok') return;

    const naturalSize = { width: img.naturalWidth, height: img.naturalHeight };
    const displaySize = { width: rect.width, height: rect.height };

    data.regions.forEach(region => {
      createOverlay(region.box, region.translation, rect, naturalSize, displaySize);
    });

    // Update progress text like "3 / 12"
    progressTextElem.textContent = `${currentIndex + 1} / ${totalCount}`;
    progressTextElem.style.color = 'black';

  } catch (e) {
    console.error('Error sending image URL to backend:', e);
  }
}

(async () => {
  // Scroll to top before starting OCR
  window.scrollTo({ top: 0, behavior: 'smooth' });

  const images = Array.from(document.images).filter(img =>
    img.naturalWidth > 300 && img.naturalHeight > 300 && img.src.startsWith('http')
  );

  if (images.length === 0) return;

  // Create simple progress display
  const progressTextElem = document.createElement('div');
  progressTextElem.style.position = 'fixed';
  progressTextElem.style.top = '10px';
  progressTextElem.style.right = '10px';
  progressTextElem.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
  progressTextElem.style.color = 'black';
  progressTextElem.style.fontWeight = 'bold';
  progressTextElem.style.fontSize = '14px';
  progressTextElem.style.padding = '6px 10px';
  progressTextElem.style.border = '1px solid black';
  progressTextElem.style.borderRadius = '6px';
  progressTextElem.style.zIndex = 10000;
  document.body.appendChild(progressTextElem);

  for (let i = 0; i < images.length; i++) {
    await processImage(images[i], i, images.length, progressTextElem);
  }

  // Remove progress text after done
  progressTextElem.remove();
})();
 