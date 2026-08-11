document.addEventListener('DOMContentLoaded', () => {
  const video = document.getElementById('kiosk-video');
  const canvas = document.getElementById('kiosk-canvas');
  const statusBadge = document.getElementById('status-badge');
  const scanLine = document.getElementById('scan-line');
  const clockEl = document.getElementById('kiosk-clock-time');
  const dateEl = document.getElementById('kiosk-clock-date');

  // Student Info Card fields
  const infoName = document.getElementById('info-name');
  const infoRoll = document.getElementById('info-roll');
  const infoCourse = document.getElementById('info-course');
  const infoStatus = document.getElementById('info-status');
  const infoTime = document.getElementById('info-time');

  let stream = null;
  let isProcessing = false;
  let pauseUntil = 0;
  const recognitionInterval = 700; // ms

  // Live Clock update
  function updateClock() {
    const now = new Date();
    if (clockEl) clockEl.innerText = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    if (dateEl) dateEl.innerText = now.toLocaleDateString([], { weekday: 'long', year: 'numeric', month: 'short', day: 'numeric' });
  }
  setInterval(updateClock, 1000);
  updateClock();

  // Initialize WebRTC Webcam stream
  async function initCamera() {
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' }
      });
      video.srcObject = stream;
      video.onloadedmetadata = () => {
        video.play();
        setStatus('Ready for Attendance', 'ready');
        startFrameSampling();
      };
    } catch (err) {
      console.error("Camera error:", err);
      setStatus('Camera Permission Required / Unavailable', 'danger');
    }
  }

  function startFrameSampling() {
    setInterval(async () => {
      const now = Date.now();
      if (now < pauseUntil || isProcessing || !stream) return;

      captureAndRecognize();
    }, recognitionInterval);
  }

  async function captureAndRecognize() {
    isProcessing = true;
    const ctx = canvas.getContext('2d');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const base64Img = canvas.toDataURL('image/jpeg', 0.85);

    try {
      const res = await fetch('/api/attendance/recognize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: base64Img })
      });

      const data = await res.json();
      handleRecognitionResult(data);
    } catch (err) {
      console.error("Recognition API error:", err);
    } finally {
      isProcessing = false;
    }
  }

  function handleRecognitionResult(data) {
    if (scanLine) scanLine.style.display = 'none';

    switch (data.status) {
      case 'NO_FACE':
        setStatus('Looking for face...', 'ready');
        resetStudentCard();
        break;

      case 'MULTIPLE_FACES':
        setStatus('Multiple Faces Detected', 'warning');
        resetStudentCard();
        break;

      case 'UNRECOGNIZED':
        setStatus('Face Not Recognized', 'danger');
        resetStudentCard();
        break;

      case 'SUCCESS':
        if (scanLine) scanLine.style.display = 'block';
        setStatus('Attendance Marked Successfully', 'success');
        updateStudentCard(data.student, 'PRESENT', data.attendance_time);
        playBeep(880, 0.15); // High beep success
        pauseUntil = Date.now() + 4000; // Pause 4s
        break;

      case 'ALREADY_MARKED':
        setStatus('Attendance Already Marked', 'warning');
        updateStudentCard(data.student, 'ALREADY PRESENT', data.attendance_time);
        playBeep(440, 0.25); // Medium double beep warning
        pauseUntil = Date.now() + 4000; // Pause 4s
        break;

      default:
        setStatus('Ready for Attendance', 'ready');
        break;
    }
  }

  function setStatus(text, stateClass) {
    if (!statusBadge) return;
    statusBadge.innerText = text;
    statusBadge.className = `status-badge status-${stateClass}`;
  }

  function updateStudentCard(student, statusText, timeText) {
    if (infoName) infoName.innerText = student.name || '--';
    if (infoRoll) infoRoll.innerText = `${student.roll_number} (${student.student_id})`;
    if (infoCourse) infoCourse.innerText = `${student.course} - ${student.division}`;
    if (infoStatus) infoStatus.innerText = statusText;
    if (infoTime) infoTime.innerText = timeText || '--';
  }

  function resetStudentCard() {
    if (infoName) infoName.innerText = '--';
    if (infoRoll) infoRoll.innerText = '--';
    if (infoCourse) infoCourse.innerText = '--';
    if (infoStatus) infoStatus.innerText = '--';
    if (infoTime) infoTime.innerText = '--';
  }

  function playBeep(freq, duration) {
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + duration);
    } catch (e) {
      // Audio context fallback if blocked by browser policy
    }
  }

  initCamera();
});
