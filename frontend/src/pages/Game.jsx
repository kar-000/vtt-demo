import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useGame } from "../contexts/GameContext";
import CharacterSheet from "../components/CharacterSheet";
import InitiativeTracker from "../components/InitiativeTracker";
import DiceRoller from "../components/DiceRoller";
import RollLog from "../components/RollLog";
import NotesSection from "../components/NotesSection";
import BattleMap from "../components/BattleMap";
import MapManager from "../components/MapManager";
import TokenPanel from "../components/TokenPanel";
import CampaignManager from "../components/CampaignManager";
import ThemeSwitcher from "../components/ThemeSwitcher";
import api from "../services/api";
import websocket from "../services/websocket";
import "./Game.css";

export default function Game() {
  const { user } = useAuth();
  const {
    currentCharacter,
    connected,
    characters,
    allCharacters,
    initiative,
    loadCharacters,
    loadAllCharacters,
  } = useGame();
  const navigate = useNavigate();
  const [sidebarTab, setSidebarTab] = useState("combat");
  const [mainTab, setMainTab] = useState("character");

  // Map state
  const [maps, setMaps] = useState([]);
  const [activeMap, setActiveMap] = useState(null);
  const [mapsLoading, setMapsLoading] = useState(false);

  const isDM = user?.is_dm;
  const campaignId = currentCharacter?.campaign_id;

  // Load maps for the campaign
  const loadMaps = useCallback(async () => {
    if (!campaignId) return;

    setMapsLoading(true);
    try {
      const mapList = await api.getCampaignMaps(campaignId);
      setMaps(mapList);

      // Load active map if there is one
      try {
        const active = await api.getActiveMap(campaignId);
        setActiveMap(active);
      } catch {
        setActiveMap(null);
      }
    } catch (err) {
      console.error("Failed to load maps:", err);
    } finally {
      setMapsLoading(false);
    }
  }, [campaignId]);

  useEffect(() => {
    loadMaps();
  }, [loadMaps]);

  // Load all characters for DM so they can see/add PCs in initiative
  useEffect(() => {
    if (isDM) {
      loadAllCharacters();
    }
  }, [isDM]);

  // Listen for real-time map updates from WebSocket
  useEffect(() => {
    const handleMapUpdate = (data) => {
      if (data.action === "tokens_updated" && data.map_id === activeMap?.id) {
        setActiveMap((prev) =>
          prev ? { ...prev, tokens: data.tokens } : prev,
        );
      } else if (data.action === "map_activated") {
        loadMaps();
      }
    };

    websocket.on("map_update", handleMapUpdate);
    return () => websocket.off("map_update", handleMapUpdate);
  }, [activeMap?.id, loadMaps]);

  // Token move handler
  const handleTokenMove = async (tokenId, x, y) => {
    if (!activeMap) return;

    try {
      const updated = await api.moveToken(activeMap.id, tokenId, x, y);
      setActiveMap(updated);
      // Broadcast to other players
      websocket.sendMapUpdate({
        action: "tokens_updated",
        map_id: activeMap.id,
        tokens: updated.tokens,
      });
    } catch (err) {
      console.error("Failed to move token:", err);
    }
  };

  // Update tokens handler
  const handleTokensUpdate = async (tokens) => {
    if (!activeMap) return;

    try {
      const updated = await api.updateMapTokens(activeMap.id, tokens);
      setActiveMap(updated);
      // Broadcast to other players
      websocket.sendMapUpdate({
        action: "tokens_updated",
        map_id: activeMap.id,
        tokens: updated.tokens,
      });
    } catch (err) {
      console.error("Failed to update tokens:", err);
    }
  };

  // Add token handler
  const handleAddToken = async (token) => {
    if (!activeMap) return;

    const newTokens = [...(activeMap.tokens || []), token];
    await handleTokensUpdate(newTokens);
  };

  // Remove token handler
  const handleRemoveToken = async (tokenId) => {
    if (!activeMap) return;

    const newTokens = (activeMap.tokens || []).filter((t) => t.id !== tokenId);
    await handleTokensUpdate(newTokens);
  };

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
          <div className="main-tabs">
            <button
              className={`main-tab ${mainTab === "character" ? "active" : ""}`}
              onClick={() => setMainTab("character")}
            >
              Character
            </button>
            <button
              className={`main-tab ${mainTab === "map" ? "active" : ""}`}
              onClick={() => setMainTab("map")}
            >
              Battle Map
              {activeMap && <span className="map-active-indicator"></span>}
            </button>
            {isDM && (
              <button
                className={`main-tab ${mainTab === "campaign" ? "active" : ""}`}
                onClick={() => setMainTab("campaign")}
              >
                Campaign
              </button>
            )}
          </div>

          {mainTab === "character" && (
            <CharacterSheet character={currentCharacter} />
          )}

          {mainTab === "campaign" && isDM && (
            <CampaignManager
              characters={allCharacters || characters}
              onCharacterUpdate={() => {
                loadCharacters();
                loadAllCharacters();
              }}
            />
          )}

          {mainTab === "map" && (
            <div className="battle-map-section">
              {isDM && campaignId && (
                <div className="map-controls-row">
                  <MapManager
                    campaignId={campaignId}
                    maps={maps}
                    activeMapId={activeMap?.id}
                    onRefresh={loadMaps}
                    onMapActivated={() => {
                      websocket.sendMapUpdate({ action: "map_activated" });
                    }}
                  />
                  {activeMap && (
                    <TokenPanel
                      characters={allCharacters || characters}
                      combatants={initiative?.combatants || []}
                      tokens={activeMap?.tokens || []}
                      onAddToken={handleAddToken}
                    />
                  )}
                </div>
              )}
              {isDM && !campaignId && (
                <div className="no-campaign-warning">
                  Create or join a campaign to use battle maps.
                </div>
              )}
              <BattleMap
                map={activeMap}
                tokens={activeMap?.tokens || []}
                onTokenMove={handleTokenMove}
                onTokenRemove={handleRemoveToken}
                onMapUpdated={setActiveMap}
                characters={allCharacters || characters}
                combatants={initiative?.combatants || []}
                editable={isDM}
              />
            </div>
          )}
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
