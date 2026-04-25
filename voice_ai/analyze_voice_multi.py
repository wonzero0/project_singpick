import os
import numpy as np
from analyze_voice import analyze_voice

USER_FEATURE_DIR = "user_features"


def analyze_all_voices():

    all_features = []

    for name in os.listdir(USER_FEATURE_DIR):
        path = os.path.join(USER_FEATURE_DIR, name)

        if not os.path.isdir(path):
            continue

        try:
            result = analyze_voice(path)["analysis_values"]
            all_features.append(result)
        except:
            print(f"[SKIP] {name}")

    if len(all_features) == 0:
        raise Exception("사용자 음성 없음")

    # =========================
    # 평균 계산
    # =========================
    avg = {}

    keys = all_features[0].keys()

    for k in keys:
        avg[k] = round(
            np.mean([f[k] for f in all_features]),
            2
        )

    return avg