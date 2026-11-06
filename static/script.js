/**
 * static/script.js — Клиентская логика чат-бота Mangystau Hub.
 * 
 * Обрабатывает отправку сообщений, индикатор «Печатает...» без перезагрузки,
 * историю диалога, политику конфиденциальности, переключение языков (RU/KZ)
 * и форматирование ссылок на WhatsApp.
 */

document.addEventListener("DOMContentLoaded", () => {
    // DOM-элементы
    const chatContainer = document.getElementById("chatContainer");
    const chatForm = document.getElementById("chatForm");
    const messageInput = document.getElementById("messageInput");
    const sendBtn = document.getElementById("sendBtn");
    const clearChatBtn = document.getElementById("clearChatBtn");
    const quickChipsContainer = document.getElementById("quickChipsContainer");
    const langButtons = document.querySelectorAll(".lang-btn");
    const headerSubtitle = document.getElementById("headerSubtitle");
    const operatorBtnText = document.getElementById("operatorBtnText");

    // Состояние приложения
    let currentLang = "ru"; // 'ru' или 'kz'
    let chatHistory = [];   // [{ user: "...", assistant: "..." }, ...]
    let isWaitingResponse = false;

    // Константы и тексты на двух языках
    const I18N = {
        ru: {
            headerSubtitle: "Региональный IT-хаб • г. Актау",
            operatorBtn: "Оператор",
            inputPlaceholder: "Напишите ваш вопрос о Mangystau Hub... (Enter для отправки)",
            typingText: "AI ассистент печатает ответ...",
            privacyTitle: "Политика конфиденциальности",
            privacyText: "Наш сайт и виртуальный AI-ассистент не собирают и не хранят ваши личные или персональные данные без вашего согласия. Общение полностью безопасно и конфиденциально.",
            welcomeText: "Здравствуйте! 👋 Я виртуальный консультант **Mangystau Hub** в городе Актау.\n\nЯ с радостью помогу вам:\n• 📅 Узнать **актуальные мероприятия** на следующей неделе и позже (интеграция с порталом Astana Hub)\n• 🏢 Рассказать о **направлениях работы**, коворкинге и образовательных курсах хаба\n• 📍 Подсказать **адрес** (г. Актау, 6 мкр., зд. 50) и **график работы**\n• 📞 Найти **контакты** и социальные сети\n• 💬 При необходимости перевести вас на **живого сотрудника** в WhatsApp!\n\nЧем я могу вам помочь?",
            chips: [
                { label: "📅 Мероприятия на следующей неделе", query: "Какие мероприятия пройдут на следующей неделе и позже?" },
                { label: "🏢 Чем занимается хаб?", query: "Расскажи подробно о Mangystau Hub, миссии и бесплатных курсах" },
                { label: "📍 Адрес и время работы", query: "Где находится хаб в Актау и в какие часы он работает?" },
                { label: "📞 Контакты и соцсети", query: "Какие контакты, телефон и соцсети у Mangystau Hub?" },
                { label: "💬 Связаться с оператором", query: "Как связаться с живым сотрудником хаба в WhatsApp?" }
            ],
            errorMessage: "⚠️ Извините, произошла ошибка соединения с сервером ИИ. Вы можете обратиться к координатору хаба напрямую:",
            clearConfirm: "Очистить историю диалога и начать заново?"
        },
        kz: {
            headerSubtitle: "Өңірлік IT-хаб • Ақтау қ.",
            operatorBtn: "Оператор",
            inputPlaceholder: "Mangystau Hub туралы сұрағыңызды жазыңыз... (Enter)",
            typingText: "AI көмекші жауап дайындауда...",
            privacyTitle: "Құпиялық саясаты",
            privacyText: "Бұл сайт пен AI-көмекші сіздің келісіміңізсіз жеке немесе дербес деректеріңізді жинамайды және сақтамайды. Байланыс толықтай қауіпсіз әрі құпия.",
            welcomeText: "Сәлеметсіз бе! 👋 Мен **Mangystau Hub** өңірлік IT-хабының виртуалды көмекшісімін.\n\nСізге келесі сұрақтар бойынша көмектесе аламын:\n• 📅 Келесі аптадағы және одан кейінгі **іс-шаралар кестесі** (Astana Hub порталынан жаңартылған тізім)\n• 🏢 Хабтың **жұмыс бағыттары**, коворкинг және тегін курстар (No-Code, Startup Academy, AI Lab)\n• 📍 **Мекенжай** (Ақтау қаласы, 6-шағын аудан, 50-ғимарат) және **жұмыс уақыты**\n• 📞 **Байланыс деректері** және әлеуметтік желілер\n• 💬 Қажет болса, сізді WhatsApp арқылы **хаб қызметкеріне** бағыттау!\n\nСізге қалай көмектесе аламын?",
            chips: [
                { label: "📅 Алдағы іс-шаралар", query: "Келесі аптада және алдағы уақытта қандай іс-шаралар болады?" },
                { label: "🏢 Хаб қызметі туралы", query: "Mangystau Hub қандай қызмет атқарады және қандай курстар бар?" },
                { label: "📍 Мекенжай және жұмыс уақыты", query: "Хаб қай жерде орналасқан және жұмыс кестесі қандай?" },
                { label: "📞 Байланыстар", query: "Mangystau Hub байланыс телефондары мен әлеуметтік желілері қандай?" },
                { label: "💬 Оператормен байланысу", query: "Хаб қызметкерімен WhatsApp арқылы қалай байланысуға болады?" }
            ],
            errorMessage: "⚠️ Кешіріңіз, байланыс қатесі орын алды. Хаб маманымен тікелей байланыса аласыз:",
            clearConfirm: "Диалог тарихын тазартып, қайта бастау керек пе?"
        }
    };

    // ───────────────────────────────────────────────────────────────────────
    // Инициализация интерфейса
    // ───────────────────────────────────────────────────────────────────────
    function init() {
        renderQuickChips();
        const initialTime = document.getElementById("initialBotTime");
        if (initialTime) {
            initialTime.textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        }
        setupEventListeners();
    }

    // Отрисовка быстрого меню подсказок (Chips)
    function renderQuickChips() {
        quickChipsContainer.innerHTML = "";
        const chips = I18N[currentLang].chips;
        chips.forEach(chip => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "chip-btn";
            btn.textContent = chip.label;
            btn.addEventListener("click", () => {
                if (isWaitingResponse) return;
                sendMessage(chip.query);
            });
            quickChipsContainer.appendChild(btn);
        });
    }

    // Сброс и отображение приветственного экрана + политики конфиденциальности
    function resetChatView() {
        chatContainer.innerHTML = "";
        chatHistory = [];

        // 1. Политика конфиденциальности (Строгое требование)
        const privacyEl = document.createElement("div");
        privacyEl.className = "privacy-banner";
        privacyEl.innerHTML = `
            <svg class="privacy-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
            <div class="privacy-content">
                <h3>🔒 ${I18N[currentLang].privacyTitle}</h3>
                <p>${I18N[currentLang].privacyText}</p>
            </div>
        `;
        chatContainer.appendChild(privacyEl);

        // 2. Первое приветственное сообщение ассистента
        appendBotMessage(I18N[currentLang].welcomeText, false);
    }

    // ───────────────────────────────────────────────────────────────────────
    // Обработчики событий
    // ───────────────────────────────────────────────────────────────────────
    function setupEventListeners() {
        // Переключение языка (RU / KZ)
        langButtons.forEach(btn => {
            btn.addEventListener("click", () => {
                const lang = btn.dataset.lang;
                if (lang === currentLang) return;

                langButtons.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                currentLang = lang;

                // Обновляем шапку и поле ввода
                headerSubtitle.textContent = I18N[currentLang].headerSubtitle;
                operatorBtnText.textContent = I18N[currentLang].operatorBtn;
                messageInput.placeholder = I18N[currentLang].inputPlaceholder;

                renderQuickChips();

                // Если в истории только первое сообщение, обновляем его
                if (chatHistory.length === 0) {
                    resetChatView();
                }
            });
        });

        // Отправка формы чата
        chatForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const text = messageInput.value.trim();
            if (text && !isWaitingResponse) {
                sendMessage(text);
            }
        });

        // Отправка по Enter (Shift+Enter для новой строки)
        messageInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                chatForm.dispatchEvent(new Event("submit"));
            }
        });

        // Авто-ресайз поля ввода
        messageInput.addEventListener("input", autoResizeInput);

        // Очистка диалога
        clearChatBtn.addEventListener("click", () => {
            if (confirm(I18N[currentLang].clearConfirm)) {
                resetChatView();
            }
        });
    }

    function autoResizeInput() {
        messageInput.style.height = "auto";
        const newHeight = Math.min(messageInput.scrollHeight, 120);
        messageInput.style.height = newHeight + "px";
    }

    // ───────────────────────────────────────────────────────────────────────
    // Отправка и получение сообщений
    // ───────────────────────────────────────────────────────────────────────
    async function sendMessage(text) {
        if (!text || isWaitingResponse) return;

        // Добавляем сообщение пользователя в интерфейс
        appendUserMessage(text);

        // Очищаем и восстанавливаем размер текстового поля
        messageInput.value = "";
        messageInput.style.height = "auto";
        messageInput.blur();

        // Показываем индикатор «Печатает...»
        showTypingIndicator();
        isWaitingResponse = true;
        sendBtn.disabled = true;

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    message: text,
                    history: chatHistory,
                    lang: currentLang
                })
            });

            const data = await response.json();
            hideTypingIndicator();

            if (data.status === "ok" && data.response) {
                appendBotMessage(data.response, true);
                chatHistory.push({
                    user: text,
                    assistant: data.response
                });
            } else {
                showErrorMessage(data.response || I18N[currentLang].errorMessage);
            }
        } catch (err) {
            console.error("Chat error:", err);
            hideTypingIndicator();
            showErrorMessage();
        } finally {
            isWaitingResponse = false;
            sendBtn.disabled = false;
            messageInput.focus();
        }
    }

    // ───────────────────────────────────────────────────────────────────────
    // Отрисовка элементов сообщений
    // ───────────────────────────────────────────────────────────────────────
    function appendUserMessage(text) {
        const row = document.createElement("div");
        row.className = "message-row user";

        const now = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

        row.innerHTML = `
            <div class="msg-avatar">Вы</div>
            <div class="msg-body">
                <div class="msg-bubble">${escapeHtml(text).replace(/\n/g, "<br>")}</div>
                <span class="msg-time">${now}</span>
            </div>
        `;

        chatContainer.appendChild(row);
        scrollToBottom();
    }

    function appendBotMessage(text, animate = true) {
        const row = document.createElement("div");
        row.className = "message-row bot";

        const now = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        const formattedHtml = formatMarkdown(text);

        row.innerHTML = `
            <div class="msg-avatar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2L2 7L12 12L22 7L12 2Z"/>
                    <path d="M2 17L12 22L22 17"/>
                    <path d="M2 12L12 17L22 12"/>
                </svg>
            </div>
            <div class="msg-body">
                <div class="msg-bubble">${formattedHtml}</div>
                <span class="msg-time">${now}</span>
            </div>
        `;

        chatContainer.appendChild(row);
        scrollToBottom();
    }

    function showErrorMessage(customHtml = null) {
        const errorContent = customHtml || `
            ${I18N[currentLang].errorMessage}<br><br>
            <a href="https://wa.me/77789807454" target="_blank" rel="noopener noreferrer" class="whatsapp-action-card">
                <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91C2.13 13.66 2.59 15.36 3.45 16.86L2.05 22L7.3 20.62C8.75 21.41 10.38 21.83 12.04 21.83C17.5 21.83 21.95 17.38 21.95 11.92C21.95 9.27 20.92 6.78 19.05 4.91C17.18 3.03 14.69 2 12.04 2Z"/>
                </svg>
                Связаться с оператором в WhatsApp
            </a>
        `;
        appendBotMessage(errorContent);
    }

    // ───────────────────────────────────────────────────────────────────────
    // Индикатор набора текста «Печатает...»
    // ───────────────────────────────────────────────────────────────────────
    function showTypingIndicator() {
        const existing = document.getElementById("typingIndicator");
        if (existing) return;

        const row = document.createElement("div");
        row.id = "typingIndicator";
        row.className = "typing-row";
        row.innerHTML = `
            <div class="msg-avatar bot">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2L2 7L12 12L22 7L12 2Z"/>
                    <path d="M2 17L12 22L22 17"/>
                    <path d="M2 12L12 17L22 12"/>
                </svg>
            </div>
            <div class="typing-bubble">
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
                <span class="typing-text">${I18N[currentLang].typingText}</span>
            </div>
        `;
        chatContainer.appendChild(row);
        scrollToBottom();
    }

    function hideTypingIndicator() {
        const el = document.getElementById("typingIndicator");
        if (el) el.remove();
    }

    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // ───────────────────────────────────────────────────────────────────────
    // Форматирование Markdown и спец-ссылок (WhatsApp, ссылки, списки)
    // ───────────────────────────────────────────────────────────────────────
    function formatMarkdown(text) {
        if (!text) return "";

        // Если это уже HTML
        if (text.includes("<div") || text.includes("<p") || text.includes("<a href=")) {
            return text;
        }

        let html = escapeHtml(text);

        // 1. Превращаем ссылки WhatsApp в стилизованную карточку-кнопку
        const waCardTemplate = (linkText, href) => `
            <a href="${href}" target="_blank" rel="noopener noreferrer" class="whatsapp-action-card">
                <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91C2.13 13.66 2.59 15.36 3.45 16.86L2.05 22L7.3 20.62C8.75 21.41 10.38 21.83 12.04 21.83C17.5 21.83 21.95 17.38 21.95 11.92C21.95 9.27 20.92 6.78 19.05 4.91C17.18 3.03 14.69 2 12.04 2Z"/>
                </svg>
                <span>${linkText}</span>
            </a>
        `;

        // Замена Markdown ссылок [текст](url)
        html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g, (match, title, url) => {
            if (url.includes("wa.me") || url.includes("whatsapp.com")) {
                return waCardTemplate(title, url);
            }
            return `<a href="${url}" target="_blank" rel="noopener noreferrer">${title}</a>`;
        });

        // Замена прямых URL
        html = html.replace(/(?<!href=")(https?:\/\/[^\s<]+)/g, (match, url) => {
            if (url.includes("wa.me") || url.includes("whatsapp.com")) {
                return waCardTemplate("Связаться в WhatsApp", url);
            }
            return `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
        });

        // Полужирный шрифт **text**
        html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");

        // Курсив *text*
        html = html.replace(/\*([^*]+)\*/g, "<em>$1</em>");

        // Списки (маркеры - или •)
        const lines = html.split("\n");
        let inList = false;
        let formattedLines = [];

        for (let line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith("• ") || trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
                if (!inList) {
                    formattedLines.push("<ul>");
                    inList = true;
                }
                formattedLines.push(`<li>${trimmed.substring(2)}</li>`);
            } else {
                if (inList) {
                    formattedLines.push("</ul>");
                    inList = false;
                }
                if (trimmed.length > 0) {
                    formattedLines.push(`<p>${line}</p>`);
                }
            }
        }
        if (inList) formattedLines.push("</ul>");

        return formattedLines.join("");
    }

    function escapeHtml(str) {
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Запуск
    init();
});
