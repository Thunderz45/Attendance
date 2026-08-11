document.addEventListener('DOMContentLoaded', () => {
  const video = document.getElementById('webcam-preview');
  const canvas = document.getElementById('webcam-canvas');
  const startBtn = document.getElementById('start-cam-btn');
  const captureBtn = document.getElementById('capture-btn');
  const statusAlert = document.getElementById('reg-status-alert');
  const progressBar = document.getElementById('reg-progress');
  const studentId = document.getElementById('student-id-holder')?.value;

  if (!video || !startBtn) return;

  let stream = null;
  let capturedFrames = [];
  const requiredSamples = 5;

  startBtn.addEventListener('click', async () => {
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' }
      });
      video.srcObject = stream;
      startBtn.disabled = true;
      startBtn.classList.add('btn-secondary');
      captureBtn.disabled = false;
      showStatus('Camera ready! Position face inside guide frame and click "Capture Sample".', 'info');
    } catch (err) {
      showStatus('Camera permission denied or camera unavailable: ' + err.message, 'danger');
    }
  });

  captureBtn.addEventListener('click', () => {
    if (!stream || capturedFrames.length >= requiredSamples) return;

    const ctx = canvas.getContext('2d');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const base64Img = canvas.toDataURL('image/jpeg', 0.9);
    capturedFrames.push(base64Img);

    const progressPct = (capturedFrames.length / requiredSamples) * 100;
    if (progressBar) progressBar.style.width = `${progressPct}%`;

    showStatus(`Captured Sample ${capturedFrames.length} of ${requiredSamples}.`, 'info');

    if (capturedFrames.length >= requiredSamples) {
      captureBtn.disabled = true;
      submitFaceData();
    }
  });

  async function submitFaceData() {
    showStatus('Processing face embeddings and validating uniqueness...', 'warning');

    try {
      const response = await fetch(`/admin/students/${studentId}/save-face`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ images: capturedFrames })
      });

      const resData = await response.json();

      if (response.ok && resData.success) {
        showStatus(resData.message, 'success');
        setTimeout(() => {
          window.location.href = resData.redirect_url || '/admin/students';
        }, 1500);
      } else {
        showStatus(resData.message || 'Face registration failed.', 'danger');
        capturedFrames = [];
        if (progressBar) progressBar.style.width = '0%';
        captureBtn.disabled = false;
      }
    } catch (err) {
      showStatus('Network error while saving face data: ' + err.message, 'danger');
      capturedFrames = [];
      if (progressBar) progressBar.style.width = '0%';
      captureBtn.disabled = false;
    }
  }

  function showStatus(msg, type) {
    if (!statusAlert) return;
    statusAlert.className = `alert alert-${type}`;
    statusAlert.innerText = msg;
    statusAlert.style.display = 'block';
  }
});
