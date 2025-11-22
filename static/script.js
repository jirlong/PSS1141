// Tab Switching
document.querySelectorAll('.tab-btn').forEach(button => {
    button.addEventListener('click', () => {
        const tabName = button.getAttribute('data-tab');
        
        // Remove active class from all tabs and buttons
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        
        // Add active class to clicked button and corresponding content
        button.classList.add('active');
        document.getElementById(`${tabName}-tab`).classList.add('active');
    });
});

// Helper function to show loading state
function setLoading(btnElement, isLoading) {
    if (isLoading) {
        btnElement.classList.add('loading');
        btnElement.disabled = true;
    } else {
        btnElement.classList.remove('loading');
        btnElement.disabled = false;
    }
}

// Helper function to display error
function showError(containerId, message) {
    const container = document.getElementById(containerId);
    container.style.display = 'block';
    container.innerHTML = `<div class="error-message">❌ 錯誤：${message}</div>`;
}

// 1. Ask Function
async function handleAsk() {
    const input = document.getElementById('ask-input').value.trim();
    const model = document.getElementById('ask-model').value;
    const resultDiv = document.getElementById('ask-result');
    const outputDiv = document.getElementById('ask-output');
    const btn = event.target;
    
    if (!input) {
        alert('請輸入您的問題！');
        return;
    }
    
    setLoading(btn, true);
    resultDiv.style.display = 'none';
    
    try {
        const response = await fetch('/api/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                input_text: input,
                model: model
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            outputDiv.textContent = data.output;
            resultDiv.style.display = 'block';
        } else {
            showError('ask-result', data.error || '請求失敗');
        }
    } catch (error) {
        showError('ask-result', '網路錯誤：' + error.message);
    } finally {
        setLoading(btn, false);
    }
}

// 2. Translate Function
async function handleTranslate() {
    const text = document.getElementById('translate-input').value.trim();
    const model = document.getElementById('translate-model').value;
    const resultDiv = document.getElementById('translate-result');
    const originalDiv = document.getElementById('translate-original');
    const outputDiv = document.getElementById('translate-output');
    const btn = event.target;
    
    if (!text) {
        alert('請輸入要翻譯的文字！');
        return;
    }
    
    setLoading(btn, true);
    resultDiv.style.display = 'none';
    
    try {
        const response = await fetch('/api/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: text,
                model: model
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            originalDiv.textContent = data.original;
            outputDiv.textContent = data.translated;
            resultDiv.style.display = 'block';
        } else {
            showError('translate-result', data.error || '翻譯失敗');
        }
    } catch (error) {
        showError('translate-result', '網路錯誤：' + error.message);
    } finally {
        setLoading(btn, false);
    }
}

// 3. News Analysis Function
async function handleNewsAnalysis() {
    const newsText = document.getElementById('news-input').value.trim();
    const model = document.getElementById('news-model').value;
    const resultDiv = document.getElementById('news-result');
    const btn = event.target;
    
    if (!newsText) {
        alert('請輸入新聞內容！');
        return;
    }
    
    setLoading(btn, true);
    resultDiv.style.display = 'none';
    
    try {
        const response = await fetch('/api/news-summary', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                news_text: newsText,
                model: model
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const summary = data.summary;
            document.getElementById('news-who').textContent = summary.who;
            document.getElementById('news-what').textContent = summary.what;
            document.getElementById('news-when').textContent = summary.when;
            document.getElementById('news-where').textContent = summary.where;
            document.getElementById('news-why').textContent = summary.why;
            document.getElementById('news-how').textContent = summary.how;
            resultDiv.style.display = 'block';
        } else {
            showError('news-result', data.error || '分析失敗');
        }
    } catch (error) {
        showError('news-result', '網路錯誤：' + error.message);
    } finally {
        setLoading(btn, false);
    }
}

// 4. Story Creation Function
async function handleStoryCreation() {
    const topic = document.getElementById('story-topic').value.trim();
    const wordCount = parseInt(document.getElementById('story-words').value);
    const style = document.getElementById('story-style').value;
    const model = document.getElementById('story-model').value;
    const resultDiv = document.getElementById('story-result');
    const outputDiv = document.getElementById('story-output');
    const btn = event.target;
    
    if (!topic) {
        alert('請輸入故事主題！');
        return;
    }
    
    setLoading(btn, true);
    resultDiv.style.display = 'none';
    
    try {
        const response = await fetch('/api/create-story', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                topic: topic,
                word_count: wordCount,
                instructions: style
                ,model: model
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            outputDiv.textContent = data.story;
            resultDiv.style.display = 'block';
        } else {
            showError('story-result', data.error || '創作失敗');
        }
    } catch (error) {
        showError('story-result', '網路錯誤：' + error.message);
    } finally {
        setLoading(btn, false);
    }
}

