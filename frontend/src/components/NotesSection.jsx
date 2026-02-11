import { useState, useEffect } from "react";
import api from "../services/api";
import { useAuth } from "../contexts/AuthContext";
import "./NotesSection.css";

const NOTE_TYPES = [
  { value: "session_note", label: "Session Notes" },
  { value: "character_journal", label: "Character Journal" },
  { value: "dm_note", label: "DM Notes" },
];

export default function NotesSection({ campaignId }) {
  const { user } = useAuth();
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isCreating, setIsCreating] = useState(false);
  const [editingNote, setEditingNote] = useState(null);
  const [expandedNoteId, setExpandedNoteId] = useState(null);
  const [filterType, setFilterType] = useState("");

  const [formData, setFormData] = useState({
    title: "",
    content: "",
    note_type: "session_note",
    is_public: false,
    tags: "",
  });

  useEffect(() => {
    if (campaignId) {
      loadNotes();
    }
  }, [campaignId, filterType]);

  const loadNotes = async () => {
    try {
      setLoading(true);
      const data = await api.getCampaignNotes(
        campaignId,
        filterType || null,
        null,
      );
      setNotes(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      title: "",
      content: "",
      note_type: "session_note",
      is_public: false,
      tags: "",
    });
  };

  const handleCreate = () => {
    setIsCreating(true);
    setEditingNote(null);
    resetForm();
  };

  const handleEdit = (note) => {
    setEditingNote(note);
    setIsCreating(false);
    setFormData({
      title: note.title,
      content: note.content,
      note_type: note.note_type,
      is_public: note.is_public,
      tags: note.tags?.join(", ") || "",
    });
  };

  const handleCancel = () => {
    setIsCreating(false);
    setEditingNote(null);
    resetForm();
  };

  const handleSave = async (e) => {
    e.preventDefault();

    const noteData = {
      title: formData.title.trim(),
      content: formData.content,
      note_type: formData.note_type,
      is_public: formData.is_public,
      tags: formData.tags
        .split(",")
        .map((t) => t.trim())
        .filter((t) => t),
    };

    try {
      if (editingNote) {
        await api.updateNote(editingNote.id, noteData);
      } else {
        await api.createNote({ ...noteData, campaign_id: campaignId });
      }
      await loadNotes();
      handleCancel();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (noteId) => {
    if (!confirm("Are you sure you want to delete this note?")) return;

    try {
      await api.deleteNote(noteId);
      await loadNotes();
    } catch (err) {
      setError(err.message);
    }
  };

  const toggleExpand = (noteId) => {
    setExpandedNoteId(expandedNoteId === noteId ? null : noteId);
  };

  const formatDate = (dateString) => {
    if (!dateString) return "";
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getNoteTypeLabel = (type) => {
    const found = NOTE_TYPES.find((t) => t.value === type);
    return found ? found.label : type;
  };

  if (loading && notes.length === 0) {
    return (
      <div className="notes-section">
        <div className="notes-loading">Loading notes...</div>
      </div>
    );
  }

  return (
    <div className="notes-section">
      <div className="notes-header">
        <h3>Campaign Notes</h3>
        <div className="notes-controls">
          <select
            className="notes-filter"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
          >
            <option value="">All Types</option>
            {NOTE_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
          <button className="btn btn-primary btn-sm" onClick={handleCreate}>
            + New Note
          </button>
        </div>
      </div>

      {error && <div className="notes-error">{error}</div>}

      {/* Note Form */}
      {(isCreating || editingNote) && (
        <form className="note-form" onSubmit={handleSave}>
          <input
            type="text"
            className="note-title-input"
            placeholder="Note title..."
            value={formData.title}
            onChange={(e) =>
              setFormData({ ...formData, title: e.target.value })
            }
            required
          />

          <textarea
            className="note-content-input"
            placeholder="Write your note here... (Markdown supported)"
            value={formData.content}
            onChange={(e) =>
              setFormData({ ...formData, content: e.target.value })
            }
            rows={6}
          />

          <div className="note-form-row">
            <select
              className="note-type-select"
              value={formData.note_type}
              onChange={(e) =>
                setFormData({ ...formData, note_type: e.target.value })
              }
            >
              {NOTE_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>

            <input
              type="text"
              className="note-tags-input"
              placeholder="Tags (comma-separated)"
              value={formData.tags}
              onChange={(e) =>
                setFormData({ ...formData, tags: e.target.value })
              }
            />

            <label className="note-public-toggle">
              <input
                type="checkbox"
                checked={formData.is_public}
                onChange={(e) =>
                  setFormData({ ...formData, is_public: e.target.checked })
                }
              />
              <span>Public</span>
            </label>
          </div>

          <div className="note-form-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleCancel}
            >
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              {editingNote ? "Update" : "Create"}
            </button>
          </div>
        </form>
      )}

      {/* Notes List */}
      <div className="notes-list">
        {notes.length === 0 ? (
          <div className="no-notes">
            No notes yet. Create one to get started!
          </div>
        ) : (
          notes.map((note) => (
            <div
              key={note.id}
              className={`note-card ${expandedNoteId === note.id ? "expanded" : ""}`}
            >
              <div
                className="note-card-header"
                onClick={() => toggleExpand(note.id)}
              >
                <div className="note-card-info">
                  <span className="note-title">{note.title}</span>
                  <span className="note-meta">
                    <span className="note-type-badge">
                      {getNoteTypeLabel(note.note_type)}
                    </span>
                    {note.is_public && (
                      <span className="note-public-badge">Public</span>
                    )}
                    <span className="note-author">
                      by {note.author_username}
                    </span>
                  </span>
                </div>
                <span className="note-expand-icon">
                  {expandedNoteId === note.id ? "▼" : "▶"}
                </span>
              </div>

              {expandedNoteId === note.id && (
                <div className="note-card-body">
                  <div className="note-content">
                    {note.content || <em className="no-content">No content</em>}
                  </div>

                  {note.tags && note.tags.length > 0 && (
                    <div className="note-tags">
                      {note.tags.map((tag, idx) => (
                        <span key={idx} className="note-tag">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="note-footer">
                    <span className="note-date">
                      {formatDate(note.created_at)}
                    </span>
                    {note.user_id === user?.id && (
                      <div className="note-actions">
                        <button
                          className="btn-icon"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEdit(note);
                          }}
                          title="Edit"
                        >
                          ✏️
                        </button>
                        <button
                          className="btn-icon btn-danger"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(note.id);
                          }}
                          title="Delete"
                        >
                          🗑️
                        </button>
                      </div>
                    )}
                    {user?.is_dm && note.user_id !== user?.id && (
                      <div className="note-actions">
                        <button
                          className="btn-icon btn-danger"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(note.id);
                          }}
                          title="Delete (DM)"
                        >
                          🗑️
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
