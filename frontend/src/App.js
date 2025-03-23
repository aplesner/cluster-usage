import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import UserList from './components/users/UserList';
import UserDetail from './components/users/UserDetail';
import DashboardHome from './components/dashboard/DashboardHome';
import HistoricUsage from './components/historic/HistoricUsage';
import './App.css';

function App() {
  return (
    <div className="app">
      <header className="header">
        <div className="container">
          <h1 className="logo">IO Usage Dashboard</h1>
          <nav className="nav">
            <ul className="nav-list">
              <li className="nav-item">
                <Link to="/" className="nav-link">Dashboard</Link>
              </li>
              <li className="nav-item">
                <Link to="/users" className="nav-link">Users</Link>
              </li>
              <li className="nav-item">
                <Link to="/machines" className="nav-link">Machines</Link>
              </li>
              <li className="nav-item">
                <Link to="/historic" className="nav-link">Historic Usage</Link>
              </li>
              <li className="nav-item">
                <Link to="/time" className="nav-link">Time Analysis</Link>
              </li>
              <li className="nav-item">
                <Link to="/sizes" className="nav-link">Size Distribution</Link>
              </li>
            </ul>
          </nav>
        </div>
      </header>
      
      <main className="main">
        <div className="container">
          <Routes>
            <Route path="/" element={<DashboardHome />} />
            <Route path="/users" element={<UserList />} />
            <Route path="/users/:username" element={<UserDetail />} />
            <Route path="/machines" element={<div>Machines Page (Coming Soon)</div>} />
            <Route path="/historic" element={<HistoricUsage />} />
            <Route path="/time" element={<div>Time Analysis (Coming Soon)</div>} />
            <Route path="/sizes" element={<div>Size Distribution (Coming Soon)</div>} />
            <Route path="*" element={<div>Page Not Found</div>} />
          </Routes>
        </div>
      </main>
      
      <footer className="footer">
        <div className="container">
          <p>IO Usage Dashboard &copy; {new Date().getFullYear()}</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
