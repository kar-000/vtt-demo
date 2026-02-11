import React, { useState, useRef } from "react";
import api from "../services/api";
import "./BattleMap.css";

export default function MapManager({
  campaignId,
  maps,
  activeMapId,
  onMapCreated,
  onMapActivated,
  onMapDeleted,
  onRefresh,
}) {
  const [isCreating, setIsCreating] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const [formData, setFormData] = useState({
    name: "",
    description: "",
    grid_width: 20,
    grid_height: 15,
    grid_size: 40,
    image_data: null,
  });

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith("image/")) {
      setError("Please select an image file");
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      setError("Image must be smaller than 5MB");
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      setFormData((prev) => ({ ...prev, image_data: event.target.result }));
      setError(null);
    };
    reader.readAsDataURL(file);
  };

  const handleCreate = async () => {
    if (!formData.name.trim()) {
      setError("Map name is required");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Build payload, excluding null/empty optional fields (Pydantic v1 compatibility)
      const payload = {
        campaign_id: campaignId,
        name: formData.name.trim(),
        grid_width: parseInt(formData.grid_width),
        grid_height: parseInt(formData.grid_height),
        grid_size: parseInt(formData.grid_size),
      };
      if (formData.description.trim()) {
        payload.description = formData.description.trim();
      }
      if (formData.image_data) {
        payload.image_data = formData.image_data;
      }
      const newMap = await api.createMap(payload);

      onMapCreated?.(newMap);
      setIsCreating(false);
      setFormData({
        name: "",
        description: "",
        grid_width: 20,
        grid_height: 15,
        grid_size: 40,
        image_data: null,
      });
      onRefresh?.();
    } catch (err) {
      setError(err.message || "Failed to create map");
    } finally {
      setIsLoading(false);
    }
  };

  const handleActivate = async (mapId) => {
    setIsLoading(true);
    try {
      await api.activateMap(mapId);
      onMapActivated?.(mapId);
      onRefresh?.();
    } catch (err) {
      setError(err.message || "Failed to activate map");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (mapId) => {
    if (!confirm("Are you sure you want to delete this map?")) return;

    setIsLoading(true);
    try {
      await api.deleteMap(mapId);
      onMapDeleted?.(mapId);
      onRefresh?.();
    } catch (err) {
      setError(err.message || "Failed to delete map");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="map-manager">
      <div className="map-manager-header">
        <h4>Battle Maps</h4>
        <button
          className="btn btn-primary btn-sm"
          onClick={() => setIsCreating(!isCreating)}
        >
          {isCreating ? "Cancel" : "+ New Map"}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Map List */}
      <div className="map-list">
        {maps.length === 0 && !isCreating && (
          <p className="no-maps-message">
            No maps yet. Create one to get started!
          </p>
        )}

        {maps.map((map) => (
          <div
            key={map.id}
            className={`map-list-item ${map.is_active ? "active" : ""}`}
          >
            <div>
              <span className="map-name">{map.name}</span>
              <span className="map-size">
                {map.grid_width}x{map.grid_height}
              </span>
              {map.is_active && <span className="active-badge">Active</span>}
            </div>
            <div className="map-actions">
              {!map.is_active && (
                <button
                  className="btn-icon"
                  onClick={() => handleActivate(map.id)}
                  disabled={isLoading}
                  title="Activate"
                >
                  ▶
                </button>
              )}
              <button
                className="btn-icon btn-danger"
                onClick={() => handleDelete(map.id)}
                disabled={isLoading}
                title="Delete"
              >
                ✕
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Create Map Form */}
      {isCreating && (
        <div className="map-form">
          <div className="form-group">
            <label>Map Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, name: e.target.value }))
              }
              placeholder="Dungeon Level 1"
            />
          </div>

          <div className="form-group">
            <label>Description (optional)</label>
            <textarea
              value={formData.description}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  description: e.target.value,
                }))
              }
              placeholder="A dark and dangerous dungeon..."
            />
          </div>

          <div className="map-form-row">
            <div className="form-group">
              <label>Width (squares)</label>
              <input
                type="number"
                min="5"
                max="100"
                value={formData.grid_width}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    grid_width: e.target.value,
                  }))
                }
              />
            </div>
            <div className="form-group">
              <label>Height (squares)</label>
              <input
                type="number"
                min="5"
                max="100"
                value={formData.grid_height}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    grid_height: e.target.value,
                  }))
                }
              />
            </div>
            <div className="form-group">
              <label>Grid Size (px)</label>
              <input
                type="number"
                min="20"
                max="100"
                value={formData.grid_size}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    grid_size: e.target.value,
                  }))
                }
              />
            </div>
          </div>

          <div className="image-upload">
            <label>Background Image (optional)</label>
            <div
              className={`image-upload-area ${formData.image_data ? "has-image" : ""}`}
              onClick={() => fileInputRef.current?.click()}
            >
              {formData.image_data ? (
                <img src={formData.image_data} alt="Map preview" />
              ) : (
                <span>Click to upload an image (max 5MB)</span>
              )}
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleImageUpload}
            />
            {formData.image_data && (
              <button
                className="btn btn-secondary btn-sm"
                onClick={() =>
                  setFormData((prev) => ({ ...prev, image_data: null }))
                }
              >
                Remove Image
              </button>
            )}
          </div>

          <div className="map-form-actions">
            <button
              className="btn btn-secondary"
              onClick={() => setIsCreating(false)}
            >
              Cancel
            </button>
            <button
              className="btn btn-primary"
              onClick={handleCreate}
              disabled={isLoading}
            >
              {isLoading ? "Creating..." : "Create Map"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
