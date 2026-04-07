from django.core.management.base import BaseCommand
from catalogs.models import Catalog


class Command(BaseCommand):
    help = 'Seed catalog data'

    def handle(self, *args, **options):
        catalogs = [
            {"name": "Văn học Việt Nam", "description": "Sách văn học Việt Nam, tiểu thuyết, truyện ngắn", "icon": "🇻🇳"},
            {"name": "Văn học nước ngoài", "description": "Tiểu thuyết, truyện ngắn văn học nước ngoài", "icon": "🌍"},
            {"name": "Kinh tế", "description": "Sách về kinh tế, tài chính, đầu tư", "icon": "💼"},
            {"name": "Kỹ năng sống", "description": "Sách phát triển bản thân, kỹ năng mềm", "icon": "🌱"},
            {"name": "Khoa học công nghệ", "description": "Sách về khoa học, công nghệ, lập trình", "icon": "💻"},
            {"name": "Thiếu nhi", "description": "Sách dành cho thiếu nhi, truyện tranh", "icon": "🧸"},
            {"name": "Giáo khoa - Tham khảo", "description": "Sách giáo khoa, sách tham khảo học tập", "icon": "📘"},
            {"name": "Tâm lý - Triết học", "description": "Sách tâm lý học, triết học", "icon": "🧠"},
            {"name": "Lịch sử - Địa lý", "description": "Sách lịch sử, địa lý, du lịch", "icon": "🗺️"},
            {"name": "Y học - Sức khỏe", "description": "Sách về y học, sức khỏe, dinh dưỡng", "icon": "🩺"},
            {"name": "Nghệ thuật - Âm nhạc", "description": "Sách về nghệ thuật, âm nhạc, hội họa", "icon": "🎨"},
            {"name": "Ngoại ngữ", "description": "Sách học ngoại ngữ, từ điển", "icon": "🗣️"},
            {"name": "Chính trị - Pháp luật", "description": "Sách về chính trị, pháp luật", "icon": "⚖️"},
            {"name": "Tôn giáo - Tâm linh", "description": "Sách về tôn giáo, tâm linh", "icon": "🕊️"},
            {"name": "Thể thao", "description": "Sách về thể thao, thể dục", "icon": "⚽"},
        ]

        created_count = 0
        for cat_data in catalogs:
            catalog, created = Catalog.objects.get_or_create(
                name=cat_data["name"],
                defaults={
                    "description": cat_data["description"],
                    "icon": cat_data["icon"],
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f"Created catalog: {catalog.name}")
            else:
                updated_fields = []
                if catalog.description != cat_data["description"]:
                    catalog.description = cat_data["description"]
                    updated_fields.append("description")
                if catalog.icon != cat_data["icon"]:
                    catalog.icon = cat_data["icon"]
                    updated_fields.append("icon")
                if updated_fields:
                    catalog.save(update_fields=updated_fields)
                self.stdout.write(f"Catalog already exists: {catalog.name}")

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {created_count} catalogs"))
