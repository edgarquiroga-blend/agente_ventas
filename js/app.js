const API_URL = 'http://localhost:5000/api';
let isProcessing = false;

// Auto-resize textarea
function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

// Handle Enter key
function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

// Send suggestion
function sendSuggestion(btn) {
  const text = btn.textContent.trim();
  document.getElementById('userInput').value = text;
  sendMessage();
}

// Send message
async function sendMessage() {
  if (isProcessing) return;

  const input = document.getElementById('userInput');
  const text = input.value.trim();
  if (!text) return;

  // Hide welcome
  const welcome = document.getElementById('welcome');
  if (welcome) welcome.style.display = 'none';

  isProcessing = true;
  document.getElementById('sendBtn').disabled = true;
  input.value = '';
  autoResize(input);

  // Add user message
  addMessage('user', text);

  // Add typing indicator
  const typingId = addTyping();

  try {
    // Send to Python backend
    const response = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pregunta: text })
    });

    const data = await response.json();
    removeTyping(typingId);

    if (data.error) {
      addMessage('agent', `❌ Error: ${data.error}`, 'error');
    } else {
      // Add response
      addMessage('agent', data.respuesta);
      
      // Handle files (images, csv, excel)
      if (data.archivos && data.archivos.length > 0) {
        data.archivos.forEach(archivo => {
          if (archivo.tipo === 'imagen') {
            showImage(archivo.nombre);
          } else {
            showDownloadButton(archivo.nombre, archivo.tipo);
          }
        });
      }
    }
  } catch (error) {
    removeTyping(typingId);
    addMessage('agent', `❌ Error de conexión: ${error.message}`, 'error');
  }

  isProcessing = false;
  document.getElementById('sendBtn').disabled = false;
  input.focus();
}

// Add message to chat
function addMessage(role, text, type = null) {
  const messages = document.getElementById('messages');

  const msg = document.createElement('div');
  msg.className = `message ${role}`;

  const avatar = document.createElement('div');
  avatar.className = `avatar ${role === 'user' ? 'user-av' : 'agent-av'}`;
  avatar.textContent = role === 'user' ? '👤' : '🤖';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  
  if (type === 'error') {
    bubble.style.borderColor = '#ef4444';
  }

  bubble.innerHTML = text.replace(/\n/g, '<br>');

  msg.appendChild(avatar);
  msg.appendChild(bubble);
  messages.appendChild(msg);
  messages.scrollTop = messages.scrollHeight;
}

// Typing indicator
function addTyping() {
  const messages = document.getElementById('messages');
  const id = 'typing-' + Date.now();

  const msg = document.createElement('div');
  msg.className = 'message agent';
  msg.id = id;

  const avatar = document.createElement('div');
  avatar.className = 'avatar agent-av';
  avatar.textContent = '🤖';

  const bubble = document.createElement('div');
  bubble.className = 'bubble typing';
  bubble.innerHTML = '<span></span><span></span><span></span>';

  msg.appendChild(avatar);
  msg.appendChild(bubble);
  messages.appendChild(msg);
  messages.scrollTop = messages.scrollHeight;
  return id;
}

function removeTyping(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

// Show image in chat
function showImage(filename) {
  const messages = document.getElementById('messages');
  const div = document.createElement('div');
  div.className = 'message agent';
  div.innerHTML = `
    <div class="avatar agent-av">🤖</div>
    <div class="bubble">
      <div class="result-tag chart">📊 Gráfico generado</div>
      <div class="image-container">
        <img src="${API_URL}/archivo/${filename}" alt="Gráfico">
        <a href="${API_URL}/archivo/${filename}" download class="download-img-btn">
          📥 Descargar
        </a>
      </div>
    </div>
  `;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

// Show download button
function showDownloadButton(filename, tipo) {
  const emoji = tipo === 'csv' ? '📄' : '📊';
  const messages = document.getElementById('messages');
  const div = document.createElement('div');
  div.className = 'message agent';
  div.innerHTML = `
    <div class="avatar agent-av">🤖</div>
    <div class="bubble">
      <div class="result-tag file">📥 Archivo exportado</div>
      <a href="${API_URL}/archivo/${filename}" download class="download-btn">
        ${emoji} Descargar ${filename}
      </a>
    </div>
  `;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

// Load stats on page load
async function loadStats() {
  try {
    const response = await fetch(`${API_URL}/estadisticas`);
    const data = await response.json();
    console.log('Estadísticas:', data);
  } catch (error) {
    console.error('Error cargando estadísticas:', error);
  }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  loadStats();
});