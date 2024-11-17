import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';
import './App.css';

const API_URL = 'https://efsqhvoi8ov26zg9.preview.dev.igent.ai';

function App() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [debugInfo, setDebugInfo] = useState('');

  useEffect(() => {
    setDebugInfo(prevInfo => prevInfo + '\nApp component mounted');
    
    // Test API connection
    axios.get(API_URL)
      .then(response => {
        setDebugInfo(prevInfo => prevInfo + `\nAPI connection successful: ${response.status}`);
      })
      .catch(error => {
        setDebugInfo(prevInfo => prevInfo + `\nAPI connection failed: ${error.message}`);
      });
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { text: input, sender: 'user' };
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setInput('');
    setIsLoading(true);
    setDebugInfo(prevInfo => prevInfo + '\nSending request to API...');

    try {
      console.log('Before API call'); // Debug statement
      setDebugInfo(prevInfo => prevInfo + '\nBefore API call');
      
      const response = await axios.post(`${API_URL}/api/chat`, { message: input });
      
      console.log('After API call', response); // Debug statement
      setDebugInfo(prevInfo => prevInfo + `\nAfter API call. Status: ${response.status}`);

      const botMessage = { text: response.data.message, sender: 'bot' };
      setMessages(prevMessages => [...prevMessages, botMessage]);

      if (response.data.plot) {
        try {
          const plotData = JSON.parse(response.data.plot);
          const plotMessage = { plot: plotData, sender: 'bot' };
          setMessages(prevMessages => [...prevMessages, plotMessage]);
          setDebugInfo(prevInfo => prevInfo + '\nPlot data received and parsed successfully');
        } catch (error) {
          console.error('Error parsing plot data:', error);
          setDebugInfo(prevInfo => prevInfo + `\nError parsing plot data: ${error.message}`);
        }
      }
    } catch (error) {
      console.error('Error:', error);
      setDebugInfo(prevInfo => prevInfo + `\nError: ${error.message}`);
      const errorMessage = { text: `An error occurred: ${error.message}. Please try again or rephrase your request.`, sender: 'bot' };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Interactive Plot Generator</h1>
      </header>
      <div className="chat-container">
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.sender}`}>
            {message.text && <p>{message.text}</p>}
            {message.plot && (
              <Plot
                data={message.plot.data}
                layout={message.plot.layout}
                style={{ width: '100%', height: '400px' }}
                config={{ responsive: true }}
              />
            )}
          </div>
        ))}
        {isLoading && <div className="message bot loading">Generating response...</div>}
      </div>
      <form onSubmit={handleSubmit} className="input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask for a plot or ask a question..."
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading}>Send</button>
      </form>
      <div className="debug-info">
        <h2>Debug Information:</h2>
        <pre>{debugInfo}</pre>
      </div>
    </div>
  );
}

export default App;