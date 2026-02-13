import React, { useState, useEffect, useRef, useCallback } from 'react';
import VoiceOrb from './VoiceOrb';
import MessageHistory from './MessageHistory';
import VoiceControls from './VoiceControls';
import './VoiceChat.css';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { API_ENDPOINTS } from '../config/api';

const API_URL = API_ENDPOINTS.ASK;

function VoiceChat() {
    const navigate = useNavigate();
    const { user } = useAuth();
    const [messages, setMessages] = useState([]);
    const [isListening, setIsListening] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [showHistory, setShowHistory] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [hasStarted, setHasStarted] = useState(false);
    const recognitionRef = useRef(null);
    const currentUtteranceRef = useRef(null);

    const stopAudio = useCallback(() => {
        window.speechSynthesis.cancel();
        setIsSpeaking(false);
    }, []);

    const speakText = useCallback((text) => {
        if (!('speechSynthesis' in window)) {
            alert('Text-to-speech not supported in this browser.');
            return;
        }

        // Cancel any ongoing speech
        window.speechSynthesis.cancel();
        setIsSpeaking(true);

        // Split text into manageable chunks (sentences)
        // This regex splits by common sentence terminators but keeps them
        const chunks = text.match(/[^.!?|]+[.!?|]*/g) || [text];

        let currentChunkIndex = 0;

        const speakNextChunk = () => {
            if (currentChunkIndex >= chunks.length) {
                setIsSpeaking(false);
                currentUtteranceRef.current = null;
                return;
            }

            const chunkText = chunks[currentChunkIndex].trim();
            if (!chunkText) {
                currentChunkIndex++;
                speakNextChunk();
                return;
            }

            const utterance = new SpeechSynthesisUtterance(chunkText);

            // Store reference to prevent garbage collection
            currentUtteranceRef.current = utterance;

            // Voice selection logic
            const hasDevanagari = /[\u0900-\u097F]/.test(chunkText);
            let voices = window.speechSynthesis.getVoices();

            // Retry voices if empty
            if (voices.length === 0) {
                voices = window.speechSynthesis.getVoices();
            }

            const findVoice = (lang, genderPreference) => {
                return voices.find(voice =>
                    voice.lang === lang &&
                    voice.name.toLowerCase().includes(genderPreference)
                );
            };

            let preferredVoice = null;

            if (hasDevanagari) {
                preferredVoice = voices.find(voice => voice.lang === 'sa-IN');
                if (!preferredVoice) preferredVoice = findVoice('hi-IN', 'male');
                if (!preferredVoice) preferredVoice = findVoice('hi-IN', 'hemant');
                if (!preferredVoice) preferredVoice = voices.find(voice => voice.lang === 'hi-IN');
                utterance.lang = preferredVoice ? preferredVoice.lang : 'hi-IN';
            } else {
                preferredVoice = findVoice('en-IN', 'male');
                if (!preferredVoice) preferredVoice = findVoice('en-IN', 'ravi'); // Microsoft Ravi
                if (!preferredVoice) preferredVoice = voices.find(voice => voice.lang === 'en-IN');
                if (!preferredVoice) preferredVoice = findVoice('en-US', 'male');
                if (!preferredVoice) preferredVoice = findVoice('en-US', 'david'); // Microsoft David
                if (!preferredVoice) preferredVoice = voices.find(voice => voice.lang.startsWith('en'));
                utterance.lang = preferredVoice ? preferredVoice.lang : 'en-US';
            }

            if (preferredVoice) {
                utterance.voice = preferredVoice;
            }

            utterance.rate = 0.9;
            utterance.pitch = 0.8;

            utterance.onend = () => {
                currentChunkIndex++;
                speakNextChunk();
            };

            utterance.onerror = (event) => {
                console.error('Speech synthesis error', event);
                // On error, try to skip to next chunk instead of dying completely
                currentChunkIndex++;
                speakNextChunk();
            };

            window.speechSynthesis.speak(utterance);
        };

        // Handle case where voices might not be loaded yet
        if (window.speechSynthesis.getVoices().length === 0) {
            window.speechSynthesis.onvoiceschanged = () => {
                speakNextChunk();
                // Remove listener to avoid multi-firing
                window.speechSynthesis.onvoiceschanged = null;
            };
        } else {
            speakNextChunk();
        }

    }, []);



    const handleVoiceInput = useCallback(async (text) => {
        if (!text.trim()) return;

        setTranscript('');

        // Add user message
        const userMessage = {
            id: Date.now(),
            type: 'user',
            text: text,
            timestamp: new Date()
        };
        setMessages(prev => [...prev, userMessage]);

        setIsLoading(true);

        try {
            const startTime = performance.now();

            // Request text only (disable backend audio generation)
            // Include user_id for conversation history
            const response = await axios.post(API_URL, {
                question: text,
                include_audio: false,
                user_id: user?.id  // Send user ID if logged in
            });

            const textTime = performance.now() - startTime;
            console.log(`⏱️ Text response received in ${textTime.toFixed(0)}ms`);

            const krishnaMessage = {
                id: Date.now() + 1,
                type: 'krishna',
                text: response.data.answer || 'क्षमा करें, मैं अभी उत्तर देने में असमर्थ हूँ।',
                timestamp: new Date()
            };

            setMessages(prev => [...prev, krishnaMessage]);

            // Speak the response using browser TTS
            speakText(krishnaMessage.text);

        } catch (error) {
            console.error('Error:', error);
            const errorMsg = {
                id: Date.now() + 1,
                type: 'krishna',
                text: 'क्षमा करें, कुछ गलत हो गया। कृपया पुनः प्रयास करें।',
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMsg]);
            speakText(errorMsg.text);
        } finally {
            setIsLoading(false);
        }
    }, [speakText, user]);

    useEffect(() => {
        // Initialize Speech Recognition
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!recognitionRef.current) {
                recognitionRef.current = new SpeechRecognition();
                recognitionRef.current.continuous = false;
                recognitionRef.current.interimResults = true;
                recognitionRef.current.lang = 'hi-IN';

                recognitionRef.current.onresult = (event) => {
                    const current = event.resultIndex;
                    const transcriptText = event.results[current][0].transcript;
                    setTranscript(transcriptText);

                    if (event.results[current].isFinal) {
                        handleVoiceInput(transcriptText);
                    }
                };

                recognitionRef.current.onerror = () => {
                    setIsListening(false);
                    setTranscript('');
                };

                recognitionRef.current.onend = () => {
                    setIsListening(false);
                };
            }
        }

        // Welcome message - only run once
        const timer = setTimeout(() => {
            setMessages(prev => {
                if (prev.length === 0) {
                    const welcomeMsg = {
                        id: Date.now(),
                        type: 'krishna',
                        text: 'नमस्ते! मैं कृष्ण हूँ। मुझसे कुछ भी पूछें।',
                        timestamp: new Date()
                    };
                    speakText(welcomeMsg.text);
                    return [welcomeMsg];
                }
                return prev;
            });
        }, 1500);

        return () => clearTimeout(timer);
    }, [handleVoiceInput, speakText]);

    const toggleListening = () => {
        if (!recognitionRef.current) {
            alert('Voice recognition not supported. Please use Chrome or Edge.');
            return;
        }

        if (isListening) {
            recognitionRef.current.stop();
            setIsListening(false);
            setTranscript('');
        } else {
            // Stop speaking if Krishna is talking
            if (isSpeaking) {
                stopAudio();
            }

            recognitionRef.current.start();
            setIsListening(true);
            setHasStarted(true);
        }
    };

    const stopSpeaking = () => {
        stopAudio();
    };

    const clearHistory = () => {
        // Stop any ongoing speech
        if (isSpeaking) {
            stopAudio();
        }
        // Clear all messages
        setMessages([]);
        // Reset to initial state
        setHasStarted(false);
    };

    return (
        <div className="voice-chat-container">
            {/* Header */}
            <header className="app-header">
                <button className="icon-button back-button" onClick={() => navigate('/')}>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M15 18l-6-6 6-6" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                </button>

                <div className="header-title-container">
                    <span className="logo-icon">🕉️</span>
                    <span className="header-title">Divine Voice</span>
                </div>

                <button
                    className="icon-button history-toggle"
                    onClick={() => setShowHistory(!showHistory)}
                    title="Toggle history"
                >
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="5" r="1" />
                        <circle cx="12" cy="12" r="1" />
                        <circle cx="12" cy="19" r="1" />
                    </svg>
                </button>
            </header>

            {/* Main Voice Interface */}
            <main className="main-content">
                {!hasStarted && (
                    <div className="hero-section">
                        <h1 className="hero-title">
                            Seek Guidance <br />
                            <span className="highlight">From The Divine</span>
                        </h1>
                        <div className="quick-actions">
                            <button className="action-chip active" onClick={() => { handleVoiceInput("Tell me about Karma Yoga"); setHasStarted(true); }}>
                                Start Journey
                            </button>
                            <button className="action-chip" onClick={() => setShowHistory(true)}>
                                History
                            </button>
                        </div>
                    </div>
                )}

                <div className="orb-section">
                    <h2 className="section-label">Soul Connection</h2>
                    <VoiceOrb
                        isListening={isListening}
                        isSpeaking={isSpeaking}
                        isLoading={isLoading}
                    />
                </div>

                {/* Status Text & Transcript */}
                <div className="status-container">
                    {transcript ? (
                        <p className="transcript">{transcript}</p>
                    ) : (
                        <p className="status-text">
                            {isListening ? 'Listening to your soul...' :
                                isSpeaking ? 'Krishna is guiding...' :
                                    isLoading ? 'Consulting the Gita...' :
                                        'Tap to Connect'}
                        </p>
                    )}
                </div>

                {/* Voice Controls */}
                <VoiceControls
                    isListening={isListening}
                    isSpeaking={isSpeaking}
                    onToggleListening={toggleListening}
                    onStopSpeaking={stopSpeaking}
                />
            </main>

            {/* Message History Sidebar */}
            <MessageHistory
                messages={messages}
                isOpen={showHistory}
                onClose={() => setShowHistory(false)}
                onClearHistory={clearHistory}
            />
        </div>
    );
}

export default VoiceChat;