// 5. Dispatch Function
async function handleDispatch() {
    const userRequest = document.getElementById('dispatch-input').value.trim();
    const model = document.getElementById('dispatch-model').value;
    const resultDiv = document.getElementById('dispatch-result');
    const typeSpan = document.getElementById('dispatch-type');
    const outputDiv = document.getElementById('dispatch-output');
    const btn = event.target;
    
    if (!userRequest) {
        alert('請輸入您的需求！');
        return;
    }
    
    setLoading(btn, true);
    resultDiv.style.display = 'none';
    
    try {
        const response = await fetch('/api/dispatch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_request: userRequest,
                model: model
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Display task type
            const taskTypeNames = {
                'translator': '🌐 翻譯服務',
                'news_summarizer': '📰 新聞分析',
                'story_creator': '📖 故事創作',
                'general_question': '💬 一般問答'
            };
            typeSpan.textContent = taskTypeNames[data.task_type] || data.task_type;
            
            // Display result based on task type
            let resultHTML = '';
            if (data.task_type === 'translator') {
                resultHTML = `
                    <div class="translation-section">
                        <strong>原文：</strong>
                        <p>${data.result.original}</p>
                    </div>
                    <div class="translation-section" style="margin-top: 15px;">
                        <strong>譯文：</strong>
                        <p>${data.result.translated}</p>
                    </div>
                `;
            } else if (data.task_type === 'news_summarizer') {
                const summary = data.result;
                resultHTML = `
                    <div class="news-analysis">
                        <div class="analysis-item"><strong>👤 Who：</strong>${summary.who}</div>
                        <div class="analysis-item"><strong>📋 What：</strong>${summary.what}</div>
                        <div class="analysis-item"><strong>⏰ When：</strong>${summary.when}</div>
                        <div class="analysis-item"><strong>📍 Where：</strong>${summary.where}</div>
                        <div class="analysis-item"><strong>❓ Why：</strong>${summary.why}</div>
                        <div class="analysis-item"><strong>⚙️ How：</strong>${summary.how}</div>
                    </div>
                `;
            } else if (data.task_type === 'story_creator') {
                resultHTML = `
                    <div class="story-text">
                        <strong>主題：${data.result.topic}</strong>
                        <p style="margin-top: 15px;">${data.result.story}</p>
                    </div>
                `;
            } else {
                resultHTML = `<p style="white-space: pre-wrap;">${data.result}</p>`;
            }
            
            outputDiv.innerHTML = resultHTML;
            resultDiv.style.display = 'block';
        } else {
            showError('dispatch-result', data.error || '處理失敗');
        }
    } catch (error) {
        showError('dispatch-result', '網路錯誤：' + error.message);
    } finally {
        setLoading(btn, false);
    }
}

// Set example for dispatch
function setDispatchExample(text) {
    document.getElementById('dispatch-input').value = text;
}

// Smooth scroll for navigation
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const target = link.getAttribute('href');
        if (target === '#services') {
            window.scrollTo({
                top: document.querySelector('.main-content').offsetTop - 80,
                behavior: 'smooth'
            });
        } else {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        }
    });
});

// Populate model dropdowns from server
document.addEventListener('DOMContentLoaded', async () => {
    const selectIds = ['ask-model', 'translate-model', 'news-model', 'story-model', 'dispatch-model'];
    try {
        const res = await fetch('/api/models');
        const data = await res.json();
        if (data && data.success && Array.isArray(data.models)) {
            const models = data.models;
            selectIds.forEach(id => {
                const sel = document.getElementById(id);
                if (!sel) return;
                // clear existing options
                sel.innerHTML = '';
                models.forEach(m => {
                    const opt = document.createElement('option');
                    opt.value = m;
                    opt.textContent = m;
                    sel.appendChild(opt);
                });
            });
        }
    } catch (e) {
        console.warn('Could not load model list from server:', e);
    }
});

// Fetch service info (which backend is active) and update badge
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const res = await fetch('/api/service-info');
        const data = await res.json();
        if (data && data.success && data.service_label) {
            const badge = document.getElementById('service-badge');
            if (badge) {
                badge.textContent = `Backend: ${data.service_label}`;
                // simple styling per service
                if (data.service === 'ollama') {
                    badge.style.background = '#e8f5e9';
                    badge.style.color = '#1b5e20';
                } else if (data.service === 'openai') {
                    badge.style.background = '#e3f2fd';
                    badge.style.color = '#0d47a1';
                }
            }
        }
    } catch (e) {
        // ignore if endpoint not available
        console.warn('Could not fetch service info:', e);
    }
});
