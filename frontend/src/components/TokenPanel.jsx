import React, { useState } from "react";
import "./TokenPanel.css";

const TOKEN_COLORS = [
  "#3498db", // Blue (default)
  "#e74c3c", // Red
  "#2ecc71", // Green
  "#9b59b6", // Purple
  "#f39c12", // Orange
  "#1abc9c", // Teal
  "#e91e63", // Pink
  "#795548", // Brown
];

export default function TokenPanel({
  characters = [],
  combatants = [],
  tokens = [],
  onAddToken,
}) {
  const [isAddingCustom, setIsAddingCustom] = useState(false);
  const [customToken, setCustomToken] = useState({
    name: "",
    color: TOKEN_COLORS[1], // Red for monsters
    size: 1,
  });

  // Get characters not already on the map
  const availableCharacters = characters.filter(
    (char) => !tokens.some((t) => t.characterId === char.id),
  );

  // Get combatants (from initiative) not already on map
  const availableCombatants = combatants.filter(
    (c) =>
      !c.character_id && // Only monsters (no character_id)
      !tokens.some((t) => t.name === c.name),
  );

  const handleAddCharacterToken = (character) => {
    onAddToken?.({
      id: `char-${character.id}-${Date.now()}`,
      characterId: character.id,
      name: character.name,
      color: "#3498db",
      size: 1,
      x: 0,
      y: 0,
    });
  };

  const handleAddCombatantToken = (combatant) => {
    onAddToken?.({
      id: `combatant-${combatant.id}-${Date.now()}`,
      name: combatant.name,
      color: "#e74c3c",
      size: combatant.size || 1,
      x: 0,
      y: 0,
    });
  };

  const handleAddCustomToken = () => {
    if (!customToken.name.trim()) return;

    onAddToken?.({
      id: `custom-${Date.now()}`,
      name: customToken.name.trim(),
      color: customToken.color,
      size: customToken.size,
      x: 0,
      y: 0,
    });

    setCustomToken({ name: "", color: TOKEN_COLORS[1], size: 1 });
    setIsAddingCustom(false);
  };

  return (
    <div className="token-panel">
      <div className="token-panel-header">
        <h4>Add Tokens</h4>
      </div>

      {/* Characters Section */}
      {availableCharacters.length > 0 && (
        <div className="token-section">
          <div className="token-section-title">Characters</div>
          <div className="token-list">
            {availableCharacters.map((char) => (
              <button
                key={char.id}
                className="token-add-btn character-token"
                onClick={() => handleAddCharacterToken(char)}
                title={`Add ${char.name} to map`}
              >
                <span
                  className="token-preview"
                  style={{ background: "#3498db" }}
                >
                  {char.name.charAt(0).toUpperCase()}
                </span>
                <span className="token-name">{char.name}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Combatants from Initiative */}
      {availableCombatants.length > 0 && (
        <div className="token-section">
          <div className="token-section-title">From Initiative</div>
          <div className="token-list">
            {availableCombatants.map((combatant) => (
              <button
                key={combatant.id}
                className="token-add-btn monster-token"
                onClick={() => handleAddCombatantToken(combatant)}
                title={`Add ${combatant.name} to map`}
              >
                <span
                  className="token-preview"
                  style={{ background: "#e74c3c" }}
                >
                  {combatant.name.charAt(0).toUpperCase()}
                </span>
                <span className="token-name">{combatant.name}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Custom Token */}
      <div className="token-section">
        <div className="token-section-title">Custom Token</div>
        {!isAddingCustom ? (
          <button
            className="btn btn-secondary btn-sm add-custom-btn"
            onClick={() => setIsAddingCustom(true)}
          >
            + Add Monster/NPC
          </button>
        ) : (
          <div className="custom-token-form">
            <input
              type="text"
              placeholder="Token name"
              value={customToken.name}
              onChange={(e) =>
                setCustomToken((prev) => ({ ...prev, name: e.target.value }))
              }
              autoFocus
            />
            <div className="color-picker">
              {TOKEN_COLORS.map((color) => (
                <button
                  key={color}
                  className={`color-option ${customToken.color === color ? "selected" : ""}`}
                  style={{ background: color }}
                  onClick={() => setCustomToken((prev) => ({ ...prev, color }))}
                />
              ))}
            </div>
            <div className="size-picker">
              <label>Size:</label>
              <select
                value={customToken.size}
                onChange={(e) =>
                  setCustomToken((prev) => ({
                    ...prev,
                    size: parseInt(e.target.value),
                  }))
                }
              >
                <option value={1}>Medium (1x1)</option>
                <option value={2}>Large (2x2)</option>
                <option value={3}>Huge (3x3)</option>
                <option value={4}>Gargantuan (4x4)</option>
              </select>
            </div>
            <div className="custom-token-actions">
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => setIsAddingCustom(false)}
              >
                Cancel
              </button>
              <button
                className="btn btn-primary btn-sm"
                onClick={handleAddCustomToken}
                disabled={!customToken.name.trim()}
              >
                Add
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Currently on Map */}
      {tokens.length > 0 && (
        <div className="token-section">
          <div className="token-section-title">On Map ({tokens.length})</div>
          <div className="tokens-on-map">
            {tokens.map((token) => (
              <span
                key={token.id}
                className="map-token-badge"
                style={{ borderColor: token.color }}
              >
                {token.name}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
