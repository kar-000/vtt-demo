import React, { useState, useEffect } from "react";
import api from "../services/api";
import "./CampaignManager.css";

export default function CampaignManager({ characters, onCharacterUpdate }) {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isCreating, setIsCreating] = useState(false);
  const [formData, setFormData] = useState({ name: "", description: "" });

  // Load campaigns on mount
  useEffect(() => {
    loadCampaigns();
  }, []);

  const loadCampaigns = async () => {
    try {
      const data = await api.getCampaigns();
      setCampaigns(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!formData.name.trim()) {
      setError("Campaign name is required");
      return;
    }

    try {
      const payload = { name: formData.name.trim() };
      if (formData.description.trim()) {
        payload.description = formData.description.trim();
      }
      await api.createCampaign(payload);
      setFormData({ name: "", description: "" });
      setIsCreating(false);
      setError(null);
      loadCampaigns();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (campaignId) => {
    if (!confirm("Delete this campaign? All characters will be unassigned.")) {
      return;
    }

    try {
      await api.deleteCampaign(campaignId);
      loadCampaigns();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleJoin = async (campaignId, characterId) => {
    try {
      await api.joinCampaign(campaignId, characterId);
      onCharacterUpdate?.();
      loadCampaigns();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleLeave = async (campaignId, characterId) => {
    try {
      await api.leaveCampaign(campaignId, characterId);
      onCharacterUpdate?.();
      loadCampaigns();
    } catch (err) {
      setError(err.message);
    }
  };

  // Get characters not in any campaign
  const unassignedCharacters = characters.filter((c) => !c.campaign_id);

  if (loading) {
    return <div className="campaign-manager">Loading campaigns...</div>;
  }

  return (
    <div className="campaign-manager">
      <div className="campaign-header">
        <h3>Campaigns</h3>
        <button
          className="btn btn-primary btn-sm"
          onClick={() => setIsCreating(!isCreating)}
        >
          {isCreating ? "Cancel" : "+ New Campaign"}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {isCreating && (
        <div className="campaign-form">
          <input
            type="text"
            placeholder="Campaign Name"
            value={formData.name}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, name: e.target.value }))
            }
          />
          <textarea
            placeholder="Description (optional)"
            value={formData.description}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, description: e.target.value }))
            }
          />
          <button className="btn btn-primary" onClick={handleCreate}>
            Create Campaign
          </button>
        </div>
      )}

      {campaigns.length === 0 && !isCreating ? (
        <p className="no-campaigns">
          No campaigns yet. Create one to enable battle maps!
        </p>
      ) : (
        <div className="campaign-list">
          {campaigns.map((campaign) => (
            <div key={campaign.id} className="campaign-item">
              <div className="campaign-info">
                <h4>{campaign.name}</h4>
                {campaign.description && <p>{campaign.description}</p>}
                <span className="character-count">
                  {campaign.character_count} character(s)
                </span>
              </div>

              <div className="campaign-actions">
                {/* Character assignment dropdown */}
                {unassignedCharacters.length > 0 && (
                  <select
                    onChange={(e) => {
                      if (e.target.value) {
                        handleJoin(campaign.id, parseInt(e.target.value));
                        e.target.value = "";
                      }
                    }}
                    defaultValue=""
                  >
                    <option value="" disabled>
                      + Add character
                    </option>
                    {unassignedCharacters.map((char) => (
                      <option key={char.id} value={char.id}>
                        {char.name}
                      </option>
                    ))}
                  </select>
                )}

                <button
                  className="btn-icon btn-danger"
                  onClick={() => handleDelete(campaign.id)}
                  title="Delete campaign"
                >
                  ✕
                </button>
              </div>

              {/* Show characters in campaign */}
              <div className="campaign-characters">
                {characters
                  .filter((c) => c.campaign_id === campaign.id)
                  .map((char) => (
                    <span key={char.id} className="character-tag">
                      {char.name}
                      <button
                        className="remove-char"
                        onClick={() => handleLeave(campaign.id, char.id)}
                        title="Remove from campaign"
                      >
                        ×
                      </button>
                    </span>
                  ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
