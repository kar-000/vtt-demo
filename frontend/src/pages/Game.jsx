import React from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useGame } from "../contexts/GameContext";
import CharacterSheet from "../components/CharacterSheet";
import InitiativeTracker from "../components/InitiativeTracker";
import DiceRoller from "../components/DiceRoller";
import RollLog from "../components/RollLog";
import ThemeSwitcher from "../components/ThemeSwitcher";
import "./Game.css";

export default function Game() {
  const { user } = useAuth();
  const { currentCharacter, connected } = useGame();
  const navigate = useNavigate();

  if (!currentCharacter) {
    return (
      <div className="game-page">
        <div className="no-character">
          <h2>No Character Selected</h2>
          <p>Please select a character from the dashboard to start playing.</p>
          <button
            onClick={() => navigate("/dashboard")}
            className="btn btn-primary"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="game-page">
      <header className="game-header">
        <div className="header-left">
          <button
            onClick={() => navigate("/dashboard")}
            className="btn btn-secondary"
          >
            ← Back to Dashboard
          </button>
          <h1>{currentCharacter.name}</h1>
        </div>
        <div className="header-right">
          <ThemeSwitcher compact />
          <div
            className={`connection-status ${connected ? "connected" : "disconnected"}`}
          >
            <span className="status-dot"></span>
            {connected ? "Connected" : "Disconnected"}
          </div>
          <span className="user-badge">
            {user?.username} {user?.is_dm && "(DM)"}
          </span>
        </div>
      </header>

      <div className="game-content">
        <div className="game-main">
          <CharacterSheet character={currentCharacter} />
        </div>
        <div className="game-sidebar">
          <InitiativeTracker />
          <DiceRoller />
          <RollLog />
        </div>
      </div>
    </div>
  );
}
