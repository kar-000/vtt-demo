import React, { useRef, useState, useEffect, useCallback } from "react";
import { useAuth } from "../contexts/AuthContext";
import api from "../services/api";
import conditionsData from "../data/srd-conditions.json";
import "./BattleMap.css";

export default function BattleMap({
  map,
  tokens,
  onTokenMove,
  onTokenAdd,
  onTokenRemove,
  onMapUpdated,
  characters,
  combatants,
  editable = false,
}) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const { user } = useAuth();
  const isDM = user?.is_dm;

  // View state
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [lastPanPoint, setLastPanPoint] = useState({ x: 0, y: 0 });

  // Drag state
  const [draggedToken, setDraggedToken] = useState(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [dragPosition, setDragPosition] = useState({ x: 0, y: 0 });

  // Fog of war state
  const [fogMode, setFogMode] = useState(false);
  const [isFogPainting, setIsFogPainting] = useState(false);
  const [fogAction, setFogAction] = useState(null); // "reveal" or "hide"

  // Image loading
  const [mapImage, setMapImage] = useState(null);

  // Load map background image
  useEffect(() => {
    if (map?.image_data) {
      const img = new Image();
      img.onload = () => setMapImage(img);
      img.src = map.image_data;
    } else {
      setMapImage(null);
    }
  }, [map?.image_data]);

  // Calculate canvas dimensions
  const gridSize = map?.grid_size || 40;
  const gridWidth = map?.grid_width || 20;
  const gridHeight = map?.grid_height || 15;
  const canvasWidth = gridWidth * gridSize;
  const canvasHeight = gridHeight * gridSize;

  // Convert screen coordinates to grid coordinates
  const screenToGrid = (screenX, screenY) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };

    const rect = canvas.getBoundingClientRect();
    // Account for CSS scaling: canvas display size may differ from attribute size
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = ((screenX - rect.left) * scaleX - pan.x) / zoom;
    const y = ((screenY - rect.top) * scaleY - pan.y) / zoom;

    return {
      x: Math.floor(x / gridSize),
      y: Math.floor(y / gridSize),
    };
  };

  // Convert grid coordinates to screen position
  const gridToScreen = (gridX, gridY) => {
    return {
      x: gridX * gridSize * zoom + pan.x,
      y: gridY * gridSize * zoom + pan.y,
    };
  };

  // Find token at screen position
  const getTokenAtPosition = (screenX, screenY) => {
    const grid = screenToGrid(screenX, screenY);
    return tokens.find(
      (t) =>
        grid.x >= t.x &&
        grid.x < t.x + (t.size || 1) &&
        grid.y >= t.y &&
        grid.y < t.y + (t.size || 1),
    );
  };

  // Build condition lookup by name (short labels for canvas rendering)
  const conditionLookup = {};
  conditionsData.forEach((c) => {
    conditionLookup[c.name] = c;
  });

  // Short labels for canvas (emojis don't render reliably on canvas)
  const CONDITION_LABELS = {
    Blinded: "BL",
    Charmed: "CH",
    Deafened: "DE",
    Frightened: "FR",
    Grappled: "GR",
    Incapacitated: "IN",
    Invisible: "IV",
    Paralyzed: "PA",
    Petrified: "PE",
    Poisoned: "PO",
    Prone: "PR",
    Restrained: "RE",
    Stunned: "ST",
    Unconscious: "UN",
    Concentrating: "CO",
    Dodging: "DO",
    Raging: "RA",
    Hexed: "HX",
    Blessed: "BL",
    "Hunter's Mark": "HM",
  };

  // Draw the map
  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    // Clear canvas
    ctx.fillStyle = "#1a1a2e";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Apply transformations
    ctx.save();
    ctx.translate(pan.x, pan.y);
    ctx.scale(zoom, zoom);

    // Draw background image if available
    if (mapImage) {
      ctx.drawImage(mapImage, 0, 0, canvasWidth, canvasHeight);
    }

    // Draw grid
    if (map?.show_grid !== false) {
      ctx.strokeStyle = map?.grid_color || "rgba(255, 255, 255, 0.2)";
      ctx.lineWidth = 1 / zoom;

      // Vertical lines
      for (let x = 0; x <= gridWidth; x++) {
        ctx.beginPath();
        ctx.moveTo(x * gridSize, 0);
        ctx.lineTo(x * gridSize, canvasHeight);
        ctx.stroke();
      }

      // Horizontal lines
      for (let y = 0; y <= gridHeight; y++) {
        ctx.beginPath();
        ctx.moveTo(0, y * gridSize);
        ctx.lineTo(canvasWidth, y * gridSize);
        ctx.stroke();
      }
    }

    // Draw fog of war
    if (map?.fog_enabled) {
      const revealed = new Set(
        (map.revealed_cells || []).map((c) => `${c.x},${c.y}`),
      );

      if (isDM) {
        // DM sees a light overlay on hidden cells
        ctx.fillStyle = "rgba(0, 0, 0, 0.35)";
        for (let x = 0; x < gridWidth; x++) {
          for (let y = 0; y < gridHeight; y++) {
            if (!revealed.has(`${x},${y}`)) {
              ctx.fillRect(x * gridSize, y * gridSize, gridSize, gridSize);
            }
          }
        }
      } else {
        // Players see opaque fog on hidden cells
        ctx.fillStyle = "rgba(0, 0, 0, 0.9)";
        for (let x = 0; x < gridWidth; x++) {
          for (let y = 0; y < gridHeight; y++) {
            if (!revealed.has(`${x},${y}`)) {
              ctx.fillRect(x * gridSize, y * gridSize, gridSize, gridSize);
            }
          }
        }
      }
    }

    // Helper: match token to combatant
    const findCombatant = (token) => {
      if (!combatants || combatants.length === 0) return null;
      // Direct match via combatant_id
      if (token.combatant_id) {
        const match = combatants.find((c) => c.id === token.combatant_id);
        if (match) return match;
      }
      // Fallback: PC token via characterId
      if (token.characterId) {
        const match = combatants.find(
          (c) => c.character_id && c.character_id === token.characterId,
        );
        if (match) return match;
      }
      // Fallback: NPC by name
      const match = combatants.find(
        (c) => !c.character_id && c.name === token.name,
      );
      return match || null;
    };

    // Draw tokens
    tokens.forEach((token) => {
      const size = (token.size || 1) * gridSize;
      const isDragging = draggedToken?.id === token.id;

      // If dragging this token, draw at drag position; otherwise at stored position
      let x, y;
      if (isDragging) {
        // Calculate snapped grid position for preview
        const snapX = Math.max(
          0,
          Math.min(
            gridWidth - (token.size || 1),
            dragPosition.x - dragOffset.x,
          ),
        );
        const snapY = Math.max(
          0,
          Math.min(
            gridHeight - (token.size || 1),
            dragPosition.y - dragOffset.y,
          ),
        );
        x = snapX * gridSize;
        y = snapY * gridSize;
      } else {
        x = token.x * gridSize;
        y = token.y * gridSize;
      }

      const centerX = x + size / 2;
      const centerY = y + size / 2;
      const radius = size / 2 - 2;

      // Find matched combatant for status overlays
      const combatant = findCombatant(token);

      // HP ring for combatants
      // NPCs have HP in combatant data; PCs need character lookup
      let hpCurrent = combatant?.current_hp;
      let hpMax = combatant?.max_hp;
      if (combatant?.character_id && characters) {
        const char = characters.find((ch) => ch.id === combatant.character_id);
        if (char) {
          hpCurrent = char.current_hp;
          hpMax = char.max_hp;
        }
      }
      if (combatant && hpMax > 0 && hpCurrent != null) {
        const hpPct = hpCurrent / hpMax;
        let ringColor;
        if (hpPct > 0.5) ringColor = "#2ecc71";
        else if (hpPct > 0.25) ringColor = "#f1c40f";
        else ringColor = "#e74c3c";

        // Draw HP arc (full circle background + colored arc for remaining HP)
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius + 2, 0, Math.PI * 2);
        ctx.strokeStyle = "rgba(0,0,0,0.4)";
        ctx.lineWidth = 4 / zoom;
        ctx.stroke();

        if (hpPct > 0) {
          ctx.beginPath();
          const startAngle = -Math.PI / 2;
          const endAngle = startAngle + Math.PI * 2 * hpPct;
          ctx.arc(centerX, centerY, radius + 2, startAngle, endAngle);
          ctx.strokeStyle = ringColor;
          ctx.lineWidth = 4 / zoom;
          ctx.stroke();
        }
      }

      // Token background
      ctx.fillStyle = token.color || "#3498db";
      ctx.globalAlpha = isDragging ? 0.7 : 1;
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
      ctx.fill();

      // Token border
      ctx.strokeStyle = isDragging ? "#fff" : "rgba(0,0,0,0.5)";
      ctx.lineWidth = isDragging ? 3 / zoom : 2 / zoom;
      ctx.stroke();
      ctx.globalAlpha = 1;

      // Token label
      ctx.fillStyle = "#fff";
      ctx.font = `${Math.max(10, size / 3)}px Arial`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";

      // Truncate name if too long
      let label = token.name || "?";
      if (label.length > 6) {
        label = label.substring(0, 5) + "...";
      }
      ctx.fillText(label, centerX, centerY);

      // Condition badges (drawn below the token)
      if (
        combatant &&
        combatant.conditions &&
        combatant.conditions.length > 0
      ) {
        const conditions = combatant.conditions;
        const maxBadges = 3;
        const badgeW = Math.max(14, size / 3);
        const badgeH = Math.max(10, size / 5);
        const badgeGap = 2;
        const badgeY = y + size + 2;
        const totalBadges = Math.min(conditions.length, maxBadges);
        const hasOverflow = conditions.length > maxBadges;
        const itemCount = totalBadges + (hasOverflow ? 1 : 0);
        const totalWidth = itemCount * badgeW + (itemCount - 1) * badgeGap;
        const startX = centerX - totalWidth / 2;

        for (let i = 0; i < totalBadges; i++) {
          const cond = conditions[i];
          const condInfo = conditionLookup[cond.name] || {};
          const bx = startX + i * (badgeW + badgeGap);

          // Badge rounded rect background
          const br = 3;
          ctx.beginPath();
          ctx.roundRect(bx, badgeY, badgeW, badgeH, br);
          ctx.fillStyle = condInfo.color || "#666";
          ctx.globalAlpha = 0.9;
          ctx.fill();
          ctx.strokeStyle = "rgba(0,0,0,0.5)";
          ctx.lineWidth = 1 / zoom;
          ctx.stroke();
          ctx.globalAlpha = 1;

          // Short text label
          const abbr =
            CONDITION_LABELS[cond.name] ||
            cond.name.substring(0, 2).toUpperCase();
          ctx.font = `bold ${Math.max(7, badgeH * 0.7)}px Arial`;
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillStyle = "#fff";
          ctx.fillText(abbr, bx + badgeW / 2, badgeY + badgeH / 2);
        }

        // Overflow indicator
        if (hasOverflow) {
          const bx = startX + totalBadges * (badgeW + badgeGap);
          const br = 3;
          ctx.beginPath();
          ctx.roundRect(bx, badgeY, badgeW, badgeH, br);
          ctx.fillStyle = "#555";
          ctx.globalAlpha = 0.9;
          ctx.fill();
          ctx.strokeStyle = "rgba(0,0,0,0.5)";
          ctx.lineWidth = 1 / zoom;
          ctx.stroke();
          ctx.globalAlpha = 1;

          ctx.font = `bold ${Math.max(7, badgeH * 0.7)}px Arial`;
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillStyle = "#fff";
          ctx.fillText(
            `+${conditions.length - maxBadges}`,
            bx + badgeW / 2,
            badgeY + badgeH / 2,
          );
        }
      }
    });

    ctx.restore();
  }, [
    map,
    mapImage,
    tokens,
    combatants,
    characters,
    zoom,
    pan,
    gridSize,
    gridWidth,
    gridHeight,
    canvasWidth,
    canvasHeight,
    isDM,
    draggedToken,
    dragPosition,
    dragOffset,
  ]);

  // Redraw on changes
  useEffect(() => {
    draw();
  }, [draw]);

  // Wheel handler with non-passive listener to prevent page scroll
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const wheelHandler = (e) => {
      e.preventDefault();
      const delta = e.deltaY > 0 ? 0.9 : 1.1;
      const newZoom = Math.max(0.25, Math.min(3, zoom * delta));

      const rect = canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      const zoomFactor = newZoom / zoom;
      setPan((prev) => ({
        x: mouseX - (mouseX - prev.x) * zoomFactor,
        y: mouseY - (mouseY - prev.y) * zoomFactor,
      }));
      setZoom(newZoom);
    };

    canvas.addEventListener("wheel", wheelHandler, { passive: false });
    return () => canvas.removeEventListener("wheel", wheelHandler);
  }, [zoom]);

  // Fog of war helpers
  const toggleFogEnabled = async () => {
    if (!map) return;
    try {
      const updated = await api.updateMap(map.id, {
        fog_enabled: !map.fog_enabled,
      });
      onMapUpdated?.(updated);
    } catch (err) {
      console.error("Failed to toggle fog:", err);
    }
  };

  const paintFogCell = async (screenX, screenY, action) => {
    if (!map) return;
    const grid = screenToGrid(screenX, screenY);
    if (grid.x < 0 || grid.x >= gridWidth || grid.y < 0 || grid.y >= gridHeight)
      return;

    try {
      const updated = await api.updateFog(
        map.id,
        [{ x: grid.x, y: grid.y }],
        action,
      );
      onMapUpdated?.(updated);
    } catch (err) {
      console.error("Failed to update fog:", err);
    }
  };

  // Mouse handlers
  const handleMouseDown = (e) => {
    const screenX = e.clientX;
    const screenY = e.clientY;

    // Fog painting mode
    if (fogMode && isDM && map?.fog_enabled) {
      e.preventDefault();
      const action = e.button === 2 ? "remove" : "add"; // right-click hides, left-click reveals
      setIsFogPainting(true);
      setFogAction(action);
      paintFogCell(screenX, screenY, action);
      return;
    }

    // Check for token drag
    if (editable && isDM) {
      const token = getTokenAtPosition(screenX, screenY);
      if (token) {
        setDraggedToken(token);
        const grid = screenToGrid(screenX, screenY);
        setDragOffset({ x: grid.x - token.x, y: grid.y - token.y });
        setDragPosition(grid);
        return;
      }
    }

    // Start panning (left click on empty space, middle click, or ctrl+left click)
    if (e.button === 0 || e.button === 1) {
      e.preventDefault();
      setIsPanning(true);
      setLastPanPoint({ x: e.clientX, y: e.clientY });
    }
  };

  const handleMouseMove = (e) => {
    // Fog painting drag
    if (isFogPainting && fogMode && isDM && fogAction) {
      paintFogCell(e.clientX, e.clientY, fogAction);
      return;
    }

    if (isPanning) {
      const dx = e.clientX - lastPanPoint.x;
      const dy = e.clientY - lastPanPoint.y;
      setPan((prev) => ({ x: prev.x + dx, y: prev.y + dy }));
      setLastPanPoint({ x: e.clientX, y: e.clientY });
    }

    if (draggedToken && editable) {
      // Update drag position for visual feedback
      const grid = screenToGrid(e.clientX, e.clientY);
      setDragPosition(grid);
    }
  };

  const handleMouseUp = (e) => {
    if (isFogPainting) {
      setIsFogPainting(false);
      setFogAction(null);
      return;
    }

    if (isPanning) {
      setIsPanning(false);
    }

    if (draggedToken && editable && isDM) {
      const grid = screenToGrid(e.clientX, e.clientY);
      const newX = Math.max(
        0,
        Math.min(gridWidth - (draggedToken.size || 1), grid.x - dragOffset.x),
      );
      const newY = Math.max(
        0,
        Math.min(gridHeight - (draggedToken.size || 1), grid.y - dragOffset.y),
      );

      if (newX !== draggedToken.x || newY !== draggedToken.y) {
        onTokenMove?.(draggedToken.id, newX, newY);
      }
      setDraggedToken(null);
    }
  };

  const handleDoubleClick = (e) => {
    if (fogMode) return; // Don't remove tokens in fog mode
    if (!editable || !isDM) return;

    const existingToken = getTokenAtPosition(e.clientX, e.clientY);

    if (existingToken) {
      // Remove token on double-click
      onTokenRemove?.(existingToken.id);
    }
  };

  // Reset view
  const resetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  if (!map) {
    return (
      <div className="battle-map-empty">
        <p>No map loaded</p>
        {isDM && <p className="hint">Create or activate a map to begin</p>}
      </div>
    );
  }

  return (
    <div className="battle-map-container" ref={containerRef}>
      <div className="map-controls">
        <button
          className="btn-map-control"
          onClick={() => setZoom((z) => Math.min(3, z * 1.2))}
          title="Zoom In"
        >
          +
        </button>
        <span className="zoom-level">{Math.round(zoom * 100)}%</span>
        <button
          className="btn-map-control"
          onClick={() => setZoom((z) => Math.max(0.25, z / 1.2))}
          title="Zoom Out"
        >
          -
        </button>
        <button
          className="btn-map-control"
          onClick={resetView}
          title="Reset View"
        >
          ↺
        </button>
        {isDM && editable && (
          <>
            <span className="control-divider">|</span>
            <button
              className={`btn-map-control ${map?.fog_enabled ? "active" : ""}`}
              onClick={toggleFogEnabled}
              title={
                map?.fog_enabled ? "Disable Fog of War" : "Enable Fog of War"
              }
            >
              ☁
            </button>
            {map?.fog_enabled && (
              <button
                className={`btn-map-control ${fogMode ? "active" : ""}`}
                onClick={() => setFogMode(!fogMode)}
                title={
                  fogMode
                    ? "Exit Fog Edit Mode"
                    : "Edit Fog (click=reveal, right-click=hide)"
                }
              >
                ✎
              </button>
            )}
          </>
        )}
      </div>

      <canvas
        ref={canvasRef}
        width={canvasWidth}
        height={canvasHeight}
        className={`battle-map-canvas ${fogMode ? "fog-cursor" : ""}`}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onDoubleClick={handleDoubleClick}
        onContextMenu={(e) => e.preventDefault()}
      />

      {isDM && editable && (
        <div className="map-instructions">
          {fogMode ? (
            <>
              <span>Click to reveal</span>
              <span>Right-click to hide</span>
              <span>Drag to paint</span>
            </>
          ) : (
            <>
              <span>Drag tokens to move</span>
              <span>Scroll to zoom</span>
              <span>Drag empty space to pan</span>
            </>
          )}
        </div>
      )}
    </div>
  );
}
