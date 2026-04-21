import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { FiChevronLeft, FiChevronRight, FiZap } from "react-icons/fi";
import { recommendationService } from "../services";
import { useCart } from "../context/CartContext";

export default function RecommendationSection({ userId, title = "Gợi ý cho bạn", context = "search" }) {
  const [recs, setRecs]         = useState([]);
  const [meta, setMeta]         = useState(null);
  const [loading, setLoading]   = useState(true);
  const { addItem }             = useCart();
  const scrollRef               = useRef(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    recommendationService
      .getModelRecommendations(userId, 8)
      .then((res) => {
        if (!cancelled) {
          const data = res.data;
          setRecs(data.recommendations || []);
          setMeta({
            model:      data.model_used,
            prediction: data.predicted_next_action,
            probs:      data.action_probabilities,
          });
        }
      })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [userId]);

  const scroll = (dir) => {
    scrollRef.current?.scrollBy({ left: dir * 220, behavior: "smooth" });
  };

  const formatPrice = (p) =>
    new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(p);

  if (loading) {
    return (
      <div className="my-8">
        <h2 className="text-xl font-bold text-gray-800 mb-4">{title}</h2>
        <div className="flex gap-4 overflow-hidden">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="w-44 flex-shrink-0 bg-white rounded-xl shadow-sm animate-pulse">
              <div className="h-48 bg-gray-200 rounded-t-xl" />
              <div className="p-3 space-y-2">
                <div className="h-3 bg-gray-200 rounded" />
                <div className="h-3 bg-gray-200 rounded w-2/3" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!recs.length) return null;

  const ACTION_LABEL = {
    add_to_cart: "Bạn có thể muốn mua",
    click:       "Bạn có thể muốn xem",
    view:        "Khám phá thêm",
  };

  return (
    <div className="my-8">
      {/* Section header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <FiZap className="text-primary-500" />
            {title}
          </h2>
          {meta && (
            <p className="text-xs text-gray-500 mt-0.5">
              Model AI: <span className="font-semibold text-primary-600">{meta.model}</span>
              {meta.prediction && (
                <> · Dự đoán: <span className="text-green-600">{ACTION_LABEL[meta.prediction] || meta.prediction}</span></>
              )}
              {meta.probs && (
                <> · Mua: {Math.round((meta.probs.add_to_cart || 0) * 100)}%</>
              )}
            </p>
          )}
        </div>
        <div className="flex gap-1">
          <button
            onClick={() => scroll(-1)}
            className="p-1.5 rounded-full border border-gray-200 hover:bg-gray-100 transition-colors"
          >
            <FiChevronLeft className="w-4 h-4 text-gray-600" />
          </button>
          <button
            onClick={() => scroll(1)}
            className="p-1.5 rounded-full border border-gray-200 hover:bg-gray-100 transition-colors"
          >
            <FiChevronRight className="w-4 h-4 text-gray-600" />
          </button>
        </div>
      </div>

      {/* Horizontal scroll cards */}
      <div
        ref={scrollRef}
        className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide"
        style={{ scrollbarWidth: "none" }}
      >
        {recs.map((rec, i) => {
          const book = rec.book;
          if (!book) return null;
          return (
            <div
              key={i}
              className="w-44 flex-shrink-0 bg-white rounded-xl shadow-sm hover:shadow-md
                         transition-shadow border border-gray-100 flex flex-col"
            >
              <Link to={`/books/${book.id}`} className="block">
                <div className="h-48 bg-gradient-to-br from-primary-50 to-primary-100 rounded-t-xl overflow-hidden">
                  {book.image_url ? (
                    <img src={book.image_url} alt={book.title}
                         className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-4xl">📚</div>
                  )}
                </div>
                <div className="p-3">
                  <p className="text-sm font-semibold text-gray-800 line-clamp-2 leading-snug">
                    {book.title}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">{book.author}</p>
                  <p className="text-sm font-bold text-primary-600 mt-1">
                    {formatPrice(book.price)}
                  </p>
                </div>
              </Link>
              <div className="px-3 pb-3 mt-auto">
                <button
                  onClick={() => addItem(book.id)}
                  disabled={book.stock === 0}
                  className="w-full text-xs py-1.5 rounded-lg bg-primary-600 text-white
                             hover:bg-primary-700 disabled:opacity-50 transition-colors"
                >
                  {book.stock === 0 ? "Hết hàng" : "Thêm vào giỏ"}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
