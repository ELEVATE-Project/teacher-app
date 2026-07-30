import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { discussAPI } from "../utils/apiClient";

function DiscussNew() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [body, setBody] = useState("");
  const [location, setLocation] = useState("");
  const [tagsStr, setTagsStr] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  if (!isAuthenticated) {
    return (
      <div className="bg-[#FFFFFF] min-h-screen px-4 md:px-8 py-6 md:py-10">
        <div className="max-w-4xl mx-auto">
          <p className="mb-4 text-[#6B7280]">Please log in to ask a question.</p>
          <Link
            to="/login"
            className="inline-block px-4 py-2 bg-[#FDE047] border-2 border-[#000000] font-bold text-[#000000] no-underline"
          >
            Log in
          </Link>
        </div>
      </div>
    );
  }

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!body.trim() || submitting) return;
    setError(null);
    setSubmitting(true);
    const tags = tagsStr
      .split(/[\s,]+/)
      .map((t) => t.trim())
      .filter(Boolean)
      .slice(0, 20);
    discussAPI
      .createPost(body.trim(), location.trim() || null, tags)
      .then((res) => {
        navigate(`/discuss/${res.data.id}`);
      })
      .catch((err) => {
        setError(err.response?.data?.detail || "Failed to create post.");
      })
      .finally(() => setSubmitting(false));
  };

  return (
    <div className="bg-[#FFFFFF] min-h-screen px-4 md:px-8 py-6 md:py-10">
      <div className="max-w-4xl mx-auto">
        <Link
          to="/discuss"
          className="inline-block mb-4 text-sm font-bold text-[#000000] no-underline hover:underline"
        >
          ← Back to Discuss
        </Link>
        <h1 className="text-2xl md:text-3xl font-bold text-[#000000] mb-6">
          Ask a question
        </h1>
        {error && (
          <p className="mb-4 p-3 border-2 border-[#000000] bg-[#FEE2E2] text-[#000000] text-sm">
            {error}
          </p>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="body" className="block font-bold text-[#000000] mb-2">
              Question
            </label>
            <textarea
              id="body"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="What would you like to ask?"
              rows={5}
              required
              className="w-full p-3 border-2 border-[#000000] bg-[#FFFFFF] text-[#000000] resize-y"
            />
          </div>
          <div>
            <label htmlFor="location" className="block font-bold text-[#000000] mb-2">
              Location (optional)
            </label>
            <input
              id="location"
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. Mumbai"
              className="w-full p-3 border-2 border-[#000000] bg-[#FFFFFF] text-[#000000]"
            />
          </div>
          <div>
            <label htmlFor="tags" className="block font-bold text-[#000000] mb-2">
              Tags (optional, comma or space separated)
            </label>
            <input
              id="tags"
              type="text"
              value={tagsStr}
              onChange={(e) => setTagsStr(e.target.value)}
              placeholder="e.g. teaching, curriculum"
              className="w-full p-3 border-2 border-[#000000] bg-[#FFFFFF] text-[#000000]"
            />
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={!body.trim() || submitting}
              className="px-4 py-2 bg-[#FDE047] border-2 border-[#000000] font-bold text-[#000000] disabled:opacity-50 disabled:cursor-not-allowed shadow-[3px_3px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] transition-all"
            >
              {submitting ? "Posting…" : "Post question"}
            </button>
            <Link
              to="/discuss"
              className="px-4 py-2 border-2 border-[#000000] bg-[#FFFFFF] font-bold text-[#000000] no-underline hover:bg-[#F3F4F6] transition-colors"
            >
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}

export default DiscussNew;
