import os
import numpy as np
import pandas as pd
import requests
from collections import defaultdict

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# ── Constants (must match train_models.py) ────────────────────────────────────
HIDDEN      = 128
NUM_LAYERS  = 2
NUM_CLASSES = 3
SEQ_LEN     = 3
DROPOUT     = 0.3
ACTION_MAP      = {"view": 0, "click": 1, "add_to_cart": 2}
IDX_TO_ACTION   = {0: "view", 1: "click", 2: "add_to_cart"}

COMMENT_SERVICE_URL = os.environ.get("COMMENT_SERVICE_URL", "http://comment-rate-service:8000")
BOOK_SERVICE_URL    = os.environ.get("BOOK_SERVICE_URL",    "http://book-service:8000")
NEO4J_URI           = os.environ.get("NEO4J_URI",           "bolt://neo4j:7687")
NEO4J_USER          = os.environ.get("NEO4J_USER",          "neo4j")
NEO4J_PASSWORD      = os.environ.get("NEO4J_PASSWORD",      "bookstore123")
ANTHROPIC_API_KEY   = os.environ.get("ANTHROPIC_API_KEY",   "")

# ── PyTorch model definitions (mirror train_models.py) ───────────────────────
if TORCH_AVAILABLE:
    def _head(in_dim):
        return nn.Sequential(
            nn.LayerNorm(in_dim),
            nn.Dropout(DROPOUT),
            nn.Linear(in_dim, NUM_CLASSES),
        )

    class RNNModel(nn.Module):
        name = "RNN"
        def __init__(self):
            super().__init__()
            self.rnn  = nn.RNN(2, HIDDEN, NUM_LAYERS, batch_first=True,
                               dropout=DROPOUT if NUM_LAYERS > 1 else 0.0)
            self.head = _head(HIDDEN)
        def forward(self, x):
            out, _ = self.rnn(x)
            return self.head(out[:, -1])

    class LSTMModel(nn.Module):
        name = "LSTM"
        def __init__(self):
            super().__init__()
            self.lstm = nn.LSTM(2, HIDDEN, NUM_LAYERS, batch_first=True,
                                dropout=DROPOUT if NUM_LAYERS > 1 else 0.0)
            self.head = _head(HIDDEN)
        def forward(self, x):
            out, _ = self.lstm(x)
            return self.head(out[:, -1])

    class BiLSTMModel(nn.Module):
        name = "BiLSTM"
        def __init__(self):
            super().__init__()
            self.bilstm = nn.LSTM(2, HIDDEN, NUM_LAYERS, batch_first=True,
                                  bidirectional=True,
                                  dropout=DROPOUT if NUM_LAYERS > 1 else 0.0)
            self.head = _head(HIDDEN * 2)
        def forward(self, x):
            out, _ = self.bilstm(x)
            return self.head(out[:, -1])

    _MODEL_CLASSES = {"RNN": RNNModel, "LSTM": LSTMModel, "BiLSTM": BiLSTMModel}

# ── Lazy singletons ───────────────────────────────────────────────────────────
_model        = None
_model_name   = None
_model_loaded = False
_df           = None
_prod_map     = None
_all_prods    = None
_neo4j_driver = None
_pid_title_map = None   # {pid: book_title} — built once, covers all 200 product IDs


def _get_model():
    global _model, _model_name, _model_loaded
    if _model_loaded:
        return _model, _model_name
    _model_loaded = True
    if not TORCH_AVAILABLE:
        return None, None
    try:
        base      = os.path.dirname(os.path.abspath(__file__))
        ckpt_path = os.path.join(base, "..", "models", "model_best.pt")
        ckpt      = torch.load(ckpt_path, map_location="cpu", weights_only=False)
        name      = ckpt["name"]
        m         = _MODEL_CLASSES[name]()
        m.load_state_dict(ckpt["state_dict"])
        m.eval()
        _model, _model_name = m, name
        print(f"[recommender] Loaded model: {name}")
    except Exception as e:
        print(f"[recommender] Model load failed: {e}")
    return _model, _model_name


