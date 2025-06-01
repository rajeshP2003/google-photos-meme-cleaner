from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict, Any, Optional
import logging
import time
from datetime import datetime
from .usage_tracker import UsageTracker

logger = logging.getLogger(__name__)

class GooglePhotosAPI:
    def __init__(self, credentials):
        self.service = build('photoslibrary', 'v1', credentials=credentials, static_discovery=False)
        self.usage_tracker = UsageTracker()
        self.page_size = 50
        
    def _estimate_media_size(self, media_item: Dict[str, Any]) -> int:
        """Estimate media item size based on metadata."""
        if 'mediaMetadata' in media_item:
            metadata = media_item['mediaMetadata']
            if 'width' in metadata and 'height' in metadata:
                # Rough estimate: width * height * 3 (RGB) * 1.5 (compression factor)
                return int(int(metadata['width']) * int(metadata['height']) * 3 * 1.5)
        return 1024 * 1024  # Default to 1MB if can't estimate

    def list_media_items(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """List media items from Google Photos with rate limiting."""
        try:
            media_items = []
            page_token = None

            while True:
                # Check rate limits before making request
                self.usage_tracker.wait_if_needed()

                request_body = {
                    'pageSize': self.page_size,
                    'pageToken': page_token
                }
                
                if filters:
                    request_body['filters'] = filters

                response = self.service.mediaItems().search(
                    body=request_body
                ).execute()

                if 'mediaItems' in response:
                    batch_size = sum(self._estimate_media_size(item) for item in response['mediaItems'])
                    self.usage_tracker.wait_if_needed(batch_size)
                    media_items.extend(response['mediaItems'])

                    # Log progress
                    logger.info(f"Fetched {len(media_items)} items so far. "
                              f"Remaining daily quota: {self.usage_tracker.get_remaining_daily_quota() / (1024*1024):.2f}MB")

                if 'nextPageToken' not in response:
                    break

                page_token = response['nextPageToken']
                time.sleep(1)  # Basic rate limiting

            return media_items

        except HttpError as e:
            logger.error(f"Error listing media items: {str(e)}")
            raise

    def get_media_item(self, media_item_id: str) -> Dict[str, Any]:
        """Get a specific media item by ID with rate limiting."""
        try:
            self.usage_tracker.wait_if_needed()
            return self.service.mediaItems().get(mediaItemId=media_item_id).execute()
        except HttpError as e:
            logger.error(f"Error getting media item {media_item_id}: {str(e)}")
            raise

    def batch_get_media_items(self, media_item_ids: List[str]) -> List[Dict[str, Any]]:
        """Get multiple media items by their IDs with rate limiting."""
        try:
            self.usage_tracker.wait_if_needed()
            response = self.service.mediaItems().batchGet(
                mediaItemIds=media_item_ids
            ).execute()
            return response.get('mediaItems', [])
        except HttpError as e:
            logger.error(f"Error batch getting media items: {str(e)}")
            raise

    def move_to_trash(self, media_item_id: str) -> bool:
        """Move a media item to trash (Note: This is a simulated function as Google Photos API doesn't support direct deletion)."""
        # Note: As of now, Google Photos API doesn't support moving items to trash
        # This is a placeholder for when the feature becomes available
        logger.warning("Moving items to trash is not supported by Google Photos API")
        return False

    def create_album(self, album_title: str) -> Dict[str, Any]:
        """Create a new album with rate limiting."""
        try:
            self.usage_tracker.wait_if_needed()
            return self.service.albums().create(
                body={"album": {"title": album_title}}
            ).execute()
        except HttpError as e:
            logger.error(f"Error creating album: {str(e)}")
            raise

    def add_to_album(self, album_id: str, media_item_ids: List[str]) -> bool:
        """Add media items to an album with rate limiting."""
        try:
            self.usage_tracker.wait_if_needed()
            self.service.albums().batchAddMediaItems(
                albumId=album_id,
                body={"mediaItemIds": media_item_ids}
            ).execute()
            return True
        except HttpError as e:
            logger.error(f"Error adding items to album: {str(e)}")
            return False

    def get_remaining_quota(self) -> float:
        """Get remaining daily quota in MB."""
        return self.usage_tracker.get_remaining_daily_quota() / (1024 * 1024) 