import { useRef, useState } from "react";
import "./CharacterPortrait.css";

export default function CharacterPortrait({
  character,
  onUpdateCharacter,
  size = "large",
  editable = true,
}) {
  const fileInputRef = useRef(null);
  const [isUploading, setIsUploading] = useState(false);

  const getInitials = (name) => {
    return name
      .split(" ")
      .map((word) => word.charAt(0).toUpperCase())
      .slice(0, 2)
      .join("");
  };

  const handleClick = () => {
    if (editable && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith("image/")) {
      alert("Please select an image file");
      return;
    }

    // Validate file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      alert("Image must be less than 2MB");
      return;
    }

    setIsUploading(true);

    try {
      // Convert to base64
      const reader = new FileReader();
      reader.onload = async (event) => {
        const base64 = event.target.result;

        // Resize image if needed (max 200x200 for storage efficiency)
        const resized = await resizeImage(base64, 200, 200);

        await onUpdateCharacter(character.id, { avatar_url: resized });
        setIsUploading(false);
      };
      reader.onerror = () => {
        alert("Error reading file");
        setIsUploading(false);
      };
      reader.readAsDataURL(file);
    } catch (error) {
      console.error("Error uploading portrait:", error);
      setIsUploading(false);
    }

    // Reset input so same file can be selected again
    e.target.value = "";
  };

  const resizeImage = (base64, maxWidth, maxHeight) => {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        let { width, height } = img;

        // Calculate new dimensions maintaining aspect ratio
        if (width > height) {
          if (width > maxWidth) {
            height = (height * maxWidth) / width;
            width = maxWidth;
          }
        } else {
          if (height > maxHeight) {
            width = (width * maxHeight) / height;
            height = maxHeight;
          }
        }

        // Create canvas and draw resized image
        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0, width, height);

        // Return as JPEG for smaller file size
        resolve(canvas.toDataURL("image/jpeg", 0.8));
      };
      img.src = base64;
    });
  };

  const handleRemovePortrait = async (e) => {
    e.stopPropagation();
    await onUpdateCharacter(character.id, { avatar_url: null });
  };

  return (
    <div
      className={`character-portrait portrait-${size} ${editable ? "editable" : ""} ${isUploading ? "uploading" : ""}`}
      onClick={handleClick}
      title={editable ? "Click to change portrait" : character.name}
    >
      {character.avatar_url ? (
        <>
          <img
            src={character.avatar_url}
            alt={character.name}
            className="portrait-image"
          />
          {editable && (
            <button
              className="portrait-remove"
              onClick={handleRemovePortrait}
              title="Remove portrait"
            >
              ✕
            </button>
          )}
        </>
      ) : (
        <div className="portrait-initials">{getInitials(character.name)}</div>
      )}

      {isUploading && <div className="portrait-loading">...</div>}

      {editable && !isUploading && (
        <div className="portrait-overlay">
          <span className="portrait-hint">📷</span>
        </div>
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        className="portrait-input"
      />
    </div>
  );
}
