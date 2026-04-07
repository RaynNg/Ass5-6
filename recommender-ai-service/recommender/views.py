import os
import requests
from collections import defaultdict
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

COMMENT_SERVICE_URL = os.environ.get("COMMENT_SERVICE_URL", "http://comment-rate-service:8000")
BOOK_SERVICE_URL = os.environ.get("BOOK_SERVICE_URL", "http://book-service:8000")


class RecommendView(APIView):
    """
    AI-based book recommendation using collaborative filtering.
    Finds users with similar tastes and recommends books they liked.
    """

    def get(self, request):
        customer_id = request.query_params.get("customer_id")
        top_n = int(request.query_params.get("top_n", 5))

        if not customer_id:
            return Response({"error": "customer_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        customer_id = int(customer_id)

        # Step 1: Fetch all ratings from comment-rate-service
        try:
            resp = requests.get(f"{COMMENT_SERVICE_URL}/api/comments/all_ratings/", timeout=10)
            all_ratings = resp.json()
        except requests.RequestException:
            return Response({"error": "Failed to fetch ratings"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if not all_ratings:
            return Response({"customer_id": customer_id, "recommendations": []})

        # Step 2: Build user-item rating matrix
        user_ratings = defaultdict(dict)  # {user_id: {book_id: rating}}
        for r in all_ratings:
            user_ratings[r["customer_id"]][r["book_id"]] = r["rating"]

        target_ratings = user_ratings.get(customer_id, {})

        if not target_ratings:
            # No ratings yet — recommend top-rated books
            return self._recommend_popular(all_ratings, top_n)

        # Step 3: Find similar users (cosine-like similarity)
        scores = defaultdict(float)
        sim_sums = defaultdict(float)

        for other_id, other_ratings in user_ratings.items():
            if other_id == customer_id:
                continue
            # Common books
            common = set(target_ratings.keys()) & set(other_ratings.keys())
            if not common:
                continue
            # Simple similarity: average absolute difference (inverted)
            diff = sum(abs(target_ratings[b] - other_ratings[b]) for b in common) / len(common)
            similarity = max(0, 1 - diff / 5.0)
            if similarity <= 0:
                continue
            # Weighted scores for books the target hasn't rated
            for book_id, rating in other_ratings.items():
                if book_id not in target_ratings:
                    scores[book_id] += similarity * rating
                    sim_sums[book_id] += similarity

        # Step 4: Rank recommendations
        recommendations = []
        for book_id in scores:
            if sim_sums[book_id] > 0:
                predicted = scores[book_id] / sim_sums[book_id]
                recommendations.append({"book_id": book_id, "predicted_rating": round(predicted, 2)})

        recommendations.sort(key=lambda x: x["predicted_rating"], reverse=True)
        recommendations = recommendations[:top_n]

        # Step 5: Enrich with book details
        for rec in recommendations:
            try:
                book_resp = requests.get(f"{BOOK_SERVICE_URL}/api/books/{rec['book_id']}/", timeout=5)
                if book_resp.status_code == 200:
                    rec["book"] = book_resp.json()
            except requests.RequestException:
                rec["book"] = None

        return Response({"customer_id": customer_id, "recommendations": recommendations})

    def _recommend_popular(self, all_ratings, top_n):
        """Fallback: recommend books with highest average rating."""
        book_scores = defaultdict(list)
        for r in all_ratings:
            book_scores[r["book_id"]].append(r["rating"])

        popular = []
        for book_id, ratings in book_scores.items():
            avg = sum(ratings) / len(ratings)
            popular.append({"book_id": book_id, "predicted_rating": round(avg, 2)})

        popular.sort(key=lambda x: x["predicted_rating"], reverse=True)
        popular = popular[:top_n]

        for rec in popular:
            try:
                book_resp = requests.get(f"{BOOK_SERVICE_URL}/api/books/{rec['book_id']}/", timeout=5)
                if book_resp.status_code == 200:
                    rec["book"] = book_resp.json()
            except requests.RequestException:
                rec["book"] = None

        return Response({"customer_id": None, "recommendations": popular})
