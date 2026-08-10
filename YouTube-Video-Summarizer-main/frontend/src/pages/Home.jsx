import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../api";

export function Home() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [url, setUrl] = useState("");
  const [method, setMethod] = useState("extractive");
  const [percentage, setPercentage] = useState(25);
  const [error, setError] = useState("");
  const [processing, setProcessing] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!url.startsWith("https://www.youtube.com/") && !url.startsWith("https://youtu.be/")) {
      setError("Please provide a valid YouTube URL");
      return;
    }

    setProcessing(true);
    try {
      const result = await api.processVideo(url, method, percentage);
      navigate("/results", { state: { url, method, percentage, result } });
    } catch (err) {
      setError(err.message);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="card">
      <div className="topbar">
        <span>Signed in as <strong>{user.username}</strong></span>
        <button className="link-btn" onClick={logout}>Log Out</button>
      </div>

      <h1>📊 YouTube Video Summarizer</h1>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="url">YouTube URL:</label>
          <input
            id="url"
            type="url"
            placeholder="https://www.youtube.com/watch?v=..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
          />
          <small>Enter a valid YouTube URL (supports both youtube.com and youtu.be formats)</small>
        </div>

        <div className="form-group">
          <label>Summarization Method:</label>
          <div className="method-options">
            <label className={`method-option ${method === "extractive" ? "selected" : ""}`}>
              <input
                type="radio"
                name="method"
                value="extractive"
                checked={method === "extractive"}
                onChange={() => setMethod("extractive")}
              />
              <strong>Extractive</strong>
              <span>Selects key sentences</span>
            </label>
            <label className={`method-option ${method === "abstractive" ? "selected" : ""}`}>
              <input
                type="radio"
                name="method"
                value="abstractive"
                checked={method === "abstractive"}
                onChange={() => setMethod("abstractive")}
              />
              <strong>Abstractive</strong>
              <span>Generates new text</span>
            </label>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="percentage">Summary Length:</label>
          <input
            id="percentage"
            type="range"
            min="10"
            max="50"
            value={percentage}
            onChange={(e) => setPercentage(Number(e.target.value))}
            className="slider"
            style={{ "--fill": `${((percentage - 10) / 40) * 100}%` }}
          />
          <p className="slider-value">{percentage}% of original length</p>
          <small>Lower values create shorter summaries, higher values preserve more detail</small>
        </div>

        {error && <p className="form-error">⚠️ {error}</p>}

        <button type="submit" className="submit-btn" disabled={processing}>
          {processing && <span className="spinner" />}
          {processing ? "Processing... this can take a while" : "📝 Generate Summary"}
        </button>
      </form>
    </div>
  );
}
