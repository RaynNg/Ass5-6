"""
python manage.py update_book_images

Fetches real book cover images from Google Books API by searching each book title.
Vietnamese titles are mapped to their original-language search query for better results.
"""

import time
import requests
from django.core.management.base import BaseCommand
from books.models import Book

GOOGLE_BOOKS_API  = "https://www.googleapis.com/books/v1/volumes"
OPEN_LIBRARY_SEARCH = "https://openlibrary.org/search.json"
OPEN_LIBRARY_COVER  = "https://covers.openlibrary.org/b/id/{id}-L.jpg"

# Category-appropriate fallback images (Unsplash, curated by genre)
CATALOG_FALLBACKS = {
    "văn học":      "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400",
    "kinh doanh":   "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=400",
    "kỹ năng":      "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=400",
    "khoa học":     "https://images.unsplash.com/photo-1532094349884-543559bf8c01?w=400",
    "công nghệ":    "https://images.unsplash.com/photo-1518770660439-4636190af475?w=400",
    "lịch sử":      "https://images.unsplash.com/photo-1461360228754-6e81c478b882?w=400",
    "giáo khoa":    "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=400",
    "thiếu nhi":    "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=400",
    "tâm lý":       "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
    "default":      "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=400",
}

# Vietnamese title → English search query for better Google Books results
VI_TO_SEARCH = {
    "Dế Mèn Phiêu Lưu Ký":                    "De Men Phieu Luu Ky To Hoai",
    "Tắt Đèn":                                  "Tat Den Ngo Tat To Vietnamese literature",
    "Chí Phèo":                                 "Chi Pheo Nam Cao Vietnamese",
    "Số Đỏ":                                    "So Do Vu Trong Phung",
    "Vợ Nhặt":                                  "Vo Nhat Kim Lan Vietnamese",
    "Lão Hạc":                                  "Lao Hac Nam Cao",
    "Mắt Biếc":                                 "Mat Biec Nguyen Nhat Anh",
    "Nỗi Buồn Chiến Tranh":                    "The Sorrow of War Bao Ninh",
    "Cho Tôi Xin Một Vé Đi Tuổi Thơ":         "Nguyen Nhat Anh childhood ticket",
    "Tôi Thấy Hoa Vàng Trên Cỏ Xanh":         "Toi thay hoa vang Nguyen Nhat Anh",
    "Kính Vạn Hoa":                             "Kinh Van Hoa Nguyen Nhat Anh",
    "Đắc Nhân Tâm":                             "How to Win Friends and Influence People Dale Carnegie",
    "Nhà Giả Kim":                              "The Alchemist Paulo Coelho",
    "1984":                                     "1984 George Orwell",
    "Trại Súc Vật":                             "Animal Farm George Orwell",
    "Giết Con Chim Nhại":                       "To Kill a Mockingbird Harper Lee",
    "Gatsby Vĩ Đại":                            "The Great Gatsby F Scott Fitzgerald",
    "Bắt Trẻ Đồng Xanh":                       "The Catcher in the Rye Salinger",
    "Hai Số Phận":                              "Kane and Abel Jeffrey Archer",
    "Hoàng Tử Bé":                              "The Little Prince Antoine de Saint-Exupery",
    "Harry Potter và Hòn Đá Phù Thủy":         "Harry Potter Philosopher's Stone Rowling",
    "Harry Potter và Phòng Chứa Bí Mật":       "Harry Potter Chamber of Secrets Rowling",
    "Harry Potter và Tên Tù Nhân Ngục Azkaban":"Harry Potter Prisoner of Azkaban Rowling",
    "Cuốn Theo Chiều Gió":                      "Gone with the Wind Margaret Mitchell",
    "Cha Giàu Cha Nghèo":                       "Rich Dad Poor Dad Robert Kiyosaki",
    "Người Giàu Có Nhất Thành Babylon":        "Richest Man in Babylon George Clason",
    "Nghĩ Giàu Làm Giàu":                      "Think and Grow Rich Napoleon Hill",
    "Bí Mật Tư Duy Triệu Phú":                "Secrets of the Millionaire Mind T Harv Eker",
    "Khởi Nghiệp Tinh Gọn":                    "The Lean Startup Eric Ries",
    "Từ Tốt Đến Vĩ Đại":                       "Good to Great Jim Collins",
    "7 Thói Quen Thành Đạt":                   "The 7 Habits of Highly Effective People Covey",
    "Chiến Lược Đại Dương Xanh":              "Blue Ocean Strategy Kim Mauborgne",
    "Quốc Gia Khởi Nghiệp":                    "Start-up Nation Dan Senor",
    "Zero To One":                              "Zero to One Peter Thiel",
    "Đừng Bao Giờ Đi Ăn Một Mình":           "Never Eat Alone Keith Ferrazzi",
    "Sức Mạnh Của Thói Quen":                  "The Power of Habit Charles Duhigg",
    "Dọn Dẹp Để Đời Thay Đổi":              "The Life-Changing Magic of Tidying Up Marie Kondo",
    "Tư Duy Nhanh Và Chậm":                    "Thinking Fast and Slow Daniel Kahneman",
    "Atomic Habits - Thói Quen Nguyên Tử":     "Atomic Habits James Clear",
    "Bí Mật Của May Mắn":                      "The Luck Factor Richard Wiseman",
    "Hành Trình Về Phương Đông":             "Journey to the East Hermann Hesse",
    "Khéo Ăn Nói Sẽ Có Được Thiên Hạ":      "The Art of Talking to Anyone Rosalie Maggio",
    "Tuổi Trẻ Đáng Giá Bao Nhiêu":           "Rosie Nguyen youth worth",
    "Sức Mạnh Hiện Tại":                       "The Power of Now Eckhart Tolle",
    "Tâm Lý Học Đám Đông":                    "The Crowd Gustave Le Bon psychology",
    "Giải Mã Giấc Mơ":                         "The Interpretation of Dreams Sigmund Freud",
    "Con Người Trưởng Thành":                  "Man's Search for Meaning Viktor Frankl",
    "Siêu Tư Duy":                              "Super Thinking Gabriel Weinberg",
    "Biết Người Biết Ta":                       "The Art of War Sun Tzu",
    "Lịch Sử Việt Nam":                        "History of Vietnam",
    "Đại Việt Sử Ký Toàn Thư":              "Dai Viet Su Ky Toan Thu Vietnamese history",
    "Súng, Vi Trùng Và Thép":                  "Guns Germs Steel Jared Diamond",
    "1000 Năm Thăng Long":                     "Thang Long 1000 years Hanoi history",
    "Việt Nam Sử Lược":                        "Vietnam Su Luoc history",
    "Hồi Ký Chiến Tranh":                      "Vietnam war memoir",
    "Thế Giới Phẳng":                          "The World Is Flat Thomas Friedman",
    "Ăn Gì Cho Khỏe":                          "Healthy eating nutrition book",
    "Sống Khỏe Để Già":                        "Healthy aging longevity book",
    "Yoga - Nghệ Thuật Chữa Lành":           "Yoga healing art practice",
    "Đông Y Gia Truyền":                        "Traditional Chinese medicine herbal",
    "Ăn Sạch Sống Sáng":                       "Clean eating healthy living",
    "Bí Quyết Sống Thọ":                       "Longevity secrets Blue Zones",
    "Lịch Sử Mỹ Thuật Việt Nam":             "Vietnamese art history",
    "Học Vẽ Căn Bản":                          "Drawing basics for beginners",
    "Âm Nhạc Việt Nam":                        "Vietnamese music history",
    "Nghệ Thuật Nhiếp Ảnh":                   "Photography art techniques",
    "Thiết Kế Đồ Họa":                         "Graphic design principles",
    "Lược Sử Thời Gian":                       "A Brief History of Time Stephen Hawking",
    "Sapiens: Lược Sử Loài Người":           "Sapiens Brief History of Humankind Harari",
    "Homo Deus":                                "Homo Deus Yuval Noah Harari",
    "Artificial Intelligence: A Modern Approach":"Artificial Intelligence Modern Approach Russell Norvig",
    "Deep Learning":                            "Deep Learning Ian Goodfellow",
    "Introduction to Algorithms":              "Introduction to Algorithms Cormen CLRS",
    "Design Patterns":                          "Design Patterns Gang of Four",
    "The Pragmatic Programmer":                "The Pragmatic Programmer Hunt Thomas",
    "Clean Code":                               "Clean Code Robert C Martin",
    "Python Crash Course":                      "Python Crash Course Eric Matthes",
    "Toán 12 Nâng Cao":                        "Advanced Mathematics 12 Vietnam textbook",
    "Văn 12 - Sách Tham Khảo":               "Vietnamese literature 12 reference",
    "Tiếng Anh 12":                             "English 12 Vietnam textbook",
    "Vật Lý 12 Nâng Cao":                      "Advanced Physics 12 textbook",
    "Hóa Học 12":                               "Chemistry 12 textbook",
    "Sinh Học 12":                              "Biology 12 textbook",
    "Lịch Sử 12":                               "History 12 Vietnam textbook",
    "Địa Lý 12":                                "Geography 12 Vietnam textbook",
    "Bộ Đề Thi Thử THPT Quốc Gia":          "Vietnam national high school exam practice",
    "Đời Ngắn Đừng Ngủ Dài":               "Don't Sleep In short life",
    "Nghệ Thuật Sống":                         "The Art of Living Epictetus",
    "Thiền Định Căn Bản":                      "Mindfulness Meditation for Beginners",
    "Phật Giáo Việt Nam":                      "Vietnamese Buddhism religion",
    "Đạo Đức Kinh":                            "Tao Te Ching Laozi",
    "Tôn Giáo Học Đại Cương":               "Introduction to Religious Studies",
    "Luật Dân Sự":                              "Civil Law textbook",
    "Luật Hình Sự":                             "Criminal Law textbook",
    "Hiến Pháp Việt Nam":                      "Vietnam Constitution law",
    "Tư Tưởng Hồ Chí Minh":                  "Ho Chi Minh Thought ideology",
    "Đường Kách Mệnh":                         "Revolutionary Path Ho Chi Minh",
    "Tiếng Nhật Sơ Cấp":                       "Japanese for Beginners",
    "Tiếng Hàn Cơ Bản":                        "Korean for Beginners",
    "Tiếng Trung Cơ Bản":                      "Chinese Mandarin for Beginners",
    "Từ Điển Anh-Việt":                        "English Vietnamese Dictionary",
    "TOEIC 990":                                "TOEIC 990 score preparation",
    "IELTS Practice Tests":                     "IELTS Practice Tests Cambridge",
    "English Grammar In Use":                  "English Grammar in Use Raymond Murphy",
    "Doraemon Tập 1":                           "Doraemon manga volume 1",
    "Doraemon Tập 2":                           "Doraemon manga volume 2",
    "Doremon Tập 3":                            "Doraemon manga volume 3",
    "Conan Tập 1":                              "Detective Conan manga volume 1",
    "Conan Tập 2":                              "Detective Conan manga volume 2",
    "Shin - Cậu Bé Bút Chì Tập 1":          "Crayon Shin-chan manga volume 1",
    "Bí Kíp Ở Nhà Một Mình":                  "Home Alone kids book",
    "Cẩm Nang Sinh Tồn":                       "Survival Handbook wilderness",
    "Dế Mèn Phiêu Lưu Ký - Bản Đặc Biệt": "De Men Phieu Luu Ky special edition",
    "Luật Bóng Đá":                            "Football Soccer Rules FIFA",
    "Kỹ Thuật Cơ Bản Bóng Rổ":             "Basketball Basic Techniques",
    "Cờ Vua Căn Bản":                          "Chess basics for beginners",
    "Tennis Cho Người Mới":                    "Tennis for beginners",
    "Bơi Lội Căn Bản":                         "Swimming basics techniques",
}


