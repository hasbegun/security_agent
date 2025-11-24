import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './ChatInterface.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const API_URL = `${API_BASE_URL}/api/chat`;

// const messages
const abort_msg = 'Okay, request cancelled.';
const backend_error_msg = 'Sorry, I encountered an error. Please try again.';

function ChatInterface() {
  const [messages, setMessages] = useState([]); // store current session msg
  const [inputValue, setInputValue] = useState(''); // text input box
  const [isLoading, setIsLoading] = useState(false); // llm resp
  const messagesEndRef = useRef(null);
  const abortControllerRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // this makes the to scroll
  useEffect(scrollToBottom, [messages]);

  const handleInputChange = (e) => {
    setInputValue(e.target.value);
  };

  // handle abort
  const handleAbort = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      console.log("Request aborted by user.");
      setIsLoading(false);
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: 'ai', text: abort_msg },
      ]);
    }
  };

  const handleSendMessage = async () => {
    const userMessage = inputValue.trim();
    if (!userMessage) return;

    setMessages((prevMessages) => [
      ...prevMessages,
      { sender: 'user', text: userMessage },
    ]);
    setInputValue('');
    setIsLoading(true);

    // register abort ctrl
    abortControllerRef.current = new AbortController();

    try {
      const response = await axios.post(
        API_URL, {
          query: userMessage,
          user_id: 'react_user', // Replace with actual user ID later if needed
        },
        {
          signal: abortControllerRef.current.signal,
        }
      );

      // llm response to the chat
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: 'ai', text: response.data.response },
      ]);
    } catch (error) {
      if (axios.isCancel(error)) {
        console.log('Request canceled:', error.message);
      } else {
      console.error('Error fetching response:', error);
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: 'ai', text: backend_error_msg },
      ]);
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleButtonClick = () => {
    if (isLoading) {
      handleAbort();
    } else {
      handleSendMessage();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="chat-container">
      <h2>Security Assistant 🛡️</h2>
      <div className="messages-area">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            <p>{msg.text}</p>
          </div>
        ))}
        {/* empty div to target for scrolling */}
        <div ref={messagesEndRef} />
      </div>
      {isLoading && <div className="loading-indicator">Assistant is thinking...</div>}
      <div className="input-area">
        <textarea
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyPress}
          placeholder="How can I assist you with security today?"
          rows="3"
          disabled={isLoading} // Disable input while loading
        />
        <button
          onClick={handleButtonClick}
          disabled={!isLoading && !inputValue.trim()}
          className={`send-button ${isLoading ? 'loading' : ''}`}
        >
          {isLoading ? (
            <>
              <span className="spinner"></span> {/* positioned */}
              <span className="stop-icon">■</span> {/* the base */}
            </>
          ) : (
            'Send'
          )}
        </button>
      </div>
    </div>
  );
}

export default ChatInterface;