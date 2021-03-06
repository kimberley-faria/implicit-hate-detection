import pandas as pd
import torch
from torch.utils.data import Dataset

from implicit_hate_dataloader.helpers import tokenize_and_format

STAGE_1_LABELS = {
    'explicit_hate': 0,
    'implicit_hate': 1,
    'not_hate': 2
}

STAGE_1_LABELS_EPLICIT_DROPPED = {
    'implicit_hate': 1,
    'not_hate': 0
}

STAGE_1_LABELS_MERGED = {
    'not_hate': 0,
    'hate': 1
}

STAGE_2_IMPLICIT_LABELS = {
    'white_grievance': 0,
    'incitement': 1,
    'inferiority': 2,
    'irony': 3,
    'stereotypical': 4,
    'threatening': 5,
    'other': 6
}
STAGE_2_EXTRA_IMPLICIT_LABELS = {
    'white_grievance': 0,
    'incitement': 1,
    'inferiority': 2,
    'irony': 3,
    'stereotypical': 4,
    'threatening': 5,
    'other': 6,
    'None': 7
}


class Stage1Dataset(Dataset):
    def __init__(self, annotations_file, drop_explicit_hate=False, merge_hate_labels=False, bertweet = False):
        self.data = pd.read_csv(annotations_file, delimiter='\t')

        label_mapping = STAGE_1_LABELS
        if drop_explicit_hate:
            self.data = self.data.loc[self.data['class'] != 'explicit_hate']
            label_mapping = STAGE_1_LABELS_EPLICIT_DROPPED
        elif merge_hate_labels:
            self.data.loc[(self.data['class'] == 'implicit_hate'), 'class'] = 'hate'
            self.data.loc[(self.data['class'] == 'explicit_hate'), 'class'] = 'hate'
            label_mapping = STAGE_1_LABELS_MERGED

        self.posts = self.data['post'].values
        self.classes = self.data['class'].values

        input_ids, attention_masks = tokenize_and_format(self.posts, bertweet)
        self.input_ids = torch.cat(input_ids, dim=0)
        self.attention_masks = torch.cat(attention_masks, dim=0)
        self.labels = torch.tensor([label_mapping.get(cls) for cls in self.classes])

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        # preprocess if required
        # (check: does it matter if you preprocess in init instead of get_item?)
        # https://pytorch.org/tutorials/beginner/data_loading_tutorial.html

        # return tokenized data
        return self.posts[idx], self.classes[idx], self.input_ids[idx], self.attention_masks[idx], self.labels[idx]


class Stage2Dataset(Dataset):
    def __init__(self, annotations_file, drop_other=False, bertweet = False):
        self.data = pd.read_csv(annotations_file, delimiter='\t').fillna('None')
        if drop_other:
            self.data = self.data.loc[self.data['implicit_class'] != 'other']

        self.posts = self.data['post'].values
        self.implicit_classes = self.data['implicit_class'].values
        self.extra_implicit_classes = self.data['extra_implicit_class'].values

        input_ids, attention_masks = tokenize_and_format(self.posts, bertweet)
        self.input_ids = torch.cat(input_ids, dim=0)
        self.attention_masks = torch.cat(attention_masks, dim=0)
        self.implicit_labels = torch.tensor(
            [STAGE_2_IMPLICIT_LABELS.get(cls) for cls in self.implicit_classes])
        self.extra_implicit_labels = torch.tensor(
            [STAGE_2_EXTRA_IMPLICIT_LABELS.get(cls) for cls in self.extra_implicit_classes])

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        # preprocess if required

        # return tokenized data
        return self.posts[idx], self.implicit_classes[idx], self.extra_implicit_classes[idx], \
               self.input_ids[idx], self.attention_masks[idx], \
               self.implicit_labels[idx], self.extra_implicit_labels[idx]
