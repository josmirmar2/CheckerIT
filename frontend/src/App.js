import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './components/Home';
import Game from './components/Game';
import Tutorial from './components/Tutorial';
import Players from './components/Players';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/players" element={<Players />} />
          <Route path="/game" element={<Game />} />
          <Route path="/tutorial" element={<Tutorial />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
