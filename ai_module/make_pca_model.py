# ai_module/make_pca_model.py

import os
import json
import joblib
import numpy as np
from sklearn.decomposition import PCA

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

REFERENCE_JSON = os.path.join(
    BASE_DIR,
    "reference_songs.json"
)

EMBEDDING_DIR = os.path.join(
    BASE_DIR,
    "embedding_vectors"
)

PCA_MODEL_PATH = os.path.join(
    BASE_DIR,
    "pca_model.pkl"
)


def load_reference():
    with open(
        REFERENCE_JSON,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def build_pca():

    data = load_reference()

    vectors = []

    for item in data:

        path = os.path.join(
            EMBEDDING_DIR,
            item["embedding_file"]
        )

        try:
            emb = np.load(path).flatten()

            if len(emb) == 256:
                vectors.append(emb)

        except Exception as e:
            print(e)

    vectors = np.array(vectors)

    print("embedding count :", len(vectors))

    pca = PCA(
        n_components=2,
        random_state=42
    )

    pca.fit(vectors)

    joblib.dump(
        pca,
        PCA_MODEL_PATH
    )

    print("✅ PCA model saved")
    print(PCA_MODEL_PATH)


if __name__ == "__main__":
    build_pca()