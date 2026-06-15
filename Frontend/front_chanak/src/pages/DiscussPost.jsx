import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { MessageCircle, ArrowUp } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { discussAPI } from "../utils/apiClient";
import { parseBoldText } from "../components/ResponseFormatter";

function DiscussPost() {
  const { id } = useParams();
  const { isAuthenticated } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [replyBody, setReplyBody] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [upvoting, setUpvoting] = useState(false);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    discussAPI
      .get(id)
      .then((res) => {
        if (!cancelled) setData(res.data);
      })
      .catch((err) => {
        if (!cancelled)
          setError(err.response?.data?.detail || "Failed to load post.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  const refreshPost = () => {
    if (!id) return;
    discussAPI.get(id).then((res) => setData(res.data)).catch(() => { });
  };

  const handleUpvote = () => {
    if (!id || upvoting) return;
    setUpvoting(true);
    discussAPI
      .upvote(id)
      .then(() => refreshPost())
      .finally(() => setUpvoting(false));
  };

  const handleReply = (e) => {
    e.preventDefault();
    if (!id || !replyBody.trim() || submitting) return;

    // Check if the reply starts with @chanakya
    const isChanakya = replyBody.trim().toLowerCase().startsWith("@chanakya");

    setSubmitting(true);

    const apiCall = isChanakya
      ? discussAPI.askChanakya(id, replyBody.trim())
      : discussAPI.createReply(id, replyBody.trim());

    apiCall
      .then(() => {
        setReplyBody("");
        refreshPost();
      })
      .catch((err) => {
        console.error("Failed to post reply:", err);
        alert(err.response?.data?.detail || "Failed to post reply");
      })
      .finally(() => setSubmitting(false));
  };

  if (loading) {
    return (
      <div className="bg-[#FFFFFF] min-h-screen px-4 md:px-8 py-6 md:py-10">
        <div className="max-w-4xl mx-auto">
          <p className="text-[#6B7280]">Loading…</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-[#FFFFFF] min-h-screen px-4 md:px-8 py-6 md:py-10">
        <div className="max-w-4xl mx-auto">
          <Link
            to="/discuss"
            className="inline-block mb-4 text-sm font-bold text-[#000000] no-underline hover:underline"
          >
            ← Back to Discuss
          </Link>
          <p className="p-3 border-2 border-[#000000] bg-[#FEE2E2] text-[#000000]">
            {error || "Post not found."}
          </p>
        </div>
      </div>
    );
  }

  const { post, replies } = data;

  return (
    <div className="bg-[#FFFFFF] min-h-screen px-4 md:px-8 py-6 md:py-10">
      <div className="max-w-6xl mx-auto">
        <Link
          to="/discuss"
          className="inline-block mb-4 text-sm font-bold text-[#000000] no-underline hover:underline"
        >
          ← Back to Discuss
        </Link>
        <article className="border-2 border-[#000000] bg-[#FFFFFF] p-4 md:p-6 shadow-[4px_4px_0px_0px_#000000]">
          <div className="flex gap-3 mb-4">
            <div className="w-10 h-10 md:w-12 md:h-12 rounded-full border-2 border-[#000000] bg-[#60A5FA] flex items-center justify-center font-bold text-sm text-white shrink-0">
              {post.author_name?.slice(0, 2).toUpperCase() ?? "?"}
            </div>
            <div>
              <p className="font-bold text-[#000000]">{post.author_name}</p>
              {post.location && (
                <p className="text-sm text-[#6B7280]">{post.location}</p>
              )}
            </div>
          </div>
          <h1 className="font-bold text-lg md:text-xl mb-3">{post.body}</h1>
          <div className="flex flex-wrap gap-3 text-sm text-[#374151] mb-3">
            <span className="flex items-center gap-1">
              <MessageCircle size={14} /> {post.reply_count} Answers
            </span>
            <button
              type="button"
              onClick={handleUpvote}
              disabled={!isAuthenticated || upvoting}
              className="flex items-center gap-1 border-0 bg-transparent p-0 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed hover:underline"
            >
              <ArrowUp size={14} /> {post.upvote_count} Votes
            </button>
          </div>
          <div className="flex flex-wrap gap-1.5 mb-4">
            {(post.tags || []).map((tag) => (
              <span
                key={tag}
                className="px-2 py-0.5 text-xs font-medium border-2 border-[#000000] bg-[#FDE047] text-[#000000]"
              >
                {tag}
              </span>
            ))}
          </div>

          {replies && replies.length > 0 && (
            <div className="border-t-2 border-[#000000] pt-4 space-y-3">
              <p className="font-bold text-[#000000]">Replies</p>
              {replies.map((r) => {
                const isChanakya = r.author_id === "chanakya_ai";
                return (
                  <div
                    key={r.id}
                    className={`p-3 border-2 border-[#000000] ${isChanakya
                      ? "bg-[#A7F3D0] border-[#000000]"
                      : "bg-[#BFDBFE]"
                      }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <p className="font-bold text-sm text-[#000000]">
                        {isChanakya ? "Chanakya AI" : r.author_name}
                      </p>
                      {isChanakya && (
                        <span className="px-2 py-0.5 text-xs font-medium border-2 border-[#000000] bg-[#34D399] text-white rounded">
                          AI Assistant
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-[#374151] mt-1 whitespace-pre-wrap">{parseBoldText(r.body)}</p>
                  </div>
                );
              })}
            </div>
          )}

          {isAuthenticated && (
            <form onSubmit={handleReply} className="mt-4 pt-4 border-t-2 border-[#000000]">
              <label htmlFor="reply-body" className="block font-bold text-sm mb-2">
                Reply
              </label>
              <textarea
                id="reply-body"
                value={replyBody}
                onChange={(e) => setReplyBody(e.target.value)}
                placeholder="Write your reply… (Tip: Start with @chanakya to get AI assistance)"
                rows={3}
                className="w-full p-3 border-2 border-[#000000] bg-[#FFFFFF] text-[#000000] resize-y"
              />
              {replyBody.trim().toLowerCase().startsWith("@chanakya") && (
                <div className="mt-2 p-2 bg-[#A7F3D0] border-2 border-[#000000] text-sm">
                  <p className="font-medium text-[#000000]">
                    🤖 Chanakya AI will respond to your query with the conversation context
                  </p>
                </div>
              )}
              <button
                type="submit"
                disabled={!replyBody.trim() || submitting}
                className="mt-2 px-4 py-2 bg-[#FDE047] border-2 border-[#000000] font-bold text-[#000000] disabled:opacity-50 disabled:cursor-not-allowed shadow-[3px_3px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] transition-all"
              >
                {submitting ? "Sending…" : "Post reply"}
              </button>
            </form>
          )}
        </article>
      </div>
    </div>
  );
}

export default DiscussPost;
