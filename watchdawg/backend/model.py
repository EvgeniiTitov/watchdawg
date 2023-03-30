import abc
from typing import List

import numpy as np
import torch
from ultralytics import YOLO

from watchdawg.util.logger import get_logger


logger = get_logger("ml")


class MLModel(abc.ABC):
    @abc.abstractmethod
    def __call__(self, batch: List[np.ndarray]):
        pass


class PlaceHolderModel(MLModel):
    def __call__(self, batch: List[np.ndarray]) -> List[dict]:
        return [{} for _ in batch]


class UltralyticsYOLO(MLModel):
    def __init__(self, model: str) -> None:
        try:
            self._model = YOLO(model)
        except Exception as e:
            logger.error(
                f"Failed while loading ultralytics model {model}. Error: {e}"
            )
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._model.to(device)
        logger.info(f"UltralyticsYOLO loaded. Inference device: {device}")

    def __call__(self, batch: List[np.ndarray]) -> List[np.ndarray]:
        results = self._model(batch)
        return [result.plot() for result in results]
