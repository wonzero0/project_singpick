# ai_module/visualization.py

import os
import json
import joblib
import numpy as np


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


def get_artist_embedding(artist_name):

    refs = load_reference()

    vectors = []

    for item in refs:

        if item["artist"] == artist_name:

            try:

                path = os.path.join(
                    EMBEDDING_DIR,
                    item["embedding_file"]
                )

                emb = np.load(path).flatten()

                vectors.append(emb)

            except:
                pass

    if len(vectors) == 0:
        return None

    return np.mean(
        vectors,
        axis=0
    )


def get_visualization_data(
        user_embedding,
        similar_artists
):

    pca = joblib.load(
        PCA_MODEL_PATH
    )

    points = []

    # 사용자
    user_embedding = np.array(
        user_embedding
    )

    user_xy = pca.transform(
        [user_embedding]
    )[0]

    points.append({

        "name": "USER",

        "x": float(user_xy[0]),
        "y": float(user_xy[1]),

        "type": "user"
    })

    # 추천 가수들
    for artist in similar_artists:

        artist_name = artist["name"]

        emb = get_artist_embedding(
            artist_name
        )

        if emb is None:
            continue

        xy = pca.transform(
            [emb]
        )[0]

        points.append({

            "name": artist_name,

            "x": float(xy[0]),
            "y": float(xy[1]),

            "match": artist["match"],

            "type": "artist"
        })

    return points