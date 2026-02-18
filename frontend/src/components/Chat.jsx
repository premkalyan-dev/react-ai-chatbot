import { useState, useEffect, useRef } from "react";

function Chat({ messages, setMessages }) {
  const [text, setText] = useState("");
  const bottomRef = useRef(null);
  const [showActions, setShowActions] = useState(true);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const addMsg = (type, text) => {
    setMessages((prev) => [...prev, { type, text }]);
  };

  const sendChat = async () => {
    if (!text.trim()) return;

    addMsg("user", text);
    setShowActions(false);

    const q = text;
    setText("");

    try {
      const params = new URLSearchParams(window.location.search);
      const pid = params.get("pid");
      const rid = params.get("rid");
      const exp = params.get("exp");
      const sig = params.get("sig");

      const response = await fetch(
        `/chat?pid=${pid}&rid=${rid}&exp=${exp}&sig=${sig}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: q }),
        },
      );

      const data = await response.json();

      addMsg("bot", data.answer || "No response.");
    } catch (err) {
      addMsg("bot", "Server connection error.");
    }
  };

  const quickAsk = (t) => {
    setText(t);
    sendChat();
  };

  const downloadReport = () => {
    const params = new URLSearchParams(window.location.search);
    const pid = params.get("pid");
    const rid = params.get("rid");
    const exp = params.get("exp");
    const sig = params.get("sig");

    window.location.href = `/download-report?pid=${pid}&rid=${rid}&exp=${exp}&sig=${sig}`;
  };

  return (
    <div className="chat">
      <div className="chat-header">DiagnoIQ Assistant</div>

      <div className="chat-body">
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.type}`}>
            {m.text}
          </div>
        ))}
        
  <div ref={bottomRef}></div>
      </div>

      {showActions && (
        <div className="actions">
          <button onClick={() => quickAsk("Hemoglobin")}>🩸 Hemoglobin</button>
          <button onClick={() => quickAsk("How many parameters")}>
            📊 Total Parameters
          </button>
          <button onClick={() => quickAsk("How many tests")}>
            🧪 Total Tests
          </button>
          <button onClick={downloadReport}>📥 Download Report</button>
        </div>
      )}

      <div className="chat-input">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type your question..."
        />
        <button onClick={sendChat}>Send</button>
      </div>
    </div>
  );
}

export default Chat;
