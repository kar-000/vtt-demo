import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useGame } from '../contexts/GameContext';
import './Dashboard.css';

export default function Dashboard() {
  const { user, logout } = useAuth();
  const { characters, setCurrentCharacter, deleteCharacter, loading } = useGame();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleSelectCharacter = (character) => {
    setCurrentCharacter(character);
    navigate('/game');
  };

  const handleCreateCharacter = () => {
    navigate('/character/new');
  };

  const handleDeleteCharacter = async (e, characterId) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this character?')) {
      try {
        await deleteCharacter(characterId);
      } catch (error) {
        alert('Failed to delete character');
      }
    }
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>D&D Virtual Tabletop</h1>
        <div className="user-info">
          <span>
            {user?.username} {user?.is_dm && '(DM)'}
          </span>
          <button onClick={handleLogout} className="btn btn-secondary">
            Logout
          </button>
        </div>
      </header>

      <main className="dashboard-content">
        <div className="characters-section">
          <div className="section-header">
            <h2>Your Characters</h2>
            <button onClick={handleCreateCharacter} className="btn btn-primary">
              Create Character
            </button>
          </div>

          {loading ? (
            <p>Loading characters...</p>
          ) : characters.length === 0 ? (
            <div className="empty-state">
              <p>You don't have any characters yet.</p>
              <p>Create your first character to get started!</p>
            </div>
          ) : (
            <div className="characters-grid">
              {characters.map((character) => (
                <div
                  key={character.id}
                  className="character-card"
                  onClick={() => handleSelectCharacter(character)}
                >
                  <div className="character-avatar">
                    {character.avatar_url ? (
                      <img src={character.avatar_url} alt={character.name} />
                    ) : (
                      <div className="avatar-placeholder">
                        {character.name.charAt(0).toUpperCase()}
                      </div>
                    )}
                  </div>
                  <div className="character-info">
                    <h3>{character.name}</h3>
                    <p>
                      Level {character.level} {character.race} {character.character_class}
                    </p>
                    <p className="character-hp">
                      HP: {character.current_hp}/{character.max_hp}
                    </p>
                  </div>
                  <button
                    className="delete-btn"
                    onClick={(e) => handleDeleteCharacter(e, character.id)}
                    title="Delete character"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
