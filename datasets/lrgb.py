import torch
from torch.utils.data import random_split
from dataclasses import dataclass

import torchvision.transforms as transforms
from torch_geometric.transforms import BaseTransform
from torch_geometric.datasets import LRGBDataset

from datasets.transforms import CenterTransform
from datasets.base_dataset import DataModule
from loaders.factory import register
from datasets.config import DataModuleConfig


@dataclass
class LRGBDataModuleConfig(DataModuleConfig):
    root: str = "./data/lrgb"
    module: str = "datasets.lrgb"
    name: str = "Peptides-func"


class ConvertToFloat(BaseTransform):
    def __call__(self, data):
        """Convert node feature data type to float."""
        data["x"] = data["x"].to(dtype=torch.float)
        return data


class OneHotDecoding(BaseTransform):
    def __call__(self, data):
        """Adjust multi-class labels (reverse one-hot encoding).

        This is necessary because some data sets use one-hot encoding
        for their labels, wreaks havoc with some multi-class tasks.
        """
        label = data["y"]

        if len(label.shape) > 1:
            label = label.squeeze().tolist()

            if isinstance(label, list):
                label = label.index(1.0)

            data["y"] = torch.as_tensor([label], dtype=torch.long)

        return data


class LrgbDataModule(DataModule):
    def __init__(self, config):
        self.config = config
        self.transform = transforms.Compose(
                [OneHotDecoding(), ConvertToFloat(), CenterTransform()]
            )
        super().__init__(
            config.root, config.batch_size, config.num_workers, config.pin_memory
        )

    def setup(self):
        self.entire_ds = torch.utils.data.ConcatDataset(
                [
                LRGBDataset(
                   root=self.config.root, 
                    pre_transform=self.transform, 
                    name=self.config.name,
                    split="train"
                    ),
                LRGBDataset(
                   root=self.config.root, 
                    pre_transform=self.transform, 
                    name=self.config.name,
                    split="test"
                    ),
                LRGBDataset(
                   root=self.config.root, 
                    pre_transform=self.transform, 
                    name=self.config.name,
                    split="val"
                    )
                ]
            )
        
        self.train_ds, self.test_ds = random_split(
            self.entire_ds,
            [
                int(0.9 * len(self.entire_ds)),
                len(self.entire_ds) - int(0.9 * len(self.entire_ds)),
            ],
        )  # type: ignore
        
        self.train_ds, self.val_ds = random_split(
            self.train_ds,
            [
                int(0.9 * len(self.train_ds)),
                len(self.train_ds) - int(0.9 * len(self.train_ds)),
            ],
        )  # type: ignore 


def initialize():
    register("dataset", LrgbDataModule)
