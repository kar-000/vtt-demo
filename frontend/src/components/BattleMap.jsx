import React, { useRef, useState, useEffect, useCallback } from "react";
import { useAuth } from "../contexts/AuthContext";
import "./BattleMap.css";

export default function BattleMap({
  map,
  tokens,
  onTokenMove,
  onTokenAdd,
  onTokenRemove,
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

    // Draw fog of war (if enabled and not DM)
    if (map?.fog_enabled && !isDM) {
      const revealed = new Set(
        (map.revealed_cells || []).map((c) => `${c.x},${c.y}`),
      );

      ctx.fillStyle = "rgba(0, 0, 0, 0.9)";
      for (let x = 0; x < gridWidth; x++) {
        for (let y = 0; y < gridHeight; y++) {
          if (!revealed.has(`${x},${y}`)) {
            ctx.fillRect(x * gridSize, y * gridSize, gridSize, gridSize);
          }
        }
      }
    }

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

      // Token background
      ctx.fillStyle = token.color || "#3498db";
      ctx.globalAlpha = isDragging ? 0.7 : 1;
      ctx.beginPath();
      ctx.arc(x + size / 2, y + size / 2, size / 2 - 2, 0, Math.PI * 2);
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
      ctx.fillText(label, x + size / 2, y + size / 2);
    });

    ctx.restore();
  }, [
    map,
    mapImage,
    tokens,
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

  // Mouse handlers
  const handleMouseDown = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const screenX = e.clientX;
    const screenY = e.clientY;

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
    if (!editable || !isDM) return;

    const grid = screenToGrid(e.clientX, e.clientY);
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
      </div>

      <canvas
        ref={canvasRef}
        width={canvasWidth}
        height={canvasHeight}
        className="battle-map-canvas"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onDoubleClick={handleDoubleClick}
        onContextMenu={(e) => e.preventDefault()}
      />

      {isDM && editable && (
        <div className="map-instructions">
          <span>Drag tokens to move</span>
          <span>Scroll to zoom</span>
          <span>Drag empty space to pan</span>
        </div>
      )}
    </div>
  );
}
