import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useGame } from "../contexts/GameContext";
import "./Dashboard.css";

export default function Dashboard() {
  const { user, logout } = useAuth();
  const {
    characters,
    allCharacters,
    setCurrentCharacter,
    deleteCharacter,
    createCharacter,
    loadAllCharacters,
    loading,
  } = useGame();
  const navigate = useNavigate();
  const [loadingAll, setLoadingAll] = useState(false);

  // Load all characters when DM views dashboard
  useEffect(() => {
    if (user?.is_dm && allCharacters.length === 0) {
      setLoadingAll(true);
      loadAllCharacters().finally(() => setLoadingAll(false));
    }
  }, [user?.is_dm]);

  // Get player characters (characters not owned by DM)
  const playerCharacters = allCharacters.filter(
    (char) => char.owner_id !== user?.id,
  );

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleSelectCharacter = (character) => {
    setCurrentCharacter(character);
    navigate("/game");
  };

  const handleCreateCharacter = () => {
    navigate("/character/new");
  };

  const handleDeleteCharacter = async (e, characterId) => {
    e.stopPropagation();
    if (window.confirm("Are you sure you want to delete this character?")) {
      try {
        await deleteCharacter(characterId);
      } catch (error) {
        alert("Failed to delete character");
      }
    }
  };

  const handleImportCharacter = () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".json";
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      try {
        const text = await file.text();
        const characterData = JSON.parse(text);

        // Remove fields that shouldn't be imported
        const {
          id,
          owner_id,
          created_at,
          updated_at,
          exported_at,
          export_version,
          ...importData
        } = characterData;

        // Create new character from imported data
        const newCharacter = await createCharacter(importData);
        alert(`Character "${newCharacter.name}" imported successfully!`);
      } catch (error) {
        console.error("Import error:", error);
        alert("Failed to import character. Please check the file format.");
      }
    };
    input.click();
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>D&D Virtual Tabletop</h1>
        <div className="user-info">
          <span>
            {user?.username} {user?.is_dm && "(DM)"}
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
            <div className="header-actions">
              <button
                onClick={handleImportCharacter}
                className="btn btn-secondary"
                title="Import character from JSON file"
              >
                📤 Import
              </button>
              <button
                onClick={handleCreateCharacter}
                className="btn btn-primary"
              >
                Create Character
              </button>
            </div>
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
                      Level {character.level} {character.race}{" "}
                      {character.character_class}
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

        {/* DM Section: View All Player Characters */}
        {user?.is_dm && (
          <div className="characters-section dm-section">
            <div className="section-header">
              <h2>Player Characters</h2>
              <span className="dm-badge">DM View</span>
            </div>

            {loadingAll ? (
              <p>Loading player characters...</p>
            ) : playerCharacters.length === 0 ? (
              <div className="empty-state">
                <p>No other player characters yet.</p>
              </div>
            ) : (
              <div className="characters-grid">
                {playerCharacters.map((character) => (
                  <div
                    key={character.id}
                    className="character-card player-card"
                    onClick={() => handleSelectCharacter(character)}
                  >
                    <div className="character-avatar">
                      {character.avatar_url ? (
                        <img src={character.avatar_url} alt={character.name} />
                      ) : (
                        <div className="avatar-placeholder player-avatar">
                          {character.name.charAt(0).toUpperCase()}
                        </div>
                      )}
                    </div>
                    <div className="character-info">
                      <h3>{character.name}</h3>
                      <p>
                        Level {character.level} {character.race}{" "}
                        {character.character_class}
                      </p>
                      <p className="character-hp">
                        HP: {character.current_hp}/{character.max_hp}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
