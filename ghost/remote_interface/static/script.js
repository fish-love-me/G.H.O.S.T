async function sendText() {
    const input = document.getElementById('textInput').value;
    const res = await fetch('/send_text', {
        method: 'POST',
        body: new URLSearchParams({ text: input }),
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    });
    const data = await res.json();
    document.getElementById('response').innerText = data.response || data.message;
}