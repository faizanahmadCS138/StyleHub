import os
import cloudinary
import cloudinary.uploader
from django.conf import settings
from django.core.management.base import BaseCommand
from apps.catalog.models import ProductImage


class Command(BaseCommand):
    help = "Uploads existing local product images to Cloudinary and updates DB records"

    def handle(self, *args, **options):
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_STORAGE.get('CLOUD_NAME'),
            api_key=settings.CLOUDINARY_STORAGE.get('API_KEY'),
            api_secret=settings.CLOUDINARY_STORAGE.get('API_SECRET'),
            secure=True,
        )

        images = ProductImage.objects.all()
        total_count = images.count()

        self.stdout.write(
            self.style.MIGRATE_HEADING(f"Found {total_count} images to process for Cloudinary.")
        )

        success_count = 0
        failed_count = 0

        for idx, img_obj in enumerate(images, start=1):
            if not img_obj.image:
                continue

            raw_name = str(img_obj.image.name)
            filename = os.path.basename(raw_name.replace('\\', '/'))
            
            # Check local media directory
            local_path = os.path.join(settings.MEDIA_ROOT, 'products', filename)
            if not os.path.exists(local_path):
                local_path = os.path.join(settings.MEDIA_ROOT, raw_name.replace('/', os.sep))

            if os.path.exists(local_path):
                file_size_mb = os.path.getsize(local_path) / (1024 * 1024)
                self.stdout.write(
                    f"[{idx}/{total_count}] Uploading {filename} ({file_size_mb:.1f} MB) to Cloudinary..."
                )

                try:
                    public_id_name = os.path.splitext(filename)[0]
                    response = cloudinary.uploader.upload(
                        local_path,
                        folder="media/products",
                        public_id=public_id_name,
                        overwrite=True,
                        resource_type="image"
                    )

                    cloudinary_url = response.get("secure_url")
                    
                    # Keep standardized relative image field name
                    img_obj.image.name = f"products/{filename}"
                    img_obj.save(update_fields=["image"])

                    self.stdout.write(
                        self.style.SUCCESS(f"  --> Uploaded & Saved: {cloudinary_url}")
                    )
                    success_count += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"  --> Failed to upload ID {img_obj.pk}: {e}")
                    )
                    failed_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f"[{idx}/{total_count}] Local file not found: {local_path}")
                )
                failed_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nFinished! Uploaded: {success_count} | Failed/Skipped: {failed_count}"
            )
        )