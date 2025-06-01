import torch
import torchvision.transforms as transforms
from torchvision.models import resnet50, ResNet50_Weights
from PIL import Image
import pytesseract
from typing import Tuple, Dict, Any
import logging
import numpy as np

class MemeClassifier:
    def __init__(self, confidence_threshold: float = 0.85):
        self.logger = logging.getLogger(__name__)
        self.confidence_threshold = confidence_threshold
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load pre-trained ResNet model
        self.model = resnet50(weights=ResNet50_Weights.DEFAULT)
        self.model.eval()
        self.model.to(self.device)

        # Image preprocessing
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                              std=[0.229, 0.224, 0.225])
        ])

        # Common meme text patterns
        self.meme_patterns = [
            'when you', 'me when', 'nobody:', 'everyone:',
            'be like', 'feels like', 'that moment',
            'meanwhile', 'plot twist', 'expectation vs reality'
        ]

    def load_image(self, image_path: str) -> Image.Image:
        """Load image from file path."""
        try:
            return Image.open(image_path).convert('RGB')
        except Exception as e:
            self.logger.error(f"Error loading image: {str(e)}")
            raise

    def extract_text(self, image: Image.Image) -> str:
        """Extract text from image using OCR."""
        try:
            return pytesseract.image_to_string(image).lower()
        except Exception as e:
            self.logger.error(f"Error extracting text: {str(e)}")
            return ""

    def analyze_image_features(self, image: Image.Image) -> Tuple[float, Dict[str, Any]]:
        """Analyze image features using the pre-trained model."""
        try:
            # Transform and prepare image
            img_tensor = self.transform(image).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                features = self.model(img_tensor)
            
            # Extract relevant features
            # Note: This is a simplified version. In practice, you'd want to train
            # a classifier specifically for meme detection
            feature_scores = torch.nn.functional.softmax(features, dim=1)
            
            # Calculate meme probability based on image features
            # This is a simplified heuristic and should be replaced with actual trained classifier
            feature_confidence = float(torch.max(feature_scores))
            
            return feature_confidence, {
                "feature_vector": features[0].cpu().numpy(),
                "top_class_confidence": feature_confidence
            }
        except Exception as e:
            self.logger.error(f"Error analyzing image features: {str(e)}")
            return 0.0, {}

    def analyze_text_patterns(self, text: str) -> Tuple[float, Dict[str, Any]]:
        """Analyze text for meme-like patterns."""
        text = text.lower()
        pattern_matches = [pattern for pattern in self.meme_patterns if pattern in text]
        
        # Calculate confidence based on number of matches
        confidence = min(len(pattern_matches) / 2, 1.0)
        
        return confidence, {
            "matched_patterns": pattern_matches,
            "text_length": len(text),
            "pattern_count": len(pattern_matches)
        }

    def is_meme_file(self, image_path: str) -> Tuple[bool, Dict[str, Any]]:
        """Determine if an image file is a meme using both image and text analysis."""
        try:
            # Load and process image
            image = self.load_image(image_path)
            
            # Extract text
            text = self.extract_text(image)
            
            # Analyze image features
            image_confidence, image_details = self.analyze_image_features(image)
            
            # Analyze text patterns
            text_confidence, text_details = self.analyze_text_patterns(text)
            
            # Combined confidence score (weighted average)
            combined_confidence = (0.6 * image_confidence + 0.4 * text_confidence)
            
            result = {
                "is_meme": combined_confidence >= self.confidence_threshold,
                "confidence": combined_confidence,
                "image_confidence": image_confidence,
                "text_confidence": text_confidence,
                "image_details": image_details,
                "text_details": text_details,
                "extracted_text": text
            }
            
            return result["is_meme"], result
            
        except Exception as e:
            self.logger.error(f"Error in meme classification: {str(e)}")
            return False, {"error": str(e)} 