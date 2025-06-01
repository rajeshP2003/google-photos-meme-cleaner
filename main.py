import os
import logging
from typing import List, Dict, Any
import argparse
from tqdm import tqdm
from datetime import datetime

from auth.google_auth import GoogleAuthHandler
from google_api.photos_api import GooglePhotosAPI
from ai.meme_classifier import MemeClassifier

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MemeCleanerApp:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.auth_handler = GoogleAuthHandler()
        self.credentials = self.auth_handler.get_credentials()
        self.photos_api = GooglePhotosAPI(self.credentials)
        self.meme_classifier = MemeClassifier()
        
    def process_media_items(self) -> Dict[str, Any]:
        """Process media items and identify memes with rate limiting."""
        stats = {
            "total_processed": 0,
            "memes_found": 0,
            "errors": 0,
            "meme_ids": []
        }

        try:
            # Create meme album if not in dry run mode
            if not self.dry_run:
                album_name = f"Detected Memes ({datetime.now().strftime('%Y-%m-%d')})"
                meme_album = self.photos_api.create_album(album_name)
                album_id = meme_album['id']
                logger.info(f"Created album: {album_name}")

            # Get all media items (this is automatically rate limited)
            media_items = self.photos_api.list_media_items()
            logger.info(f"Found {len(media_items)} items to process")

            # Process items with progress bar
            for item in tqdm(media_items, desc="Processing items"):
                try:
                    base_url = item.get('baseUrl')
                    if not base_url:
                        continue

                    is_meme, details = self.meme_classifier.is_meme(base_url)
                    stats["total_processed"] += 1

                    if is_meme:
                        stats["memes_found"] += 1
                        stats["meme_ids"].append(item['id'])
                        
                        if not self.dry_run:
                            # Add to meme album (rate limited internally)
                            self.photos_api.add_to_album(album_id, [item['id']])
                            logger.info(f"Added meme to album: {item.get('filename', 'unknown')}")

                            # Log remaining quota
                            remaining_quota = self.photos_api.get_remaining_quota()
                            logger.info(f"Remaining daily quota: {remaining_quota:.2f}MB")

                except Exception as e:
                    logger.error(f"Error processing item {item.get('id', 'unknown')}: {str(e)}")
                    stats["errors"] += 1

        except Exception as e:
            logger.error(f"Error in main processing loop: {str(e)}")
            raise

        return stats

def main():
    parser = argparse.ArgumentParser(description="Google Photos Meme Cleaner (API Version)")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (no changes made)")
    args = parser.parse_args()

    try:
        app = MemeCleanerApp(dry_run=args.dry_run)
        
        logger.info("Starting meme detection process...")
        if args.dry_run:
            logger.info("Running in DRY RUN mode - no changes will be made")

        stats = app.process_media_items()

        # Print summary
        logger.info("\nProcess Complete!")
        logger.info(f"Total items processed: {stats['total_processed']}")
        logger.info(f"Memes found: {stats['memes_found']}")
        logger.info(f"Errors encountered: {stats['errors']}")
        
        if args.dry_run:
            logger.info("\nThis was a dry run. No changes were made to your Google Photos library.")
            logger.info("Run without --dry-run to move detected memes to a new album.")
        else:
            logger.info("\nMemes have been added to a new album in your Google Photos.")
            logger.info("Note: Original photos remain in place as Google Photos API doesn't support deletion.")
            logger.info("You can manually review and delete the originals through the Google Photos interface.")

        # Show remaining quota
        remaining_quota = app.photos_api.get_remaining_quota()
        logger.info(f"\nRemaining daily quota: {remaining_quota:.2f}MB")

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main()) 