class Command(BaseCommand):
    help = "Update book cover images using Google Books API"

    def add_arguments(self, parser):
        parser.add_argument("--only-missing", action="store_true",
                            help="Only update books that still use Unsplash placeholders")

    def handle(self, *args, **options):
        qs = Book.objects.all().order_by("id")
        if options["only_missing"]:
            qs = qs.filter(image_url__contains="unsplash")
        books = list(qs)
        self.stdout.write(f"Updating images for {len(books)} books…")

        updated, skipped = 0, 0

        for book in books:
            query   = VI_TO_SEARCH.get(book.title, book.title)
            # 1) Google Books with mapped query
            url = self._fetch_google(query)
            # 2) Google Books with raw title
            if not url:
                url = self._fetch_google(book.title)
            # 3) Open Library
            if not url:
                url = self._fetch_openlibrary(book.title)
            # 4) Curated category fallback
            if not url:
                url = self._fallback(book.title)

            if url:
                book.image_url = url
                book.save(update_fields=["image_url"])
                updated += 1
                self.stdout.write(f"  OK  {book.title[:50]}")
            else:
                skipped += 1
                self.stdout.write(f"  --  {book.title[:50]}")

            time.sleep(0.1)

        self.stdout.write(
            self.style.SUCCESS(f"\nDone — updated: {updated}, skipped: {skipped}")
        )

    def _fetch_google(self, query: str) -> str | None:
        try:
            resp = requests.get(
                GOOGLE_BOOKS_API,
                params={"q": query, "maxResults": 1, "printType": "books"},
                timeout=8,
            )
            if resp.status_code != 200:
                return None
            items = resp.json().get("items", [])
            if not items:
                return None
            links = items[0].get("volumeInfo", {}).get("imageLinks", {})
            url   = (links.get("large") or links.get("medium")
                     or links.get("thumbnail") or links.get("smallThumbnail"))
            if url:
                url = url.replace("http://", "https://")
                url = url.replace("zoom=1", "zoom=3")
            return url or None
        except Exception:
            return None

    def _fetch_openlibrary(self, title: str) -> str | None:
        try:
            resp = requests.get(
                OPEN_LIBRARY_SEARCH,
                params={"title": title, "limit": 1, "fields": "cover_i"},
                timeout=8,
            )
            if resp.status_code != 200:
                return None
            docs = resp.json().get("docs", [])
            if not docs or not docs[0].get("cover_i"):
                return None
            cover_id = docs[0]["cover_i"]
            return OPEN_LIBRARY_COVER.format(id=cover_id)
        except Exception:
            return None

    def _fallback(self, title: str) -> str:
        t = title.lower()
        if any(w in t for w in ["toán", "vật lý", "hóa", "sinh", "lịch sử 1", "địa lý 1", "tiếng anh 1", "văn 1"]):
            return CATALOG_FALLBACKS["giáo khoa"]
        if any(w in t for w in ["kinh doanh", "khởi nghiệp", "triệu phú", "giàu", "tài chính", "kinh tế"]):
            return CATALOG_FALLBACKS["kinh doanh"]
        if any(w in t for w in ["python", "code", "algorithm", "design pattern", "deep learning", "ai", "lập trình"]):
            return CATALOG_FALLBACKS["công nghệ"]
        if any(w in t for w in ["lịch sử", "sử", "thăng long", "đại việt"]):
            return CATALOG_FALLBACKS["lịch sử"]
        if any(w in t for w in ["doraemon", "conan", "shin", "thiếu nhi", "dế mèn"]):
            return CATALOG_FALLBACKS["thiếu nhi"]
        if any(w in t for w in ["tâm lý", "sức mạnh", "tư duy", "thói quen", "kỹ năng", "nghệ thuật sống"]):
            return CATALOG_FALLBACKS["tâm lý"]
        if any(w in t for w in ["khoa học", "vũ trụ", "thời gian", "súng vi trùng", "sapiens", "homo"]):
            return CATALOG_FALLBACKS["khoa học"]
        if any(w in t for w in ["truyện", "tiểu thuyết", "ký", "thơ", "văn học"]):
            return CATALOG_FALLBACKS["văn học"]
        return CATALOG_FALLBACKS["default"]
