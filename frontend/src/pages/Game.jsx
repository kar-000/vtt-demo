import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useGame } from "../contexts/GameContext";
import CharacterSheet from "../components/CharacterSheet";
import InitiativeTracker from "../components/InitiativeTracker";
import DiceRoller from "../components/DiceRoller";
import RollLog from "../components/RollLog";
import NotesSection from "../components/NotesSection";
import ThemeSwitcher from "../components/ThemeSwitcher";
import "./Game.css";

export default function Game() {
  const { user } = useAuth();
  const { currentCharacter, connected } = useGame();
  const navigate = useNavigate();
  const [sidebarTab, setSidebarTab] = useState("combat");

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
          <div className="sidebar-tabs">
            <button
              className={`sidebar-tab ${sidebarTab === "combat" ? "active" : ""}`}
              onClick={() => setSidebarTab("combat")}
            >
              Combat
            </button>
            <button
              className={`sidebar-tab ${sidebarTab === "notes" ? "active" : ""}`}
              onClick={() => setSidebarTab("notes")}
            >
              Notes
            </button>
          </div>

          {sidebarTab === "combat" && (
            <>
              <InitiativeTracker />
              <DiceRoller />
              <RollLog />
            </>
          )}

          {sidebarTab === "notes" && currentCharacter?.campaign_id && (
            <NotesSection campaignId={currentCharacter.campaign_id} />
          )}

          {sidebarTab === "notes" && !currentCharacter?.campaign_id && (
            <div className="no-campaign-notes">
              <p>Notes require a campaign. Join or create a campaign first.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