def _get_data():
    global _df, _prod_map, _all_prods
    if _df is not None:
        return _df, _prod_map, _all_prods
    candidates = [
        "/app/data_user500.csv",
        os.path.join(os.path.dirname(__file__), "..", "..", "data_user500.csv"),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                df       = pd.read_csv(path, parse_dates=["timestamp"])
                df       = df.sort_values(["user_id", "timestamp"]).reset_index(drop=True)
                df["act"] = df["action"].map(ACTION_MAP)
                prods    = sorted(df["product_id"].unique())
                prod_map = {p: i / max(len(prods) - 1, 1) for i, p in enumerate(prods)}
                df["prod_norm"] = df["product_id"].map(prod_map)
                _df, _prod_map, _all_prods = df, prod_map, prods
                print(f"[recommender] Dataset loaded: {len(df)} rows, {len(prods)} products")
                return _df, _prod_map, _all_prods
            except Exception as e:
                print(f"[recommender] Data load failed ({path}): {e}")
    return None, {}, []


def _get_pid_title_map() -> dict:
    """
    Build a {product_id: book_title} map covering every PID in the dataset.
    Cycles through available books if PIDs outnumber books (200 PIDs, 120 books).
    Result is cached for the lifetime of the process.
    """
    global _pid_title_map
    if _pid_title_map is not None:
        return _pid_title_map

    _, _, all_prods = _get_data()
    if not all_prods:
        _pid_title_map = {}
        return _pid_title_map

    try:
        r = requests.get(
            f"{BOOK_SERVICE_URL}/api/books/",
            params={"limit": 500},
            timeout=10,
        )
        books = r.json()
        if isinstance(books, dict):
            books = books.get("results", [])
    except Exception as e:
        print(f"[pid_map] book fetch failed: {e}")
        _pid_title_map = {}
        return _pid_title_map

    if not books:
        _pid_title_map = {}
        return _pid_title_map

    pids_sorted = sorted(all_prods)  # e.g. ['P0001', 'P0002', ..., 'P0200']
    mapping = {}
    for i, pid in enumerate(pids_sorted):
        book = books[i % len(books)]
        mapping[pid] = book.get("title") or pid
    _pid_title_map = mapping
    print(f"[pid_map] Built mapping for {len(mapping)} product IDs → {len(books)} books")
    return _pid_title_map


def _get_neo4j():
    global _neo4j_driver
    if _neo4j_driver is not None or not NEO4J_AVAILABLE:
        return _neo4j_driver
    try:
        _neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        _neo4j_driver.verify_connectivity()
        print("[recommender] Neo4j connected")
    except Exception as e:
        print(f"[recommender] Neo4j connection failed: {e}")
        _neo4j_driver = None
    return _neo4j_driver


# ── View 1: Collaborative Filtering (existing) ────────────────────────────────
class RecommendView(APIView):
    """Collaborative filtering using rating data from comment-rate-service."""

    def get(self, request):
        customer_id = request.query_params.get("customer_id")
        top_n       = int(request.query_params.get("top_n", 5))

        if not customer_id:
            return Response({"error": "customer_id is required"}, status=400)
        customer_id = int(customer_id)

        try:
            resp        = requests.get(f"{COMMENT_SERVICE_URL}/api/comments/all_ratings/", timeout=10)
            all_ratings = resp.json()
        except requests.RequestException:
            return Response({"error": "Failed to fetch ratings"}, status=503)

        if not all_ratings:
            return Response({"customer_id": customer_id, "recommendations": []})

        user_ratings = defaultdict(dict)
        for r in all_ratings:
            user_ratings[r["customer_id"]][r["book_id"]] = r["rating"]

        target = user_ratings.get(customer_id, {})
        if not target:
            return self._popular(all_ratings, top_n)

        scores, sim_sums = defaultdict(float), defaultdict(float)
        for other_id, other in user_ratings.items():
            if other_id == customer_id:
                continue
            common = set(target) & set(other)
            if not common:
                continue
            diff = sum(abs(target[b] - other[b]) for b in common) / len(common)
            sim  = max(0, 1 - diff / 5.0)
            if sim <= 0:
                continue
            for book_id, rating in other.items():
                if book_id not in target:
                    scores[book_id]   += sim * rating
                    sim_sums[book_id] += sim

        recs = sorted(
            [{"book_id": b, "predicted_rating": round(scores[b] / sim_sums[b], 2)}
             for b in scores if sim_sums[b] > 0],
            key=lambda x: x["predicted_rating"], reverse=True,
        )[:top_n]

        for rec in recs:
            try:
                r = requests.get(f"{BOOK_SERVICE_URL}/api/books/{rec['book_id']}/", timeout=5)
                if r.status_code == 200:
                    rec["book"] = r.json()
            except requests.RequestException:
                rec["book"] = None
        return Response({"customer_id": customer_id, "recommendations": recs})

    def _popular(self, all_ratings, top_n):
        book_scores = defaultdict(list)
        for r in all_ratings:
            book_scores[r["book_id"]].append(r["rating"])
        popular = sorted(
            [{"book_id": b, "predicted_rating": round(sum(v) / len(v), 2)}
             for b, v in book_scores.items()],
            key=lambda x: x["predicted_rating"], reverse=True,
        )[:top_n]
        for rec in popular:
            try:
                r = requests.get(f"{BOOK_SERVICE_URL}/api/books/{rec['book_id']}/", timeout=5)
                if r.status_code == 200:
                    rec["book"] = r.json()
            except requests.RequestException:
                rec["book"] = None
        return Response({"customer_id": None, "recommendations": popular})


# ── View 2: RNN/LSTM/BiLSTM Model-Based Recommendations ──────────────────────
class ModelRecommendView(APIView):
    """
    Uses the trained best model (RNN/LSTM/BiLSTM) from model_best.pt.
    Predicts the user's likely next action from their recent behavior sequence,
    then scores books from the catalog accordingly.
    """

    def get(self, request):
        user_id = request.query_params.get("user_id", "")
        top_n   = int(request.query_params.get("top_n", 6))

        model, model_name = _get_model()
        df, prod_map, all_prods = _get_data()

        prediction = None
        probs      = None
        recent_seq = []

        # ── Build sequence from user's recent behavior ────────────────────
        if df is not None and user_id:
            user_df = df[df["user_id"] == user_id].tail(SEQ_LEN)
            if len(user_df) >= SEQ_LEN and model is not None:
                seq = np.array(
                    [[row["prod_norm"], row["act"] / 2.0]
                     for _, row in user_df.iterrows()],
                    dtype=np.float32,
                )
                with torch.no_grad():
                    logits  = model(torch.tensor(seq).unsqueeze(0))
                    probs_t = torch.softmax(logits, dim=1).squeeze().numpy()
                pred_idx   = int(probs_t.argmax())
                prediction = IDX_TO_ACTION[pred_idx]
                probs      = {IDX_TO_ACTION[i]: round(float(p), 4)
                              for i, p in enumerate(probs_t)}
                recent_seq = user_df[["product_id", "action"]].to_dict("records")

        # ── Fetch real books from book-service ────────────────────────────
        try:
            resp      = requests.get(f"{BOOK_SERVICE_URL}/api/books/", timeout=10,
                                     params={"limit": 50})
            data      = resp.json()
            all_books = data.get("results", data) if isinstance(data, dict) else data
        except requests.RequestException:
            all_books = []

        # ── Score books based on model prediction ─────────────────────────
        # Use add_to_cart probability as boost; sort by stock + price signals
        add_prob = probs.get("add_to_cart", 0.33) if probs else 0.33

        scored = []
        for book in all_books:
            base_score = add_prob + (1 / (1 + float(book.get("price", 100000)) / 100000))
            scored.append((base_score, book))

        scored.sort(key=lambda x: x[0], reverse=True)
        recommendations = [
            {"book": bk, "score": round(sc, 4)}
            for sc, bk in scored[:top_n]
        ]

        return Response({
            "user_id":               user_id or None,
            "model_used":            model_name or "unavailable",
            "predicted_next_action": prediction,
            "action_probabilities":  probs,
            "recent_sequence":       recent_seq,
            "recommendations":       recommendations,
        })


# ── View 3: RAG Chat using KB_Graph + Claude ──────────────────────────────────
class ChatView(APIView):
    """
    RAG chat: queries the Neo4j knowledge base graph for context,
    then uses Claude (or rule-based fallback) to generate a response.
    """

    def post(self, request):
        message = request.data.get("message", "").strip()
        user_id = request.data.get("user_id", "")
        history = request.data.get("history", [])

        if not message:
            return Response({"error": "message is required"}, status=400)

        context  = self._query_kb(message, user_id)
        reply    = self._generate(message, context, history)

        return Response({
            "reply":       reply,
            "kb_context":  context.get("summary", ""),
            "user_id":     user_id or None,
        })

    # ── Helpers ───────────────────────────────────────────────────────────
    def _resolve(self, pid: str) -> str:
        """Return book title for a product ID, never falls back to raw PID."""
        title = _get_pid_title_map().get(pid)
        return title if title else pid

    # ── KB Graph query ────────────────────────────────────────────────────
    def _query_kb(self, message: str, user_id: str) -> dict:
        driver = _get_neo4j()
        context = {}
        if not driver:
            return context

        msg_lower = message.lower()
        try:
            with driver.session() as session:
                # Top add_to_cart products
                r = session.run("""
                    MATCH (u:User)-[:ADDED_TO_CART]->(p:Product)
                    WITH p, count(*) AS cnt ORDER BY cnt DESC LIMIT 5
                    RETURN p.id AS product_id, cnt
                """)
                context["top_cart"] = [dict(rec) for rec in r]

                # Trending (most interactions)
                r = session.run("""
                    MATCH (u:User)-[]->(p:Product)
                    WITH p, count(*) AS cnt ORDER BY cnt DESC LIMIT 5
                    RETURN p.id AS product_id, cnt
                """)
                context["trending"] = [dict(rec) for rec in r]

                # User-specific behavior
                if user_id:
                    r = session.run("""
                        MATCH (u:User {id: $uid})-[rel]->(p:Product)
                        RETURN type(rel) AS action, p.id AS product_id
                        ORDER BY product_id LIMIT 10
                    """, uid=user_id)
                    context["user_history"] = [dict(rec) for rec in r]

                # Co-purchased products
                if any(w in msg_lower for w in ["cùng", "also", "together", "kết hợp"]):
                    r = session.run("""
                        MATCH (p1:Product)-[c:CO_PURCHASED_WITH]->(p2:Product)
                        RETURN p1.id AS prod1, p2.id AS prod2, c.count AS times
                        ORDER BY times DESC LIMIT 5
                    """)
                    context["co_purchased"] = [dict(rec) for rec in r]

        except Exception as e:
            print(f"[chat] Neo4j query error: {e}")
            context["summary"] = "KB Graph không khả dụng"
            return context

        # ── Resolve product IDs → book titles (uses cached map) ──────────
        top_names = [self._resolve(x["product_id"]) for x in context.get("top_cart", [])]
        context["summary"] = (
            f"Sách được thêm vào giỏ nhiều nhất: {', '.join(top_names)}"
            if top_names else "Chưa có dữ liệu KB Graph"
        )
        return context

    # ── Response generation ───────────────────────────────────────────────
    def _generate(self, message: str, context: dict, history: list) -> str:
        system = self._build_system(context)
        if ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY:
            return self._call_claude(message, system, history)
        return self._rule_based(message, context)

    def _build_system(self, context: dict) -> str:
        lines = [
            "Bạn là trợ lý tư vấn sách thông minh của BookStore.",
            "Hãy tư vấn nhiệt tình, ngắn gọn bằng tiếng Việt.",
            "Khi gợi ý sách, hãy dùng tên sách, không dùng mã sản phẩm.",
            "",
            "Dữ liệu từ Knowledge Base Graph:",
        ]
        if context.get("top_cart"):
            titles = [self._resolve(x["product_id"]) for x in context["top_cart"]]
            lines.append(f"- Sách được thêm vào giỏ nhiều nhất: {', '.join(titles)}")
        if context.get("trending"):
            titles = [self._resolve(x["product_id"]) for x in context["trending"]]
            lines.append(f"- Sách hot (nhiều tương tác): {', '.join(titles)}")
        if context.get("user_history"):
            acts = context["user_history"][:3]
            pairs = [(a["action"], self._resolve(a["product_id"])) for a in acts]
            lines.append(f"- Lịch sử người dùng: {pairs}")
        if context.get("co_purchased"):
            pairs = [(self._resolve(x["prod1"]), self._resolve(x["prod2"]))
                     for x in context["co_purchased"][:3]]
            lines.append(f"- Sách thường mua cùng nhau: {pairs}")
        return "\n".join(lines)

    def _call_claude(self, message: str, system: str, history: list) -> str:
        try:
            client   = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            messages = []
            for h in history[-6:]:
                if h.get("role") in ("user", "assistant"):
                    messages.append({"role": h["role"], "content": h["content"]})
            messages.append({"role": "user", "content": message})

            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                system=system,
                messages=messages,
            )
            return resp.content[0].text
        except Exception as e:
            print(f"[chat] Claude API error: {e}")
            return self._rule_based(message, {})

    def _rule_based(self, message: str, context: dict) -> str:
        msg = message.lower()

        def top_titles(key, n=3):
            return [self._resolve(x["product_id"]) for x in context.get(key, [])[:n]]

        if any(w in msg for w in ["xin chào", "hello", "hi", "chào", "hey"]):
            return ("Xin chào! Tôi là trợ lý BookStore AI. "
                    "Tôi có thể gợi ý sách, tư vấn mua hàng và giải đáp thắc mắc. "
                    "Bạn cần hỗ trợ gì hôm nay?")

        if any(w in msg for w in ["gợi ý", "recommend", "suggest", "nên mua", "mua gì"]):
            titles = top_titles("top_cart")
            if titles:
                listing = ", ".join(f'"{t}"' for t in titles)
                return (f"Dựa trên dữ liệu hành vi mua sắm, tôi gợi ý: {listing}. "
                        f"Đây là những cuốn sách được thêm vào giỏ hàng nhiều nhất!")
            return "Hãy vào trang Sách để khám phá những cuốn sách phù hợp nhất với bạn!"

        if any(w in msg for w in ["hot", "trending", "nổi bật", "phổ biến", "bán chạy"]):
            titles = top_titles("trending")
            if titles:
                listing = ", ".join(f'"{t}"' for t in titles)
                return f"Những cuốn sách đang được quan tâm nhiều nhất: {listing}!"
            return "Hãy kiểm tra trang chủ để xem các sách hot nhất!"

        if any(w in msg for w in ["giỏ hàng", "cart", "thêm vào"]):
            return ("Để thêm sách vào giỏ hàng, bạn click vào nút 'Thêm vào giỏ' "
                    "trên trang chi tiết sản phẩm. Chúng tôi hỗ trợ thanh toán an toàn!")

        if any(w in msg for w in ["đơn hàng", "order", "giao hàng", "ship"]):
            return ("Bạn có thể theo dõi đơn hàng tại trang 'Đơn hàng của tôi'. "
                    "Thời gian giao hàng thường từ 2-5 ngày làm việc.")

        if any(w in msg for w in ["giá", "price", "rẻ", "discount", "giảm giá"]):
            return ("Chúng tôi thường xuyên có chương trình ưu đãi! "
                    "Hãy kiểm tra trang Sách và lọc theo giá để tìm sách phù hợp ngân sách.")

        return ("Cảm ơn bạn đã liên hệ BookStore! "
                "Tôi có thể giúp bạn tìm sách, gợi ý sản phẩm hot, hoặc hỗ trợ đơn hàng. "
                "Bạn muốn hỏi về điều gì?")
