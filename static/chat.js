var MAX_LENGTH = 1000;
var messages = document.getElementById("messages");
var form = document.getElementById("chat-form");
var input = document.getElementById("message");
var sendButton = form.querySelector("button");

// Добавляет сообщение в чат. Текст выводится через textContent, а не innerHTML.
function addMessage(text, className, rule) {
    var bubble = document.createElement("div");
    bubble.className = "msg " + className;
    bubble.textContent = text;
    if (rule) {
        var note = document.createElement("span");
        note.className = "rule";
        note.textContent = rule;
        bubble.appendChild(note);
    }
    messages.appendChild(bubble);
    messages.scrollTop = messages.scrollHeight;
}

// Из шагов распознавания показываем строку со сработавшим правилом.
function findRule(steps) {
    for (var i = 0; i < steps.length; i++) {
        if (steps[i].startsWith("Правило:")) {
            return steps[i];
        }
    }
    return "";
}

async function send(text) {
    text = text.trim();
    if (!text) {
        return;
    }
    if (text.length > MAX_LENGTH) {
        addMessage("Сообщение длиннее " + MAX_LENGTH + " символов.", "error");
        return;
    }

    addMessage(text, "user");
    sendButton.disabled = true;
    try {
        var response = await fetch("/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({message: text})
        });
        var data = await response.json();
        if (response.ok) {
            addMessage(data.answer, "bot", findRule(data.steps));
        } else if (typeof data.detail === "string") {
            addMessage(data.detail, "error");
        } else {
            addMessage("Сервер не принял сообщение (код " + response.status + ").", "error");
        }
    } catch (error) {
        addMessage("Не удалось связаться с сервером. Попробуйте ещё раз.", "error");
    }
    sendButton.disabled = false;
}

form.addEventListener("submit", function (event) {
    event.preventDefault();
    send(input.value);
    input.value = "";
});

var askButtons = document.querySelectorAll("[data-ask]");
for (var i = 0; i < askButtons.length; i++) {
    askButtons[i].addEventListener("click", function (event) {
        send(event.target.dataset.ask);
    });
}
