// App.js
import React, { useState, useEffect } from "react";
import axios from "axios";
import Plot from "react-plotly.js";
import { IoSend } from "react-icons/io5";
import "./App.css";

const API_URL = "http://127.0.0.1:8080";

function App() {
    const [input, setInput] = useState("");
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [debugInfo, setDebugInfo] = useState("");

    useEffect(() => {
        setDebugInfo((prevInfo) => prevInfo + "\nApp component mounted");
        axios
            .get(API_URL)
            .then((response) => {
                setDebugInfo(
                    (prevInfo) =>
                        prevInfo +
                        `\nAPI connection successful: ${response.status}`,
                );
            })
            .catch((error) => {
                setDebugInfo(
                    (prevInfo) =>
                        prevInfo + `\nAPI connection failed: ${error.message}`,
                );
            });
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMessage = {
            text: input,
            sender: "user",
            timestamp: new Date().toLocaleTimeString(),
        };
        setMessages((prevMessages) => [...prevMessages, userMessage]);
        setInput("");
        setIsLoading(true);

        try {
            const response = await axios.post(`${API_URL}/api/chat`, {
                message: input,
            });

            const botMessage = {
                text: response.data.message,
                sender: "bot",
                timestamp: new Date().toLocaleTimeString(),
            };
            setMessages((prevMessages) => [...prevMessages, botMessage]);

            if (response.data.plot) {
                try {
                    const plotData = JSON.parse(response.data.plot);
                    const plotMessage = {
                        plot: plotData,
                        sender: "bot",
                        timestamp: new Date().toLocaleTimeString(),
                    };
                    setMessages((prevMessages) => [
                        ...prevMessages,
                        plotMessage,
                    ]);
                } catch (error) {
                    console.error("Error parsing plot data:", error);
                }
            }
        } catch (error) {
            console.error("Error:", error);
            const errorMessage = {
                text: `An error occurred: ${error.message}. Please try again.`,
                sender: "bot",
                timestamp: new Date().toLocaleTimeString(),
            };
            setMessages((prevMessages) => [...prevMessages, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="App">
            <header className="App-header">
                <h1>Data Mystery Solver</h1>
                <p className="subtitle">Ask questions about your data</p>
            </header>
            <div className="chat-container">
                <div className="messages-wrapper">
                    {messages.map((message, index) => (
                        <div
                            key={index}
                            className={`message ${message.sender}`}
                        >
                            <div className="message-content">
                                {message.text && <p>{message.text}</p>}
                                {message.plot && (
                                    <Plot
                                        data={message.plot.data}
                                        layout={message.plot.layout}
                                        style={{
                                            width: "100%",
                                            height: "400px",
                                        }}
                                        config={{ responsive: true }}
                                    />
                                )}
                                <span className="timestamp">
                                    {message.timestamp}
                                </span>
                            </div>
                        </div>
                    ))}
                    {isLoading && (
                        <div className="message bot loading">
                            <div className="loading-dots">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    )}
                </div>
            </div>
            <form onSubmit={handleSubmit} className="input-form">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Type your message..."
                    disabled={isLoading}
                />
                <button type="submit" disabled={isLoading}>
                    <IoSend />
                </button>
            </form>
        </div>
    );
}

export default App;
