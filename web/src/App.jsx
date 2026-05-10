import { useState, useRef, useEffect } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from 'react-leaflet';
import './index.css';

// Component to dynamically update map bounds
function ChangeView({ bounds }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [bounds, map]);
  return null;
}

function App() {
  const [userInput, setUserInput] = useState('');
  const [messages, setMessages] = useState([
    { type: 'system-msg', text: "Hi! I'm Dari, your intelligent navigation assistant. Tell me where you want to go, or just chat with me." }
  ]);
  const [loading, setLoading] = useState(false);
  const [routeData, setRouteData] = useState(null);
  
  const chatRef = useRef(null);

  // Auto-scroll chat
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!userInput.trim()) return;

    const message = userInput;
    setMessages(prev => [...prev, { type: 'user-msg', text: message }]);
    setLoading(true);
    setUserInput('');
    // We don't clear routeData here to keep the last path visible until a new one is found

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to communicate with agent.');
      }

      if (data.type === 'route') {
        setRouteData(data.data);
        setMessages(prev => [...prev, { type: 'system-msg', text: data.content }]);
      } else {
        setMessages(prev => [...prev, { type: 'system-msg', text: data.content }]);
      }

    } catch (err) {
      setMessages(prev => [...prev, { type: 'error-msg', text: `Error: ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1>Dari 🗺️</h1>
          <p>Agentic Navigation Reasoning</p>
        </div>
        
        <div className="chat-container" ref={chatRef}>
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.type}`} dangerouslySetInnerHTML={{ __html: msg.text }} />
          ))}
          {loading && (
            <div className="message system-msg">
              <span className="loading-dots">Thinking</span>
            </div>
          )}
        </div>

        <form className="input-area" onSubmit={handleSendMessage}>
          <input 
            type="text" 
            placeholder="Type your message... (e.g., 'Find a shortcut from Central Park to Times Square')" 
            value={userInput}
            onChange={e => setUserInput(e.target.value)}
            disabled={loading}
          />
          <button type="submit" disabled={loading || !userInput.trim()}>
            Send
          </button>
        </form>
      </aside>

      <main className="map-container">
        <MapContainer center={[40.7128, -74.0060]} zoom={13} scrollWheelZoom={true}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            maxZoom={19}
          />
          
          {routeData && (
            <>
              <Marker position={routeData.start_coords}>
                <Popup>Start</Popup>
              </Marker>
              <Marker position={routeData.end_coords}>
                <Popup>Destination</Popup>
              </Marker>
              <Polyline 
                positions={routeData.route} 
                pathOptions={{ color: '#10b981', weight: 5, opacity: 0.8, dashArray: '10, 10', lineJoin: 'round' }} 
              />
              <ChangeView bounds={routeData.route} />
            </>
          )}
        </MapContainer>
      </main>
    </div>
  );
}

export default App;
