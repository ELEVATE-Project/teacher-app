import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { MessageCircle, ArrowUp } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { discussAPI } from "../utils/apiClient";

const POSTS_PER_PAGE = 8;

// Lighter vibrant palettes for post cards
const POST_CARD_COLORS = [
  "#FDE68A", // light amber
  "#BFDBFE", // light blue
  "#A7F3D0", // light green
  "#DDD6FE", // light violet
  "#FBCFE8", // light pink
  "#FED7AA", // light orange
  "#FECACA", // light coral
  "#FEF08A", // light yellow
];

function Discuss() {
  const { isAuthenticated } = useAuth();
  const [currentPage, setCurrentPage] = useState(1);
  const [posts, setPosts] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const skip = (currentPage - 1) * POSTS_PER_PAGE;
  const totalPages = Math.max(1, Math.ceil(total / POSTS_PER_PAGE));

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    discussAPI
      .list(skip, POSTS_PER_PAGE)
      .then((res) => {
        if (!cancelled) {
          setPosts(res.data.posts || []);
          setTotal(res.data.total ?? 0);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.response?.data?.detail || "Failed to load posts.");
          setPosts([]);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [skip]);

  return (
    <div className="bg-[#FFFFFF] min-h-screen px-4 md:px-8 py-6 md:py-10" >
      <div className="max-w-4xl mx-auto">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <h1 className="text-2xl md:text-3xl font-bold text-[#000000]">
            Discuss
          </h1>
          {isAuthenticated && (
            <Link
              to="/discuss/new"
              className="px-4 md:px-6 py-2 bg-[#FDE047] border-2 border-[#000000] font-bold text-[#000000] no-underline shadow-[4px_4px_0px_0px_#000000] hover:shadow-[2px_2px_0px_0px_#000000] hover:translate-x-1 hover:translate-y-1 transition-all text-sm md:text-base"
            >
              Ask question
            </Link>
          )}
        </div>

        {error && (
          <p className="mb-4 p-3 border-2 border-[#000000] bg-[#FEE2E2] text-[#000000] text-sm">
            {error}
          </p>
        )}

        {loading ? (
          <p className="py-8 text-[#6B7280]">Loading…</p>
        ) : (
          <>
            <ul className="space-y-4 list-none p-0 m-0">
              {posts.length === 0 && !error ? (
                <li className="p-6 text-[#6B7280]">No posts yet. Ask a question!</li>
              ) : (
                posts.map((post, index) => (
                  <li key={post.id}>
                    <Link
                      to={`/discuss/${post.id}`}
                      className="flex gap-3 md:gap-4 p-4 md:p-5 transition-colors no-underline text-[#000000] hover:brightness-95 border-2 border-[#000000] rounded-lg"
                      style={{
                        backgroundColor: POST_CARD_COLORS[index % POST_CARD_COLORS.length],
                      }}
                    >
                      <div className="shrink-0 w-10 h-10 md:w-12 md:h-12 rounded-full border-2 border-[#000000] bg-[#60A5FA] flex items-center justify-center font-bold text-sm text-white">
                        {post.author_name
                          ?.split(" ")
                          .map((n) => n[0])
                          .join("")
                          .slice(0, 2)
                          .toUpperCase() ?? "?"}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h2 className="font-bold text-base md:text-lg mb-2 line-clamp-2">
                          {post.body}
                        </h2>
                        <div className="flex flex-wrap items-center gap-3 md:gap-4 text-sm text-[#374151] mb-2">
                          <span className="flex items-center gap-1">
                            <MessageCircle size={14} />
                            {post.reply_count} Answers
                          </span>
                          <span className="flex items-center gap-1">
                            <ArrowUp size={14} />
                            {post.upvote_count} Votes
                          </span>
                          {post.location && (
                            <span className="text-[#6B7280]">{post.location}</span>
                          )}
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {(post.tags || []).map((tag) => (
                            <span
                              key={tag}
                              className="px-2 py-0.5 text-xs font-medium border-2 border-[#000000] bg-[#FDE047] text-[#000000]"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    </Link>
                  </li>
                ))
              )}
            </ul>

            {totalPages > 1 && (
              <div className="flex flex-wrap items-center justify-center gap-2 mt-6">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((n) => (
                  <button
                    key={n}
                    type="button"
                    onClick={() => setCurrentPage(n)}
                    className={
                      currentPage === n
                        ? "w-9 h-9 border-2 border-[#000000] bg-[#A7F3D0] font-bold text-[#000000] shadow-[3px_3px_0px_0px_#000000]"
                        : "w-9 h-9 border-2 border-[#000000] bg-[#FFFFFF] font-bold text-[#000000] hover:bg-[#F3F4F6] transition-colors"
                    }
                  >
                    {n}
                  </button>
                ))}
                <button
                  type="button"
                  onClick={() =>
                    setCurrentPage((p) => (p < totalPages ? p + 1 : p))
                  }
                  disabled={currentPage >= totalPages}
                  className="px-3 py-1.5 border-2 border-[#000000] bg-[#FFFFFF] font-bold text-[#000000] disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#F3F4F6] transition-colors"
                >
                  Next &gt;
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default Discuss;
